"""
Vector Generation Service - Generate vector embeddings for database schema
"""

import uuid
from typing import Dict, Any, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import BackgroundTasks

from app.core.logging_config import Logger, log_method_calls
from app.models.database import DatabaseConnection
from app.services.database_service import DatabaseService
from app.services.vector_service import VectorService
from app.services.embedding_service import EmbeddingService
from app.schemas.vector_document import VectorDocumentCreate


class VectorGenerationService:
    def __init__(self):
        self.database_service = DatabaseService()
        self.embedding_service = EmbeddingService()
        self.vector_service = VectorService(self.embedding_service)

    @log_method_calls
    async def generate_database_vectors(
        self,
        db: AsyncSession,
        db_connection: DatabaseConnection,
        background_tasks: BackgroundTasks
    ) -> str:
        """Generate vector documents for database schema"""
        job_id = str(uuid.uuid4())

        # Add background task
        background_tasks.add_task(
            self._generate_vectors_task,
            db,
            db_connection,
            job_id
        )

        return job_id

    async def _generate_vectors_task(
        self,
        db: AsyncSession,
        db_connection: DatabaseConnection,
        job_id: str
    ):
        """Background task to generate vector documents"""
        try:
            Logger.info(f"Starting vector generation for database {db_connection.alias} (job: {job_id})")

            # First, clean up existing vector documents for this database
            await self._cleanup_existing_vectors(db, db_connection.alias)

            # Introspect database schema
            schema_metadata = await self.database_service.introspect_database(db_connection)

            # Generate vector documents for tables and columns
            documents = []

            schemas = schema_metadata.get('schemas', {})
            for schema_name, schema_tables in schemas.items():
                for table_name, table_info in schema_tables.items():
                    full_table_name = f"{schema_name}.{table_name}"

                    # Generate table document
                    table_doc = await self._create_table_document(
                        db_connection.alias,
                        schema_name,
                        table_name,
                        table_info
                    )
                    documents.append(table_doc)

                    # Generate column documents
                    columns = table_info.get('columns', [])
                    for column in columns:
                        column_doc = await self._create_column_document(
                            db_connection.alias,
                            schema_name,
                            table_name,
                            column
                        )
                        documents.append(column_doc)

            # Create vector documents in batches
            batch_size = 10
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                await self._create_vector_documents_batch(db, batch)

            Logger.info(f"Completed vector generation for {db_connection.alias}: {len(documents)} documents created")

        except Exception as e:
            Logger.error(f"Vector generation failed for {db_connection.alias}: {str(e)}")

    async def _cleanup_existing_vectors(self, db: AsyncSession, database_alias: str):
        """Clean up existing vector documents for this database"""
        try:
            # Use vector service to delete documents by database
            from app.api.v1.endpoints.vector import delete_documents_by_database
            await delete_documents_by_database(database_alias, db)
            Logger.info(f"Cleaned up existing vectors for database: {database_alias}")
        except Exception as e:
            Logger.warning(f"Failed to cleanup existing vectors: {str(e)}")

    async def _create_table_document(
        self,
        database_alias: str,
        schema_name: str,
        table_name: str,
        table_info: Dict[str, Any]
    ) -> VectorDocumentCreate:
        """Create a vector document for a table"""
        full_table_name = f"{schema_name}.{table_name}"
        table_meta = table_info.get('metadata', {})

        # Build comprehensive content for the table
        content_parts = []
        content_parts.append(f"Table: {full_table_name}")

        if table_meta.get('comment'):
            content_parts.append(f"Description: {table_meta['comment']}")

        content_parts.append(f"Type: {table_meta.get('type', 'TABLE')}")

        # Add column information summary
        columns = table_info.get('columns', [])
        if columns:
            content_parts.append(f"Columns ({len(columns)}):")
            for col in columns[:20]:  # Limit to first 20 columns
                col_desc = f"  {col['name']} ({col['data_type']})"
                if not col.get('is_nullable', True):
                    col_desc += " NOT NULL"
                if col.get('comment'):
                    col_desc += f" - {col['comment']}"
                content_parts.append(col_desc)

        # Add sample data summary if available
        sample_data = table_info.get('sample_data', [])
        if sample_data:
            content_parts.append(f"Sample data ({len(sample_data)} rows available)")

        content = "\n".join(content_parts)

        return VectorDocumentCreate(
            resource_id=f"{database_alias}::{schema_name}::{table_name}",
            resource_type="table_doc",
            content=content,
            db_alias=database_alias,
            metadata={
                'database': database_alias,
                'schema': schema_name,
                'table': table_name,
                'table_type': table_meta.get('type', 'TABLE'),
                'column_count': len(columns),
                'has_sample_data': bool(sample_data)
            }
        )

    async def _create_column_document(
        self,
        database_alias: str,
        schema_name: str,
        table_name: str,
        column: Dict[str, Any]
    ) -> VectorDocumentCreate:
        """Create a vector document for a column"""
        column_name = column['name']
        full_column_name = f"{schema_name}.{table_name}.{column_name}"

        # Build content for the column
        content_parts = []
        content_parts.append(f"Column: {full_column_name}")
        content_parts.append(f"Data Type: {column['data_type']}")

        if not column.get('is_nullable', True):
            content_parts.append("NOT NULL")

        if column.get('comment'):
            content_parts.append(f"Description: {column['comment']}")

        if column.get('default_value'):
            content_parts.append(f"Default: {column['default_value']}")

        content = "\n".join(content_parts)

        return VectorDocumentCreate(
            resource_id=f"{database_alias}::{schema_name}::{table_name}::{column_name}",
            resource_type="column_doc",
            content=content,
            db_alias=database_alias,
            metadata={
                'database': database_alias,
                'schema': schema_name,
                'table': table_name,
                'column': column_name,
                'data_type': column['data_type'],
                'is_nullable': column.get('is_nullable', True),
                'has_comment': bool(column.get('comment'))
            }
        )

    async def _create_vector_documents_batch(
        self,
        db: AsyncSession,
        documents: List[VectorDocumentCreate]
    ):
        """Create a batch of vector documents"""
        try:
            for doc in documents:
                await self.vector_service.create_document(db, doc)
        except Exception as e:
            Logger.error(f"Failed to create vector document batch: {str(e)}")
            raise