"""
Text2SQL Service - AI-powered SQL generation from natural language
Inspired by WrenAI's architecture for generating accurate SQL queries
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session
from openai import AsyncOpenAI
import json
import re

from app.core.config import settings
from app.services.database_service import DatabaseService
from app.services.vector_service import VectorService
from app.services.embedding_service import EmbeddingService
from app.services.progressive_retrieval_service import ProgressiveRetrievalService
from app.schemas.vector_document import VectorSearchRequest
from app.core.logging_config import debug_logger

logger = logging.getLogger(__name__)


class Text2SQLQuery(BaseModel):
    """Model for Text2SQL query request"""
    model_config = ConfigDict(extra='forbid', validate_assignment=True)

    question: str = Field(..., description="Natural language question")
    database_alias: str = Field(..., description="Target database alias")
    thread_id: Optional[str] = Field(None, description="Conversation thread ID")
    context: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Previous conversation context")
    sample_size: Optional[int] = Field(100, description="Sample size for query results")


class Text2SQLResponse(BaseModel):
    """Model for Text2SQL response"""
    model_config = ConfigDict(extra='forbid', validate_assignment=True)

    sql: str = Field(..., description="Generated SQL query")
    explanation: str = Field(..., description="Explanation of the query logic")
    confidence: float = Field(..., description="Confidence score (0-1)")
    tables_used: List[str] = Field(..., description="Tables referenced in the query")
    columns_used: List[str] = Field(..., description="Columns referenced in the query")
    reasoning: str = Field(..., description="Step-by-step reasoning")
    thread_id: str = Field(..., description="Conversation thread ID")
    query_type: str = Field(..., description="Type of query (SELECT, COUNT, etc.)")


class DatabaseSchema(BaseModel):
    """Model for database schema information"""
    model_config = ConfigDict(extra='forbid', validate_assignment=True)

    tables: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]
    constraints: List[Dict[str, Any]]


class Text2SQLService:
    """Service for converting natural language to SQL queries"""

    def __init__(self):
        self.database_service = DatabaseService()
        self.embedding_service = EmbeddingService()
        self.vector_service = VectorService(self.embedding_service)
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None

        # SQL generation prompt template
        self.system_prompt = """
You are an expert SQL query generator that converts natural language questions into accurate SQL queries.

CORE PRINCIPLES:
1. Generate syntactically correct SQL for the specific database system
2. Use proper table and column names from the provided schema
3. Apply appropriate filters, joins, and aggregations
4. Ensure queries are efficient and follow best practices
5. Provide clear explanations for your reasoning

RESPONSE FORMAT:
You must respond with a JSON object containing:
- sql: The generated SQL query
- explanation: Clear explanation of what the query does
- confidence: Confidence score between 0 and 1
- tables_used: Array of table names used
- columns_used: Array of column names used
- reasoning: Step-by-step reasoning process
- query_type: Type of SQL operation (SELECT, COUNT, SUM, etc.)

GUIDELINES:
- Always use explicit JOIN syntax instead of comma-separated FROM clauses
- Include appropriate WHERE clauses for filtering
- Use proper aggregation functions when asking for totals, counts, averages
- Handle date ranges and time periods correctly
- Consider case sensitivity in string comparisons
- Use LIMIT/TOP for result size restrictions when appropriate
"""

        self.user_prompt_template = """
### DATABASE SCHEMA ###
{schema_info}

### PREVIOUS CONTEXT ###
{context_info}

### QUESTION ###
User's Question: {question}

### INSTRUCTIONS ###
1. Analyze the question to understand what data is being requested
2. Identify the relevant tables and columns from the schema
3. Determine the appropriate joins, filters, and aggregations
4. Generate the SQL query following best practices
5. Provide reasoning for your choices

