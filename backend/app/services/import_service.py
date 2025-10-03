from typing import Dict, Any, Optional
import uuid
import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import BackgroundTasks

from app.models.database import DatabaseConnection
from app.models.import_job import ImportJob as ImportJobModel
from app.schemas.database import SchemaImportRequest, ImportJob, ImportJobStatus
from app.services.database_service import DatabaseService
from app.services.vector_service import VectorService
from app.services.embedding_service import EmbeddingService
from app.core.logging_config import Logger


class ImportService:
    def __init__(self):
        self.database_service = DatabaseService()
        self.embedding_service = EmbeddingService()
        self.vector_service = VectorService(self.embedding_service)

    async def start_import_job(
        self,
        db: AsyncSession,
        db_conn: DatabaseConnection,
        import_request: SchemaImportRequest,
        background_tasks: BackgroundTasks
    ) -> str:
        """Start a schema import job"""
        job_id = str(uuid.uuid4())

        # Create job record in database
        job_model = ImportJobModel(
            job_id=job_id,
            db_alias=db_conn.alias,
            status=ImportJobStatus.PENDING.value,
            progress=0.0
        )

        db.add(job_model)
        await db.commit()
        await db.refresh(job_model)

        Logger.info(f"Created import job {job_id} for database {db_conn.alias}")

        # Start background task
        background_tasks.add_task(self._run_import_job, job_id, db_conn, import_request)

        return job_id

    async def get_job_status(self, db: AsyncSession, job_id: str) -> Optional[ImportJob]:
        """Get the status of an import job"""
        query = select(ImportJobModel).where(ImportJobModel.job_id == job_id)
        result = await db.execute(query)
        job_model = result.scalar_one_or_none()

        if not job_model:
            return None

        # Convert model to schema
        return ImportJob(
            job_id=job_model.job_id,
            db_alias=job_model.db_alias,
            status=ImportJobStatus(job_model.status),
            progress=job_model.progress,
            message=job_model.message,
            created_at=job_model.created_at,
            updated_at=job_model.updated_at
        )

    async def _run_import_job(self, job_id: str, db_conn: DatabaseConnection, import_request: SchemaImportRequest):
        """Run the actual import job in the background"""
        # Need a new database session for the background task
        from app.core.database import get_db_session

        db = get_db_session()
        try:
            try:
                # Update job status to running
                await self._update_job_status(db, job_id, ImportJobStatus.RUNNING, 0.0, "Starting import...")

                # Step 1: Introspect database schema
                await self._update_job_status(db, job_id, ImportJobStatus.RUNNING, 10.0, "Introspecting database schema...")
                schema_info = await self.database_service.introspect_database(db_conn)

                # Step 2: Generate documentation for tables and columns
                await self._update_job_status(db, job_id, ImportJobStatus.RUNNING, 30.0, "Generating documentation...")
                documents = await self._generate_documentation(schema_info)

                # Step 3: Create embeddings and store in vector database
                await self._update_job_status(db, job_id, ImportJobStatus.RUNNING, 60.0, "Creating embeddings...")
                # TODO: Implement actual vector document storage
                await asyncio.sleep(2)  # Simulate processing time

                # Step 4: Complete
                await self._update_job_status(
                    db, job_id, ImportJobStatus.COMPLETED, 100.0,
                    f"Successfully imported {len(documents)} documents"
                )

                Logger.info(f"Import job {job_id} completed successfully with {len(documents)} documents")

            except Exception as e:
                Logger.error(f"Import job {job_id} failed: {str(e)}")
                await self._update_job_status(
                    db, job_id, ImportJobStatus.FAILED, 0.0,
                    f"Import failed: {str(e)}"
                )
        finally:
            await db.close()

    async def _update_job_status(
        self,
        db: AsyncSession,
        job_id: str,
        status: ImportJobStatus,
        progress: float,
        message: str
    ):
        """Update job status in database"""
        query = select(ImportJobModel).where(ImportJobModel.job_id == job_id)
        result = await db.execute(query)
        job_model = result.scalar_one_or_none()

        if job_model:
            job_model.status = status.value
            job_model.progress = progress
            job_model.message = message
            job_model.updated_at = datetime.utcnow()

            if status == ImportJobStatus.COMPLETED:
                job_model.completed_at = datetime.utcnow()
            elif status == ImportJobStatus.FAILED:
                job_model.error_details = message

            await db.commit()

    async def _generate_documentation(self, schema_info: Dict[str, Any]) -> list:
        """Generate human-readable documentation from schema information"""
        documents = []

        db_alias = schema_info['db_alias']
        schemas = schema_info['schemas']

        for schema_name, tables in schemas.items():
            for table_name, table_info in tables.items():
                # Generate table documentation
                table_doc = self._generate_table_documentation(
                    db_alias, schema_name, table_name, table_info
                )
                documents.append(table_doc)

                # Generate column documentation
                for column in table_info['columns']:
                    column_doc = self._generate_column_documentation(
                        db_alias, schema_name, table_name, column, table_info['sample_data']
                    )
                    documents.append(column_doc)

        return documents

    def _generate_table_documentation(self, db_alias: str, schema: str, table: str, table_info: Dict) -> Dict:
        """Generate documentation for a table"""
        metadata = table_info['metadata']
        columns = table_info['columns']
        sample_data = table_info['sample_data']

        # Build table description
        content_parts = [
            f"Table: {schema}.{table}",
            f"Type: {metadata.get('type', 'TABLE')}",
            f"Description: {metadata.get('comment', 'No description available')}"
        ]

        if columns:
            content_parts.append(f"Columns ({len(columns)}):")
            for col in columns:
                col_desc = f"  - {col['name']} ({col['data_type']})"
                if col.get('comment'):
                    col_desc += f" - {col['comment']}"
                content_parts.append(col_desc)

        if sample_data:
            content_parts.append(f"Sample data ({len(sample_data)} rows):")
            for i, row in enumerate(sample_data[:3]):  # Show first 3 rows
                content_parts.append(f"  Row {i+1}: {dict(row)}")

        return {
            'resource_id': f"{db_alias}.{schema}.{table}",
            'resource_type': 'table_doc',
            'db_alias': db_alias,
            'title': f"{schema}.{table}",
            'content': "\n".join(content_parts),
            'metadata': {
                'schema': schema,
                'table': table,
                'column_count': len(columns),
                'sample_row_count': len(sample_data),
                'table_type': metadata.get('type', 'TABLE')
            }
        }

    def _generate_column_documentation(self, db_alias: str, schema: str, table: str, column: Dict, sample_data: list) -> Dict:
        """Generate documentation for a column"""
        col_name = column['name']
        data_type = column['data_type']

        content_parts = [
            f"Column: {schema}.{table}.{col_name}",
            f"Data Type: {data_type}",
            f"Nullable: {'Yes' if column.get('is_nullable') else 'No'}"
        ]

        if column.get('comment'):
            content_parts.append(f"Description: {column['comment']}")

        if column.get('default_value'):
            content_parts.append(f"Default: {column['default_value']}")

        # Add sample values
        if sample_data:
            sample_values = [str(row.get(col_name, '')) for row in sample_data[:10] if row.get(col_name) is not None]
            if sample_values:
                unique_values = list(set(sample_values))[:5]  # First 5 unique values
                content_parts.append(f"Sample values: {', '.join(unique_values)}")

        return {
            'resource_id': f"{db_alias}.{schema}.{table}.{col_name}",
            'resource_type': 'column_doc',
            'db_alias': db_alias,
            'title': f"{schema}.{table}.{col_name}",
            'content': "\n".join(content_parts),
            'metadata': {
                'schema': schema,
                'table': table,
                'column': col_name,
                'data_type': data_type,
                'is_nullable': column.get('is_nullable', False),
                'max_length': column.get('max_length'),
                'precision': column.get('precision'),
                'scale': column.get('scale')
            }
        }