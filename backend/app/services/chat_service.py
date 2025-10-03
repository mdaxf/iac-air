from typing import List, Optional, Dict, Any, Union
import uuid
import json
from datetime import datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.chat import Conversation as ConversationModel, ChatMessage
from app.schemas.chat import (
    ConversationCreate, Conversation, ChatMessageCreate, ChatResponse,
    ConversationMessage, DrillDownRequest, ExportRequest
)
from app.core.logging_config import Logger, log_method_calls, debug_logger
from app.services.vector_service import VectorService
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService
from app.services.sql_service import SQLService
from app.services.text2sql_service import Text2SQLService, Text2SQLQuery


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime and other non-serializable objects"""

    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, uuid.UUID):
            return str(obj)
        elif isinstance(obj, Decimal):
            return float(obj)
        elif hasattr(obj, 'isoformat'):
            # Handle date, time, and other datetime-like objects
            return obj.isoformat()
        return super().default(obj)


class ChatService:
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.vector_service = VectorService(self.embedding_service)
        self.llm_service = LLMService()
        self.sql_service = SQLService()
        self.text2sql_service = Text2SQLService()

    def _serialize_uuid_in_data(self, data: Union[Dict, List, Any]) -> Union[Dict, List, Any]:
        """Recursively convert UUID, datetime, and other non-JSON serializable objects to strings"""
        if isinstance(data, dict):
            return {key: self._serialize_uuid_in_data(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._serialize_uuid_in_data(item) for item in data]
        elif isinstance(data, uuid.UUID):
            return str(data)
        elif isinstance(data, datetime):
            return data.isoformat()
        elif hasattr(data, '__str__') and 'uuid' in str(type(data)).lower():
            # Handle asyncpg.pgproto.pgproto.UUID and other UUID-like objects
            return str(data)
        elif hasattr(data, 'isoformat'):
            # Handle date, time, and other datetime-like objects
            return data.isoformat()
        elif isinstance(data, (bytes, bytearray)):
            # Handle binary data
            return str(data)
        elif hasattr(data, '__dict__') and not isinstance(data, (str, int, float, bool, type(None))):
            # Handle complex objects by converting to dict
            try:
                return self._serialize_uuid_in_data(data.__dict__)
            except (AttributeError, TypeError):
                return str(data)
        else:
            return data

    def _serialize_datetime(self, dt) -> str:
        """Helper method to safely serialize datetime objects"""
        if hasattr(dt, 'isoformat'):
            return dt.isoformat()
        return str(dt)

    @log_method_calls
    async def create_conversation(self, db: AsyncSession, conversation_data: ConversationCreate) -> Conversation:
        """Create a new conversation"""
        db_conversation = ConversationModel(
            id=str(uuid.uuid4()),
            title=conversation_data.title,
            user_id=conversation_data.user_id,
            db_alias=conversation_data.db_alias,
            auto_execute_query=conversation_data.auto_execute_query
        )

        db.add(db_conversation)
        await db.commit()
        await db.refresh(db_conversation)
        Logger.info(f"Created conversation {db_conversation.id} for user {conversation_data.user_id}")
        return Conversation.model_validate(db_conversation)

    @log_method_calls
    async def get_conversation(self, db: AsyncSession, conversation_id: str) -> Optional[Conversation]:
        """Get a conversation by ID"""
        query = select(ConversationModel).where(ConversationModel.id == conversation_id)
        result = await db.execute(query)
        db_conversation = result.scalar_one_or_none()
        if db_conversation:
            return Conversation.model_validate(db_conversation)
        return None

    @log_method_calls
    async def delete_conversation(self, db: AsyncSession, conversation_id: str, user_id: str) -> bool:
        """Delete a conversation and all its messages"""
        query = select(ConversationModel).where(
            ConversationModel.id == conversation_id,
            ConversationModel.user_id == user_id  # Ensure user can only delete their own conversations
        )
        result = await db.execute(query)
        db_conversation = result.scalar_one_or_none()

        if not db_conversation:
            return False

        await db.delete(db_conversation)
        await db.commit()
        return True

    @log_method_calls
    async def get_user_conversations(self, db: AsyncSession, user_id: str, limit: int = 100, offset: int = 0) -> List[Conversation]:
        """Get conversations for a user with pagination"""
        debug_logger.debug(f"Get conversations for a user with pagination for: {user_id}, {limit}, {offset}")
        query = (
            select(ConversationModel)
            .where(ConversationModel.user_id == user_id)
            .order_by(ConversationModel.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        debug_logger.debug(f"query: {query}")
        result = await db.execute(query)
        debug_logger.debug(f"resilt: {result}")

        db_conversations = result.scalars().all()
        
        debug_logger.debug(f"db_conversations: {db_conversations}")

        list_result = [Conversation.model_validate(db_conv) for db_conv in db_conversations]

        debug_logger.debug(f"list_result: {list_result}")

        return list_result

    @log_method_calls
    async def get_conversation_messages(self, db: AsyncSession, conversation_id: str, limit: int = 50, offset: int = 0) -> List[ChatResponse]:
        """Get messages for a specific conversation"""
        query = (
            select(ChatMessage)
            .where(ChatMessage.conversation_id == conversation_id)
            .order_by(ChatMessage.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await db.execute(query)
        db_messages = result.scalars().all()

        # Convert ChatMessage models to ChatResponse objects
        chat_responses = []
        for msg in db_messages:
            chat_response = ChatResponse(
                answer_id=str(msg.id),
                conversation_id=msg.conversation_id,
                narrative=msg.response or "No response available",
                sql=msg.sql_query,
                table_preview=self._serialize_uuid_in_data(msg.result_data),
                chart_meta=self._serialize_uuid_in_data(msg.chart_meta),
                provenance=self._serialize_uuid_in_data(msg.provenance or {}),
                created_at=self._serialize_datetime(msg.created_at)
            )
            chat_responses.append(chat_response)

        return chat_responses

    @log_method_calls
    async def get_conversation_messages_complete(self, db: AsyncSession, conversation_id: str, limit: int = 50, offset: int = 0) -> List[ConversationMessage]:
        """Get complete conversation messages with both user questions and AI responses"""
        query = (
            select(ChatMessage)
            .where(ChatMessage.conversation_id == conversation_id)
            .order_by(ChatMessage.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await db.execute(query)
        db_messages = result.scalars().all()

        # Convert ChatMessage models to ConversationMessage objects
        conversation_messages = []
        for msg in db_messages:
            conversation_message = ConversationMessage(
                message_id=str(msg.id),
                conversation_id=msg.conversation_id,
                user_question=msg.text,  # The original user question
                ai_response=msg.response or "No response available",  # The AI response
                sql=msg.sql_query,
                table_preview=self._serialize_uuid_in_data(msg.result_data),
                chart_meta=self._serialize_uuid_in_data(msg.chart_meta),
                provenance=self._serialize_uuid_in_data(msg.provenance or {}),
                created_at=self._serialize_datetime(msg.created_at)
            )
            conversation_messages.append(conversation_message)

        return conversation_messages

    @log_method_calls
    async def execute_pending_query(self, db: AsyncSession, message_id: str, modified_sql: Optional[str] = None) -> ChatResponse:
        """Execute a pending query (when auto_execute_query is false)"""
        try:
            # Get the original message
            query = select(ChatMessage).where(ChatMessage.id == message_id)
            result = await db.execute(query)
            original_message = result.scalar_one_or_none()

            if not original_message:
                raise ValueError("Original message not found")

            # Use modified SQL if provided, otherwise use the original SQL
            sql_to_execute = modified_sql if modified_sql else original_message.sql_query

            if not sql_to_execute:
                raise ValueError("No SQL query to execute")
            # Execute the SQL query
            execution_result = await self.text2sql_service.execute_generated_sql(
                sql=sql_to_execute,
                database_alias=original_message.db_alias,
                db_session=db,
                limit=100
            )

            result_data = execution_result.get('data', [])
            chart_meta = None

            # Generate chart metadata if we have data
            if result_data:
                chart_meta = self._generate_chart_metadata(result_data, original_message.text)

            # Update the original message with execution results
            narrative = f"{original_message.response}\n\nQuery executed successfully!"
            original_message.response = narrative
            original_message.sql_query = sql_to_execute
            original_message.result_data = json.loads(json.dumps(result_data, cls=DateTimeEncoder))
            original_message.chart_meta = json.loads(json.dumps(chart_meta, cls=DateTimeEncoder))

            # Update provenance to reflect execution
            provenance = original_message.provenance or {}
            provenance['query_status'] = 'executed'
            provenance['execution_time'] = datetime.now().isoformat()
            original_message.provenance = json.loads(json.dumps(provenance, cls=DateTimeEncoder))

            await db.commit()
            await db.refresh(original_message)

            return ChatResponse(
                answer_id=str(original_message.id),
                conversation_id=original_message.conversation_id,
                narrative=narrative,
                sql=sql_to_execute,
                table_preview=self._serialize_uuid_in_data(result_data[:20] if result_data else None),
                chart_meta=self._serialize_uuid_in_data(chart_meta),
                provenance=self._serialize_uuid_in_data(provenance),
                created_at=self._serialize_datetime(original_message.created_at)
            )

        except Exception as e:
            Logger.error(f"Error executing pending query: {str(e)}")
            # Rollback the session to handle any transaction issues
            await db.rollback()

            try:
                # Re-fetch the original message after rollback
                query = select(ChatMessage).where(ChatMessage.id == message_id)
                result = await db.execute(query)
                original_message = result.scalar_one_or_none()

                if original_message:
                    # Update the message with error information
                    error_narrative = f"{original_message.response}\n\nQuery execution failed: {str(e)}"
                    original_message.response = error_narrative

                    # Update provenance
                    provenance = original_message.provenance or {}
                    provenance['query_status'] = 'failed'
                    provenance['error'] = str(e)
                    provenance['error_time'] = datetime.now().isoformat()
                    original_message.provenance = json.loads(json.dumps(provenance, cls=DateTimeEncoder))

                    await db.commit()
                    await db.refresh(original_message)

                    return ChatResponse(
                        answer_id=str(original_message.id),
                        conversation_id=original_message.conversation_id,
                        narrative=error_narrative,
                        sql=sql_to_execute if 'sql_to_execute' in locals() else original_message.sql_query,
                        table_preview=None,
                        chart_meta=None,
                        provenance=self._serialize_uuid_in_data(provenance),
                        created_at=self._serialize_datetime(original_message.created_at)
                    )
                else:
                    raise ValueError("Could not retrieve original message after error")

            except Exception as rollback_error:
                Logger.error(f"Error during rollback handling: {str(rollback_error)}")
                raise e  # Re-raise the original exception

    @log_method_calls
    async def regenerate_query(self, db: AsyncSession, message_id: str, additional_context: Optional[str] = None) -> ChatResponse:
        """Regenerate a query for a message with additional context"""
        # Get the original message
        query = select(ChatMessage).where(ChatMessage.id == message_id)
        result = await db.execute(query)
        original_message = result.scalar_one_or_none()

        if not original_message:
            raise ValueError("Original message not found")

        try:
            # Create enhanced question with additional context if provided
            enhanced_question = original_message.text
            if additional_context:
                enhanced_question = f"{original_message.text}\n\nAdditional context: {additional_context}"

            # Use Text2SQL service to regenerate the query
            text2sql_query = Text2SQLQuery(
                question=enhanced_question,
                database_alias=original_message.db_alias,
                thread_id=original_message.conversation_id,
                sample_size=100
            )

            text2sql_response = await self.text2sql_service.generate_sql(text2sql_query, db)

            sql_query = text2sql_response.sql
            explanation = text2sql_response.explanation
            reasoning = text2sql_response.reasoning
            confidence = text2sql_response.confidence
            tables_used = text2sql_response.tables_used
            columns_used = text2sql_response.columns_used

            # Update the message with new generated query (don't execute)
            narrative = f"{explanation}\n\nRegenerated SQL Query:\n```sql\n{sql_query}\n```\n\nReasoning: {reasoning}\n\nReview the updated query above. You can modify it, regenerate it again, or execute it to see the results."

            original_message.response = narrative
            original_message.sql_query = sql_query

            # Update provenance
            provenance = {
                'db_alias': original_message.db_alias,
                'tables': tables_used,
                'columns': columns_used,
                'confidence': confidence,
                'query_type': text2sql_response.query_type,
                'thread_id': text2sql_response.thread_id,
                'auto_execute': False,
                'query_status': 'regenerated',
                'regeneration_time': datetime.now().isoformat()
            }
            original_message.provenance = json.loads(json.dumps(provenance, cls=DateTimeEncoder))

            await db.commit()
            await db.refresh(original_message)

            return ChatResponse(
                answer_id=str(original_message.id),
                conversation_id=original_message.conversation_id,
                narrative=narrative,
                sql=sql_query,
                table_preview=None,
                chart_meta=None,
                provenance=self._serialize_uuid_in_data(provenance),
                created_at=self._serialize_datetime(original_message.created_at)
            )

        except Exception as e:
            Logger.error(f"Error regenerating query: {str(e)}")
            error_narrative = f"Failed to regenerate query: {str(e)}"

            return ChatResponse(
                answer_id=str(original_message.id),
                conversation_id=original_message.conversation_id,
                narrative=error_narrative,
                sql=original_message.sql_query,
                table_preview=None,
                chart_meta=None,
                provenance=self._serialize_uuid_in_data(original_message.provenance or {}),
                created_at=self._serialize_datetime(original_message.created_at)
            )

    @log_method_calls
    async def get_conversation_first_question(self, db: AsyncSession, conversation_id: str) -> Optional[str]:
        """Get the first question from a conversation for title generation"""
        query = (
            select(ChatMessage)
            .where(ChatMessage.conversation_id == conversation_id)
            .order_by(ChatMessage.created_at.asc())
            .limit(1)
        )
        result = await db.execute(query)
        first_message = result.scalar_one_or_none()

        if first_message and first_message.text:
            # Truncate to 20-50 words as requested
            words = first_message.text.split()
            if len(words) <= 50:
                return first_message.text
            else:
                return ' '.join(words[:50]) + '...'
        return None

    @log_method_calls
    async def process_message(self, db: AsyncSession, message_data: ChatMessageCreate) -> ChatResponse:
        """Process a chat message using Text2SQL service with vector search fallback"""
        # Step 1: Get conversation to check auto_execute_query flag
        conversation = await self.get_conversation(db, message_data.conversation_id)
        auto_execute = conversation.auto_execute_query if conversation else True

        # Step 2: Create the message record
        message = ChatMessage(
            conversation_id=message_data.conversation_id,
            text=message_data.text,
            db_alias=message_data.db_alias
        )

        try:
            # Step 3: Use Text2SQL service for integrated AI query generation
            text2sql_query = Text2SQLQuery(
                question=message_data.text,
                database_alias=message_data.db_alias,
                thread_id=message_data.conversation_id,
                sample_size=100
            )

            # Generate SQL with Text2SQL service (includes schema discovery and vector search)
            text2sql_response = await self.text2sql_service.generate_sql(text2sql_query, db)

            sql_query = text2sql_response.sql
            explanation = text2sql_response.explanation
            reasoning = text2sql_response.reasoning
            confidence = text2sql_response.confidence
            tables_used = text2sql_response.tables_used
            columns_used = text2sql_response.columns_used

            debug_logger.debug(f"The AI response message: query: {sql_query} explanation: {explanation} tables_used: {tables_used}, columns_used:{columns_used} confidence: {confidence} and reasoning: {reasoning}")

            # Step 4: Conditionally execute the generated SQL based on auto_execute_query flag
            result_data = []
            chart_meta = None

            if auto_execute and sql_query and message_data.db_alias:
                try:
                    execution_result = await self.text2sql_service.execute_generated_sql(
                        sql=sql_query,
                        database_alias=message_data.db_alias,
                        db_session=db,
                        limit=100
                    )

                    result_data = execution_result.get('data', [])

                    # Generate chart metadata if we have data
                    if result_data:
                        chart_meta = self._generate_chart_metadata(result_data, message_data.text)

                    # Create comprehensive narrative combining explanation and reasoning
                    narrative = f"{explanation}\n\nAnalysis: {reasoning}"

                except Exception as e:
                    Logger.error(f"Error executing generated SQL: {str(e)}")
                    narrative = f"{explanation}\n\nNote: Query generation succeeded but execution failed: {str(e)}"
            elif not auto_execute and sql_query:
                # When auto_execute is false, provide the generated query for user review
                narrative = f"{explanation}\n\nGenerated SQL Query:\n```sql\n{sql_query}\n```\n\nReasoning: {reasoning}\n\nReview the query above. You can modify it, regenerate it, or execute it to see the results."
            else:
                narrative = f"{explanation}\n\nReasoning: {reasoning}"

            # Step 5: Create provenance information
            provenance = {
                'db_alias': message_data.db_alias,
                'tables': tables_used,
                'columns': columns_used,
                'confidence': confidence,
                'query_type': text2sql_response.query_type,
                'thread_id': text2sql_response.thread_id,
                'auto_execute': auto_execute,
                'query_status': 'executed' if auto_execute and result_data else ('pending' if not auto_execute and sql_query else 'failed')
            }

        except Exception as e:
            # Fallback to vector search if Text2SQL fails
            Logger.error(f"Text2SQL failed, falling back to vector search: {str(e)}")
            try:
                analysis_result = await self._analyze_query_intent_with_vector_fallback(
                    db, message_data.text, message_data.db_alias
                )
                sql_query = None
                result_data = []
                chart_meta = None
                narrative = f"I found these relevant tables: {', '.join(analysis_result['involved_tables'])}, but couldn't generate SQL. Error: {str(e)}"
                provenance = self._extract_provenance_from_analysis(analysis_result, message_data.db_alias)
            except Exception as fallback_error:
                Logger.error(f"Vector fallback also failed: {str(fallback_error)}")
                sql_query = None
                result_data = []
                chart_meta = None
                narrative = f"I encountered an error while processing your query: {str(e)}"
                provenance = {'db_alias': message_data.db_alias, 'error': str(e)}

        # Step 6: Update message with results (serialize UUIDs in JSONB fields)
        message.response = narrative
        message.sql_query = sql_query

        # Debug logging to identify datetime serialization issues
        debug_logger.debug(f"About to serialize result_data: {type(result_data)}")
        try:
            serialized_result_data = self._serialize_uuid_in_data(result_data)
            debug_logger.debug(f"Successfully serialized result_data")
        except Exception as e:
            debug_logger.error(f"Error serializing result_data: {e}")
            debug_logger.error(f"result_data content: {result_data}")
            raise

        debug_logger.debug(f"About to serialize chart_meta: {type(chart_meta)}")
        try:
            serialized_chart_meta = self._serialize_uuid_in_data(chart_meta)
            debug_logger.debug(f"Successfully serialized chart_meta")
        except Exception as e:
            debug_logger.error(f"Error serializing chart_meta: {e}")
            debug_logger.error(f"chart_meta content: {chart_meta}")
            raise

        debug_logger.debug(f"About to serialize provenance: {type(provenance)}")
        try:
            serialized_provenance = self._serialize_uuid_in_data(provenance)
            debug_logger.debug(f"Successfully serialized provenance")
        except Exception as e:
            debug_logger.error(f"Error serializing provenance: {e}")
            debug_logger.error(f"provenance content: {provenance}")
            raise

        # Use JSON serialization with custom encoder for JSONB fields
        message.result_data = json.loads(json.dumps(result_data, cls=DateTimeEncoder))
        message.chart_meta = json.loads(json.dumps(chart_meta, cls=DateTimeEncoder))
        message.provenance = json.loads(json.dumps(provenance, cls=DateTimeEncoder))

        debug_logger.debug(f"About to add message to database")
        db.add(message)
        debug_logger.debug(f"About to commit to database")
        await db.commit()
        debug_logger.debug(f"Successfully committed to database")
        await db.refresh(message)

        # Step 7: Update conversation title if this is the first message
        await self._update_conversation_title_if_first_message(db, message_data.conversation_id, message_data.text)

        # Step 8: Return response
        return ChatResponse(
            answer_id=str(message.id),
            conversation_id=message_data.conversation_id,
            narrative=narrative,
            sql=sql_query,
            table_preview=self._serialize_uuid_in_data(result_data[:20] if result_data else None),
            chart_meta=self._serialize_uuid_in_data(chart_meta),
            provenance=self._serialize_uuid_in_data(provenance),
            created_at=self._serialize_datetime(message.created_at)
        )
    @log_method_calls
    async def drill_down_analysis(self, db: AsyncSession, drill_request: DrillDownRequest) -> ChatResponse:
        """Perform drill-down analysis on previous results"""
        # Get the original message
        query = select(ChatMessage).where(ChatMessage.id == drill_request.answer_id)
        result = await db.execute(query)
        original_message = result.scalar_one_or_none()

        if not original_message:
            raise ValueError("Original answer not found")

        # Generate modified SQL based on drill-down criteria
        modified_sql = await self.llm_service.modify_sql_for_drilldown(
            original_message.sql_query,
            original_message.text,
            drill_request.filter_criteria
        )

        # Execute the modified query
        if modified_sql:
            execution_result = await self.sql_service.execute_sql(modified_sql, original_message.db_alias)
            result_data = execution_result.get('data', [])
            chart_meta = self._generate_chart_metadata(result_data, "Drill-down analysis")
        else:
            result_data = []
            chart_meta = None

        # Generate narrative for drill-down
        narrative = await self.llm_service.generate_drilldown_narrative(
            original_message.text,
            drill_request.filter_criteria,
            result_data
        )

        # Create new message for drill-down (serialize UUIDs in JSONB fields)
        drill_message = ChatMessage(
            conversation_id=original_message.conversation_id,
            text=f"Drill-down: {drill_request.filter_criteria}",
            response=narrative,
            sql_query=modified_sql,
            result_data=json.loads(json.dumps(result_data, cls=DateTimeEncoder)),
            chart_meta=json.loads(json.dumps(chart_meta, cls=DateTimeEncoder)),
            provenance=json.loads(json.dumps(original_message.provenance, cls=DateTimeEncoder)),
            db_alias=original_message.db_alias
        )

        db.add(drill_message)
        await db.commit()
        await db.refresh(drill_message)

        return ChatResponse(
            answer_id=str(drill_message.id),
            conversation_id=drill_message.conversation_id,
            narrative=narrative,
            sql=modified_sql,
            table_preview=self._serialize_uuid_in_data(result_data[:20] if result_data else None),
            chart_meta=self._serialize_uuid_in_data(chart_meta),
            provenance=self._serialize_uuid_in_data(drill_message.provenance),
            created_at=self._serialize_datetime(drill_message.created_at)
        )
    @log_method_calls
    async def export_results(self, db: AsyncSession, export_request: ExportRequest) -> Dict[str, Any]:
        """Export chat results to various formats"""
        # Get the message
        query = select(ChatMessage).where(ChatMessage.id == export_request.answer_id)
        result = await db.execute(query)
        message = result.scalar_one_or_none()

        if not message:
            raise ValueError("Answer not found")

        # Generate export data based on format
        if export_request.format.lower() == 'csv':
            export_data = await self._export_to_csv(message, export_request.include_sql)
        elif export_request.format.lower() == 'excel':
            export_data = await self._export_to_excel(message, export_request.include_sql)
        elif export_request.format.lower() == 'pdf':
            export_data = await self._export_to_pdf(message, export_request.include_sql)
        else:
            raise ValueError(f"Unsupported export format: {export_request.format}")

        return export_data

    async def _analyze_query_intent_with_vector_fallback(self, db: AsyncSession, user_query: str, db_alias: str) -> Dict[str, Any]:
        """Vector search fallback when Text2SQL fails"""
        try:
            return await self._analyze_query_intent(db, user_query, db_alias)
        except Exception as e:
            Logger.error(f"Vector search fallback failed: {str(e)}")
            # If vector search fails, try to get schema directly from database
            return await self._analyze_query_with_direct_schema(db, user_query, db_alias)

    async def _analyze_query_intent(self, db: AsyncSession, user_query: str, db_alias: str) -> Dict[str, Any]:
        """Step 2: AI + Vector DB Analysis to identify relevant tables and context"""
        # First, use vector search to find relevant table and column documentation
        from app.schemas.vector_document import VectorSearchRequest

        # Search for table documentation
        table_search = VectorSearchRequest(
            query=user_query,
            db_alias=db_alias,
            resource_type='table_doc',
            top_k=5
        )
        table_docs = await self.vector_service.search_similar(db, table_search)

        # Search for column documentation
        column_search = VectorSearchRequest(
            query=user_query,
            db_alias=db_alias,
            resource_type='column_doc',
            top_k=10
        )
        column_docs = await self.vector_service.search_similar(db, column_search)

        # Extract involved tables and build context
        involved_tables = set()
        context_parts = []
        analysis_steps = []

        # Process table documents
        for doc_result in table_docs:
            doc = doc_result.document
            if doc.metadata and 'table' in doc.metadata:
                table_name = f"{doc.metadata.get('schema', '')}.{doc.metadata['table']}"
                involved_tables.add(table_name)
                context_parts.append(f"TABLE: {table_name}")
                context_parts.append(f"Description: {doc.content}")
                context_parts.append("---")

                analysis_steps.append({
                    'step': 'table_identified',
                    'table': table_name,
                    'relevance_score': doc_result.score,
                    'reason': f"Matched query with score {doc_result.score:.3f}"
                })

        # Process column documents
        table_columns = {}
        for doc_result in column_docs:
            doc = doc_result.document
            if doc.metadata and 'table' in doc.metadata and 'column' in doc.metadata:
                table_name = f"{doc.metadata.get('schema', '')}.{doc.metadata['table']}"
                column_name = doc.metadata['column']

                if table_name not in table_columns:
                    table_columns[table_name] = []
                table_columns[table_name].append({
                    'name': column_name,
                    'content': doc.content,
                    'score': doc_result.score
                })

        # Add column information to context
        for table_name, columns in table_columns.items():
            context_parts.append(f"COLUMNS for {table_name}:")
            for col in sorted(columns, key=lambda x: x['score'], reverse=True)[:5]:  # Top 5 relevant columns
                context_parts.append(f"  - {col['name']}: {col['content']}")
            context_parts.append("---")

        # Use AI to refine the analysis
        analysis_prompt = f"""
        User Query: {user_query}
        Database: {db_alias}

        Found Tables: {', '.join(involved_tables)}

        Based on this query, identify:
        1. Primary tables needed for this query
        2. Key columns/fields mentioned or implied
        3. Type of analysis (aggregation, filtering, joining, etc.)
        4. Any business logic considerations

        Provide a brief analysis focusing on what tables and columns are most relevant.
        """

        try:
            ai_analysis = await self.llm_service.generate_analysis(analysis_prompt)
            analysis_steps.append({
                'step': 'ai_refinement',
                'analysis': ai_analysis
            })
        except Exception as e:
            ai_analysis = "AI analysis unavailable"

        return {
            'involved_tables': list(involved_tables),
            'context': "\n".join(context_parts),
            'table_columns': table_columns,
            'ai_analysis': ai_analysis,
            'analysis_steps': analysis_steps
        }

    @log_method_calls
    async def _generate_query_with_context(self, user_query: str, analysis_result: Dict[str, Any], db_alias: str) -> Optional[str]:
        """Step 3: Generate SQL query using AI with identified table context"""
        if not analysis_result['involved_tables']:
            return None

        # Build enhanced context for SQL generation
        context_for_sql = f"""
        Database: {db_alias}
        User Request: {user_query}

        AI Analysis: {analysis_result['ai_analysis']}

        Available Schema Information:
        {analysis_result['context']}

        Primary Tables Identified: {', '.join(analysis_result['involved_tables'])}
        """

        return await self.llm_service.generate_sql(user_query, context_for_sql, db_alias)

    async def _analyze_query_with_direct_schema(self, db: AsyncSession, user_query: str, db_alias: str) -> Dict[str, Any]:
        """Fallback: Analyze query using direct database schema introspection"""
        try:
            from app.services.database_service import DatabaseService
            database_service = DatabaseService()

            # Get database connection and schema
            db_connection = await database_service.get_database_connection(db, db_alias)
            if not db_connection:
                return {'involved_tables': [], 'context': f'Database {db_alias} not found', 'analysis_steps': []}

            # Introspect database schema
            metadata = await database_service.introspect_database(db_connection)

            # Build context from schema
            schema_parts = []
            table_names = []

            schemas = metadata.get('schemas', {})
            for schema_name, schema_tables in schemas.items():
                for table_name, table_info in schema_tables.items():
                    full_table_name = f"{schema_name}.{table_name}"
                    table_names.append(full_table_name)

                    schema_parts.append(f"Table: {full_table_name}")
                    table_meta = table_info.get('metadata', {})
                    if table_meta.get('comment'):
                        schema_parts.append(f"Description: {table_meta['comment']}")

                    # Add column information
                    columns = table_info.get('columns', [])[:10]  # Limit to first 10 columns
                    if columns:
                        schema_parts.append("Key Columns:")
                        for col in columns:
                            col_desc = f"  - {col['name']} ({col['data_type']})"
                            if col.get('comment'):
                                col_desc += f" - {col['comment']}"
                            schema_parts.append(col_desc)
                    schema_parts.append("---")

            return {
                'involved_tables': table_names[:10],  # Limit tables
                'context': "\n".join(schema_parts),
                'analysis_steps': [{'step': 'direct_schema_introspection', 'tables_found': len(table_names)}],
                'ai_analysis': f"Found {len(table_names)} tables in {db_alias} database"
            }

        except Exception as e:
            Logger.error(f"Direct schema analysis failed: {str(e)}")
            return {
                'involved_tables': [],
                'context': f'Failed to analyze database schema: {str(e)}',
                'analysis_steps': [{'step': 'schema_analysis_failed', 'error': str(e)}],
                'ai_analysis': f'Could not analyze {db_alias} database schema'
            }

    def _extract_provenance_from_analysis(self, analysis_result: Dict[str, Any], db_alias: str) -> Dict[str, Any]:
        """Extract provenance information from analysis result"""
        return {
            'db_alias': db_alias,
            'tables': analysis_result['involved_tables'],
            'schemas': list(set(table.split('.')[0] for table in analysis_result['involved_tables'] if '.' in table)),
            'analysis_steps': analysis_result.get('analysis_steps', []),
            'ai_analysis': analysis_result.get('ai_analysis', '')
        }

    def _build_context_from_docs(self, relevant_docs) -> str:
        """Build context string from relevant documents (legacy method)"""
        context_parts = []
        for doc_result in relevant_docs:
            doc = doc_result.document
            context_parts.append(f"Resource: {doc.resource_id}")
            context_parts.append(f"Type: {doc.resource_type}")
            context_parts.append(f"Content: {doc.content}")
            context_parts.append("---")

        return "\n".join(context_parts)

    def _extract_provenance(self, relevant_docs, db_alias: str) -> Dict[str, Any]:
        """Extract provenance information from documents"""
        tables = set()
        schemas = set()

        for doc_result in relevant_docs:
            doc = doc_result.document
            if doc.metadata and 'table' in doc.metadata:
                tables.add(f"{doc.metadata.get('schema', '')}.{doc.metadata['table']}")
                schemas.add(doc.metadata.get('schema', ''))

        return {
            'db_alias': db_alias,
            'tables': list(tables),
            'schemas': list(schemas),
            'document_count': len(relevant_docs)
        }

    def _generate_chart_metadata(self, data: List[Dict], query_text: str) -> Optional[Dict[str, Any]]:
        """Generate chart metadata based on data structure and query"""
        if not data:
            return None

        # Simple heuristics for chart type suggestion
        columns = list(data[0].keys()) if data else []
        numeric_columns = []
        text_columns = []

        for col in columns:
            sample_values = [row.get(col) for row in data[:10] if row.get(col) is not None]
            if sample_values and all(isinstance(v, (int, float)) for v in sample_values):
                numeric_columns.append(col)
            else:
                text_columns.append(col)

        chart_type = "table"  # Default
        if len(numeric_columns) >= 1 and len(text_columns) >= 1:
            if "time" in query_text.lower() or "date" in query_text.lower():
                chart_type = "line"
            else:
                chart_type = "bar"
        elif len(numeric_columns) >= 2:
            chart_type = "scatter"

        return {
            'type': chart_type,
            'x_axis': text_columns[0] if text_columns else columns[0],
            'y_axis': numeric_columns[0] if numeric_columns else columns[-1],
            'columns': columns,
            'numeric_columns': numeric_columns,
            'text_columns': text_columns
        }

    async def _export_to_csv(self, message: ChatMessage, include_sql: bool) -> Dict[str, Any]:
        """Export message results to CSV format"""
        # Implementation would generate CSV content
        return {
            'format': 'csv',
            'filename': f'export_{message.id}.csv',
            'content': 'CSV content here',  # Placeholder
            'size': 1024
        }

    async def _export_to_excel(self, message: ChatMessage, include_sql: bool) -> Dict[str, Any]:
        """Export message results to Excel format"""
        # Implementation would generate Excel content
        return {
            'format': 'excel',
            'filename': f'export_{message.id}.xlsx',
            'content': 'Excel content here',  # Placeholder
            'size': 2048
        }

    async def _export_to_pdf(self, message: ChatMessage, include_sql: bool) -> Dict[str, Any]:
        """Export message results to PDF format"""
        # Implementation would generate PDF content
        return {
            'format': 'pdf',
            'filename': f'export_{message.id}.pdf',
            'content': 'PDF content here',  # Placeholder
            'size': 4096
        }

    @log_method_calls
    async def _update_conversation_title_if_first_message(self, db: AsyncSession, conversation_id: str, message_text: str) -> None:
        """Update conversation title with first question if this is the first message"""
        debug_logger.debug(f"_update_conversation_title_if_first_message called: conversation_id={conversation_id}, message_text='{message_text[:50]}...'")
        try:
            # Get the conversation
            query = select(ConversationModel).where(ConversationModel.id == conversation_id)
            result = await db.execute(query)
            conversation = result.scalar_one_or_none()

            if not conversation:
                Logger.warning(f"Conversation {conversation_id} not found for title update")
                return

            # Check if title is still the default generated title or empty
            # Only update if title is exactly a default pattern or starts with "Analysis - " followed by timestamp
            should_update = (
                not conversation.title or
                conversation.title == '' or
                conversation.title == 'New Conversation' or
                (conversation.title and conversation.title.startswith('Analysis - ') and
                 # Check if it's a timestamp-based title (contains date/time patterns)
                 any(char.isdigit() for char in conversation.title))
            )

            debug_logger.debug(f"Title update check: conversation.title='{conversation.title}', should_update={should_update}")

            if should_update:
                # Generate title from first question (truncate to 20-50 words)
                words = message_text.split()
                if len(words) <= 20:
                    new_title = message_text
                else:
                    new_title = ' '.join(words[:20]) + '...'

                # Update the conversation title
                conversation.title = new_title
                await db.commit()
                Logger.info(f"Updated conversation {conversation_id} title to: {new_title}")

        except Exception as e:
            Logger.error(f"Error updating conversation title: {str(e)}")
            # Don't raise the exception as this is not critical for the main flow