Generate a response in the specified JSON format.
"""

    async def generate_sql(self, query: Text2SQLQuery, db_session) -> Text2SQLResponse:
        """Generate SQL from natural language question with semantic business context"""
        debug_logger.debug(f"Generate SQL from natural language question with semantic business contex")

        try:
            # First, try progressive retrieval with business semantics
            semantic_context = await self._get_semantic_context_with_progressive_retrieval(
                question=query.question,
                database_alias=query.database_alias,
                db_session=db_session
            )

            debug_logger.debug(f"Get the semantic coontext from the RAG: {semantic_context}")

            if semantic_context and (semantic_context.get('relevant_tables') or
                                    semantic_context.get('business_entities') or
                                    semantic_context.get('business_metrics')):
                # Use progressive retrieval result with business entity mappings
                debug_logger.debug(f"Using progressive retrieval with business semantics for: {query.question}")
                schema_info = self._format_semantic_context_as_schema(semantic_context)

                debug_logger.debug(f"Get schema infor from vector document: {schema_info}")
            else:
                # Fallback to traditional schema retrieval
                debug_logger.debug(f"Falling back to traditional schema retrieval for: {query.question}")
                schema_info = await self._get_database_schema(query.database_alias, db_session)
                debug_logger.debug(f"Get schema infor from database: {schema_info}")

            # Build context from conversation history

            context_info = self._build_context_info(query.context)

            # Generate SQL using LLM with enhanced schema info
            sql_response = await self._generate_sql_with_llm(
                question=query.question,
                schema_info=schema_info,
                context_info=context_info
            )

            # Validate and enhance the response
            validated_response = await self._validate_and_enhance_sql(
                sql_response=sql_response,
                database_alias=query.database_alias,
                thread_id=query.thread_id or self._generate_thread_id()
            )

            return validated_response

        except Exception as e:
            logger.error(f"Error generating SQL: {str(e)}")
            raise Exception(f"Failed to generate SQL query: {str(e)}")

    async def _get_semantic_context_with_progressive_retrieval(
        self,
        question: str,
        database_alias: str,
        db_session
    ) -> Optional[Dict[str, Any]]:
        """Get semantic context using progressive retrieval with business entities and metrics"""
        try:
            # Generate embedding for the question
            question_embedding = await self.embedding_service.get_embedding(question)

            # Use progressive retrieval to get relevant context
            context = await ProgressiveRetrievalService.retrieve_relevant_context(
                db=db_session,
                db_alias=database_alias,
                question=question,
                query_embedding=question_embedding,
                max_tables=10,
                similarity_threshold=0.7
            )

            debug_logger.debug(f"Progressive retrieval found {len(context['relevant_tables'])} tables, "
                       f"{len(context['business_entities'])} entities, "
                       f"{len(context['business_metrics'])} metrics")

            return context

        except Exception as e:
            logger.error(f"Error in progressive retrieval: {str(e)}")
            return None

    def _format_semantic_context_as_schema(self, context: Dict[str, Any]) -> str:
        """Format progressive retrieval context into schema string with business semantics"""
        schema_parts = []

        # Add business entity mappings
        if context.get('business_entities'):
            schema_parts.append("### BUSINESS ENTITY MAPPINGS ###")
            schema_parts.append("These map business concepts to database tables:")
            for entity in context['business_entities']:
                mapping_info = [
                    f"- **{entity.entity_name}** ({entity.entity_type})"
                ]
                if entity.description:
                    mapping_info.append(f"  Description: {entity.description}")
                if entity.source_mapping:
                    primary = entity.source_mapping.get('primary_table', '')
                    related = [t.get('table', '') for t in entity.source_mapping.get('related_tables', [])]
                    all_tables = [primary] + related if primary else related
                    if all_tables:
                        mapping_info.append(f"  Maps to tables: {', '.join(all_tables)}")
                schema_parts.append('\n'.join(mapping_info))
            schema_parts.append("")

        # Add business metrics
        if context.get('business_metrics'):
            schema_parts.append("### BUSINESS METRICS ###")
            schema_parts.append("These define calculated business values:")
            for metric in context['business_metrics']:
                metric_info = [
                    f"- **{metric.metric_name}**"
                ]
                if metric.metric_definition:
                    if metric.metric_definition.get('description'):
                        metric_info.append(f"  Description: {metric.metric_definition['description']}")
                    if metric.metric_definition.get('calculation'):
                        metric_info.append(f"  Calculation: {metric.metric_definition['calculation']}")
                    if metric.metric_definition.get('tables'):
                        tables = ', '.join(metric.metric_definition.get('tables', []))
                        metric_info.append(f"  Uses tables: {tables}")
                schema_parts.append('\n'.join(metric_info))
            schema_parts.append("")

        # Add relevant tables with columns
        if context.get('relevant_tables'):
            schema_parts.append("### RELEVANT DATABASE TABLES ###")
            for table_ctx in context['relevant_tables']:
                table = table_ctx['table']
                schema_parts.append(f"\nTable: {table.schema_name}.{table.table_name}")
                if table.description:
                    schema_parts.append(f"Description: {table.description}")

                # Add columns
                if table_ctx.get('columns'):
                    schema_parts.append("Columns:")
                    for col in table_ctx['columns']:
                        col_info = f"  - {col.column_name} ({col.data_type})"
                        if col.column_description:
                            col_info += f" - {col.column_description}"
                        schema_parts.append(col_info)

                # Add relationships
                if table_ctx.get('relationships'):
                    schema_parts.append("Relationships:")
                    for rel in table_ctx['relationships']:
                        schema_parts.append(
                            f"  - {rel.relationship_type}: {rel.source_table_id} -> {rel.target_table_id}"
                        )

        # Add query templates
        if context.get('query_templates'):
            schema_parts.append("\n### SIMILAR QUERY TEMPLATES ###")
            schema_parts.append("These are examples of similar queries:")
            for template in context['query_templates']:
                template_info = [
                    f"- **{template.template_name}**"
                ]
                if template.description:
                    template_info.append(f"  Description: {template.description}")
                if template.sql_template:
                    template_info.append(f"  SQL Template:\n  ```sql\n  {template.sql_template}\n  ```")
                schema_parts.append('\n'.join(template_info))

        return '\n'.join(schema_parts)

    async def _get_database_schema(self, database_alias: str, db_session) -> str:
        """Get formatted database schema information using vector documents first, with fallback to direct DB introspection"""
        try:
            # First, try to get schema from vector documents
            schema_from_vectors = await self._get_schema_from_vector_documents(database_alias, db_session)

            if schema_from_vectors:
                logger.info(f"Retrieved schema for {database_alias} from vector documents")
                return schema_from_vectors

            # Fallback to direct database introspection if no vector documents found
            logger.info(f"No vector documents found for {database_alias}, falling back to direct DB introspection")
            return await self._get_schema_from_database_introspection(database_alias, db_session)

        except Exception as e:
            logger.error(f"Error getting database schema: {str(e)}")
            return f"Error retrieving schema for database: {database_alias} - {str(e)}"

    async def _get_schema_from_vector_documents(self, database_alias: str, db_session) -> Optional[str]:
        """Get schema information from vector documents"""
        try:
            # Search for table documents for this database
            table_search = VectorSearchRequest(
                query="table schema structure",
                db_alias=database_alias,
                resource_type='table_doc',
                top_k=50  # Get more tables for comprehensive schema
            )
         

            table_docs = await self.vector_service.search_similar(db_session, table_search)

            logger.debug(f("from vector db get the tables for db {database_alias}, result: {table_docs}"))

            # Search for column documents for this database
            column_search = VectorSearchRequest(
                query="column field definition",
                db_alias=database_alias,
                resource_type='column_doc',
                top_k=200  # Get more columns for comprehensive schema
            )

            column_docs = await self.vector_service.search_similar(db_session, column_search)

            logger.debug(f("from vector db get the tables for db {database_alias}, result: {column_docs}"))

            # If no documents found, return None to trigger fallback
            if not table_docs and not column_docs:
                return None

            schema_parts = []
            schema_parts.append(f"Database: {database_alias} (from vector documents)")
            schema_parts.append("=" * 50)

            # Group tables and their columns
            tables_info = {}

            # Process table documents
            for doc_result in table_docs:
                doc = doc_result.document
                if doc.metadata and 'table' in doc.metadata:
                    schema_name = doc.metadata.get('schema', 'public')
                    table_name = doc.metadata['table']
                    full_table_name = f"{schema_name}.{table_name}"

                    if full_table_name not in tables_info:
                        tables_info[full_table_name] = {
                            'description': doc.content,
                            'columns': [],
                            'schema': schema_name,
                            'table': table_name,
                            'metadata': doc.metadata
                        }

            # Process column documents and group by table
            for doc_result in column_docs:
                doc = doc_result.document
                if doc.metadata and 'table' in doc.metadata and 'column' in doc.metadata:
                    schema_name = doc.metadata.get('schema', 'public')
                    table_name = doc.metadata['table']
                    full_table_name = f"{schema_name}.{table_name}"
                    column_name = doc.metadata['column']

                    if full_table_name not in tables_info:
                        tables_info[full_table_name] = {
                            'description': f"Table: {table_name}",
                            'columns': [],
                            'schema': schema_name,
                            'table': table_name,
                            'metadata': doc.metadata
                        }

                    tables_info[full_table_name]['columns'].append({
                        'name': column_name,
                        'description': doc.content,
                        'metadata': doc.metadata
                    })

            # Build schema output grouped by schema
            schemas = {}
            for full_table_name, table_info in tables_info.items():
                schema_name = table_info['schema']
                if schema_name not in schemas:
                    schemas[schema_name] = {}
                schemas[schema_name][table_info['table']] = table_info

            # Format output
            for schema_name, schema_tables in schemas.items():
                schema_parts.append(f"\nSchema: {schema_name}")

                for table_name, table_info in schema_tables.items():
                    schema_parts.append(f"\nTable: {schema_name}.{table_name}")
                    schema_parts.append(f"Description: {table_info['description']}")

                    # Add columns
                    columns = table_info.get('columns', [])
                    if columns:
                        schema_parts.append("Columns:")
                        # Sort columns by name for consistency
                        for col in sorted(columns, key=lambda x: x['name']):
                            col_desc = col['description']
                            # Try to extract data type from description if available
                            data_type = col['metadata'].get('data_type', 'unknown')
                            col_info = f"  - {col['name']} ({data_type})"
                            if col_desc:
                                col_info += f" - {col_desc}"
                            schema_parts.append(col_info)
                    else:
                        schema_parts.append("Columns: (No column information available)")

                    schema_parts.append("")  # Empty line between tables

            result = "\n".join(schema_parts) if schema_parts else None
            return result

        except Exception as e:
            logger.error(f"Error retrieving schema from vector documents: {str(e)}")
            return None

    async def _get_schema_from_database_introspection(self, database_alias: str, db_session) -> str:
        """Get schema information by directly introspecting the database (fallback method)"""
        try:
            # Get database connection
            db_connection = await self.database_service.get_database_connection(db_session, database_alias)
            if not db_connection:
                return f"Database connection '{database_alias}' not found"

            # Introspect database to get schema
            metadata = await self.database_service.introspect_database(db_connection)

            schema_parts = []
            schema_parts.append(f"Database: {database_alias} (from direct introspection)")
            schema_parts.append("=" * 50)

            # Process schemas and tables from introspection
            schemas = metadata.get('schemas', {})
            for schema_name, schema_tables in schemas.items():
                schema_parts.append(f"\nSchema: {schema_name}")

                for table_name, table_info in schema_tables.items():
                    table_meta = table_info.get('metadata', {})
                    schema_parts.append(f"\nTable: {schema_name}.{table_name}")
                    schema_parts.append(f"Type: {table_meta.get('type', 'TABLE')}")
                    schema_parts.append(f"Description: {table_meta.get('comment', 'No description')}")

                    # Add columns
                    columns = table_info.get('columns', [])
                    if columns:
                        schema_parts.append("Columns:")
                        for col in columns:
                            col_info = f"  - {col['name']} ({col['data_type']})"
                            if not col.get('is_nullable', True):
                                col_info += " NOT NULL"
                            if col.get('comment'):
                                col_info += f" - {col['comment']}"
                            schema_parts.append(col_info)

                    # Add sample data if available
                    sample_data = table_info.get('sample_data', [])
                    if sample_data:
                        schema_parts.append("Sample Data (first 1 rows):")
                        for i, row in enumerate(sample_data[:1]):
                            schema_parts.append(f"  Row {i+1}: {dict(row)}")

                    schema_parts.append("")  # Empty line between tables

            return "\n".join(schema_parts) if schema_parts else f"No schema information available for {database_alias}"

        except Exception as e:
            logger.error(f"Error getting database schema from introspection: {str(e)}")
            return f"Error retrieving schema for database: {database_alias} - {str(e)}"

    def _build_context_info(self, context: List[Dict[str, Any]]) -> str:
        """Build context information from conversation history"""
        if not context:
            return "No previous context."

        context_parts = []
        for i, ctx in enumerate(context[-5:], 1):  # Last 5 messages
            if 'question' in ctx and 'sql' in ctx:
                context_parts.append(f"{i}. Question: {ctx['question']}")
                context_parts.append(f"   SQL: {ctx['sql']}")

        return "\n".join(context_parts) if context_parts else "No previous context."

    async def _generate_sql_with_llm(self, question: str, schema_info: str, context_info: str) -> Dict[str, Any]:
        """Generate SQL using Language Model"""
        if not self.client:
            raise Exception("OpenAI API key not configured")

        user_prompt = self.user_prompt_template.format(
            schema_info=schema_info,
            context_info=context_info,
            question=question
        )

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content
            sql_response = json.loads(content)

            return sql_response

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from LLM: {e}")
            raise Exception("Generated response was not valid JSON")
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            raise Exception(f"Failed to generate SQL with AI: {str(e)}")

    async def _validate_and_enhance_sql(
        self,
        sql_response: Dict[str, Any],
        database_alias: str,
        thread_id: str
    ) -> Text2SQLResponse:
        """Validate and enhance the SQL response"""

        # Extract required fields with defaults
        sql = sql_response.get('sql', '')
        explanation = sql_response.get('explanation', 'SQL query generated from natural language')
        confidence = min(max(float(sql_response.get('confidence', 0.7)), 0.0), 1.0)
        tables_used = sql_response.get('tables_used', [])
        columns_used = sql_response.get('columns_used', [])
        reasoning = sql_response.get('reasoning', 'Generated using AI language model')
        query_type = sql_response.get('query_type', 'SELECT')

        # Basic SQL validation
        if not sql.strip():
            raise Exception("Generated SQL query is empty")

        # Clean up SQL formatting
        sql = self._format_sql(sql)

        # Validate SQL syntax (basic checks)
        await self._basic_sql_validation(sql, database_alias)

        return Text2SQLResponse(
            sql=sql,
            explanation=explanation,
            confidence=confidence,
            tables_used=tables_used,
            columns_used=columns_used,
            reasoning=reasoning,
            thread_id=thread_id,
            query_type=query_type.upper()
        )

    def _format_sql(self, sql: str) -> str:
        """Format SQL for better readability"""
        # Remove extra whitespace and normalize
        sql = re.sub(r'\s+', ' ', sql.strip())

        # Ensure SQL ends with semicolon
        if not sql.endswith(';'):
            sql += ';'

        return sql

    async def _basic_sql_validation(self, sql: str, database_alias: str) -> None:
        """Perform basic SQL validation with improved keyword detection"""
        import re

        # Check for required SELECT statement first
        sql_upper = sql.upper().strip()
        if not sql_upper.startswith('SELECT'):
            raise Exception("Only SELECT queries are allowed")

        # Check for dangerous operations using word boundaries
        # This ensures we match whole words, not substrings
        dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'TRUNCATE', 'ALTER', 'CREATE']

        for keyword in dangerous_keywords:
            # Use word boundary regex to match whole words only
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, sql_upper):
                # Additional check: make sure it's not in a string literal or comment
                if self._is_dangerous_keyword_in_context(sql_upper, keyword):
                    raise Exception(f"Query contains potentially dangerous operation: {keyword}")

        # Additional validations can be added here
        logger.info(f"SQL validation passed for database: {database_alias}")

    def _is_dangerous_keyword_in_context(self, sql_upper: str, keyword: str) -> bool:
        """Check if a dangerous keyword is in a dangerous context (not in string literals/comments)"""
        import re

        # Simple heuristic: if the keyword appears at the start of a statement or after semicolon
        # This is not foolproof but covers most cases
        dangerous_patterns = [
            r'^\s*' + re.escape(keyword) + r'\b',  # At start of query
            r';\s*' + re.escape(keyword) + r'\b',  # After semicolon
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, sql_upper):
                return True

        return False

    def _generate_thread_id(self) -> str:
        """Generate a unique thread ID"""
        from uuid import uuid4
        return str(uuid4())

    def _serialize_row_data(self, row_data: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize database row data to handle datetime and other non-JSON serializable objects"""
        import uuid
        from datetime import datetime, date, time
        from decimal import Decimal

        serialized_row = {}
        for key, value in row_data.items():
            if isinstance(value, datetime):
                serialized_row[key] = value.isoformat()
            elif isinstance(value, date):
                serialized_row[key] = value.isoformat()
            elif isinstance(value, time):
                serialized_row[key] = value.isoformat()
            elif isinstance(value, uuid.UUID):
                serialized_row[key] = str(value)
            elif isinstance(value, Decimal):
                serialized_row[key] = float(value)
            elif hasattr(value, 'isoformat'):
                # Handle any other datetime-like objects
                serialized_row[key] = value.isoformat()
            else:
                serialized_row[key] = value
        return serialized_row

    async def get_suggested_questions(self, database_alias: str, db_session, limit: int = 5) -> List[str]:
        """Generate suggested questions for a database"""
        try:
            schema_info = await self._get_database_schema(database_alias, db_session)

            if not self.client:
                # Return fallback questions if no AI available
                return [
                    "Show me the total number of records in each table",
                    "What are the most recent entries?",
                    "Show me a summary of the data",
                    "What are the unique values in the main columns?",
                    "Show me data from the last 30 days"
                ]

            suggestion_prompt = f"""
Based on the following database schema, suggest {limit} natural language questions that would be useful for data analysis:

{schema_info}

Guidelines:
- Focus on questions that would provide business insights
- Include questions about trends, totals, comparisons, and patterns
- Make questions specific to the available data
- Ensure questions can be answered with SELECT queries

Return only the questions as a JSON array of strings.
"""

            response = await self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are a data analyst suggesting useful questions for database exploration."},
                    {"role": "user", "content": suggestion_prompt}
                ],
                temperature=0.7,
                max_tokens=500,
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content
            suggestions = json.loads(content)

            # Extract questions from response
            if isinstance(suggestions, dict) and 'questions' in suggestions:
                return suggestions['questions'][:limit]
            elif isinstance(suggestions, list):
                return suggestions[:limit]
            else:
                return []

        except Exception as e:
            logger.error(f"Error generating suggested questions: {str(e)}")
            return []

    async def execute_generated_sql(
        self,
        sql: str,
        database_alias: str,
        db_session,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """Execute the generated SQL query and return results"""
        try:
            # Add LIMIT if not present and limit specified
            if limit and 'LIMIT' not in sql.upper():
                sql = sql.rstrip(';') + f' LIMIT {limit};'

            # Get database connection
            db_connection = await self.database_service.get_database_connection(db_session, database_alias)
            if not db_connection:
                raise Exception(f"Database connection '{database_alias}' not found")

            # Get the appropriate connector
            from app.schemas.database import DatabaseType
            connector = self.database_service.connectors.get(DatabaseType(db_connection.type))
            if not connector:
                raise Exception(f"Unsupported database type: {db_connection.type}")

            # Get connection parameters and execute query
            connection_params = self.database_service._get_connection_params(db_connection)

            # Execute the SQL query directly using asyncpg for PostgreSQL
            if db_connection.type == DatabaseType.POSTGRES.value:
                import asyncpg
                conn = await asyncpg.connect(**connection_params)
                try:
                    rows = await conn.fetch(sql)
                    if rows:
                        columns = list(rows[0].keys())
                        data = [self._serialize_row_data(dict(row)) for row in rows]
                    else:
                        columns = []
                        data = []

                    return {
                        'columns': columns,
                        'data': data,
                        'total_rows': len(data)
                    }
                finally:
                    await conn.close()
            else:
                raise Exception(f"Query execution not implemented for database type: {db_connection.type}")

        except Exception as e:
            logger.error(f"Error executing generated SQL: {str(e)}")
            raise Exception(f"Failed to execute query: {str(e)}")