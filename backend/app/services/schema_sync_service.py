"""
Schema Synchronization Service

Syncs database schema to vector metadata tables for progressive retrieval.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from datetime import datetime
import hashlib

from app.models.vector_metadata import (
    VectorTableMetadata,
    VectorColumnMetadata,
    VectorRelationshipMetadata,
    VectorDocumentEnhanced
)
from app.models.vector_job import VectorRegenerationJob
from app.models.database import DatabaseConnection
from app.services.database_service import DatabaseService


class SchemaSyncService:
    """Service for synchronizing database schema to vector metadata"""

    @staticmethod
    async def sync_database_schema(
        db: AsyncSession,
        db_alias: str,
        schema_names: Optional[List[str]] = None,
        force_refresh: bool = False,
        job_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Sync database schema to vector metadata tables.
        Returns sync results.
        """
        results = {
            'tables_synced': 0,
            'columns_synced': 0,
            'relationships_synced': 0,
            'documents_created': 0,
            'errors': []
        }

        try:
            # Update job status
            if job_id:
                await SchemaSyncService._update_job_progress(db, job_id, 0.1, "Fetching schema information")

            # Fetch tables
            if job_id:
                await SchemaSyncService._update_job_progress(db, job_id, 0.2, "Syncing tables")

            tables = await SchemaSyncService._fetch_tables(db, db_alias, schema_names)

            for idx, table_info in enumerate(tables):
                try:
                    # Sync table metadata
                    table_metadata = await SchemaSyncService._sync_table(
                        db, db_alias, table_info, force_refresh
                    )
                    if table_metadata:
                        results['tables_synced'] += 1

                        # Sync columns
                        columns = await SchemaSyncService._sync_columns(
                            db, table_metadata, table_info, force_refresh
                        )
                        results['columns_synced'] += len(columns)

                        # Create vector documents for table
                        doc = await SchemaSyncService._create_table_document(
                            db, table_metadata
                        )
                        if doc:
                            results['documents_created'] += 1

                    # Update progress
                    if job_id:
                        progress = 0.2 + (0.6 * (idx + 1) / len(tables))
                        await SchemaSyncService._update_job_progress(
                            db, job_id, progress, f"Syncing table {idx + 1}/{len(tables)}"
                        )

                except Exception as e:
                    results['errors'].append({
                        'table': f"{table_info.get('schema_name')}.{table_info.get('table_name')}",
                        'error': str(e)
                    })

            # Discover relationships
            if job_id:
                await SchemaSyncService._update_job_progress(db, job_id, 0.8, "Discovering relationships")

            relationships = await SchemaSyncService._discover_relationships(db, db_alias)
            results['relationships_synced'] = len(relationships)

            # Complete
            if job_id:
                await SchemaSyncService._update_job_progress(db, job_id, 1.0, "Completed")

        except Exception as e:
            results['errors'].append({'error': f"Schema sync failed: {str(e)}"})

        return results

    @staticmethod
    async def _fetch_tables(
        db: AsyncSession,
        db_alias: str,
        schema_names: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Fetch table list from database"""
        # Get database connection
        query = select(DatabaseConnection).filter(DatabaseConnection.alias == db_alias)
        result = await db.execute(query)
        db_conn = result.scalar_one_or_none()

        if not db_conn:
            raise ValueError(f"Database connection not found: {db_alias}")

        # Get database service
        db_service = DatabaseService()

        # Get connection parameters
        connection_params = db_service._get_connection_params(db_conn)

        # Get connector for the database type
        from app.schemas.database import DatabaseType
        connector = db_service.connectors.get(DatabaseType(db_conn.type))
        if not connector:
            raise ValueError(f"Unsupported database type: {db_conn.type}")

        # Get schemas if not specified
        if not schema_names:
            schema_names = await connector.get_schemas(connection_params)

        # Fetch tables from all schemas
        all_tables = []
        for schema in schema_names:
            try:
                tables = await connector.get_tables(connection_params, schema)

                # Fetch columns for each table
                for table in tables:
                    try:
                        columns = await connector.get_columns(
                            connection_params, schema, table['name']
                        )
                        table['schema_name'] = schema
                        table['table_name'] = table['name']
                        table['columns'] = columns
                        all_tables.append(table)
                    except Exception as e:
                        # Log and continue
                        pass
            except Exception as e:
                # Log and continue
                pass

        return all_tables

    @staticmethod
    async def _sync_table(
        db: AsyncSession,
        db_alias: str,
        table_info: Dict[str, Any],
        force_refresh: bool = False
    ) -> Optional[VectorTableMetadata]:
        """Sync single table metadata"""
        schema_name = table_info.get('schema_name')
        table_name = table_info.get('table_name')

        # Check if exists
        query = select(VectorTableMetadata).filter(
            VectorTableMetadata.db_alias == db_alias,
            VectorTableMetadata.schema_name == schema_name,
            VectorTableMetadata.table_name == table_name
        )
        result = await db.execute(query)
        existing = result.scalar_one_or_none()

        if existing and not force_refresh:
            # Update last_schema_sync timestamp
            existing.last_schema_sync = datetime.utcnow()
            await db.commit()
            return existing

        # Create or update
        if existing:
            table_metadata = existing
        else:
            table_metadata = VectorTableMetadata(
                db_alias=db_alias,
                schema_name=schema_name,
                table_name=table_name
            )
            db.add(table_metadata)

        # Update metadata
        table_metadata.table_type = table_info.get('type', 'BASE TABLE')
        table_metadata.description = table_info.get('comment', table_info.get('description'))
        table_metadata.last_schema_sync = datetime.utcnow()

        # Update technical metadata
        technical_metadata = table_metadata.technical_metadata or {}
        technical_metadata.update({
            'row_count_estimate': table_info.get('row_count'),
            'size_mb': table_info.get('size_mb')
        })
        table_metadata.technical_metadata = technical_metadata

        await db.commit()
        await db.refresh(table_metadata)
        return table_metadata

    @staticmethod
    async def _sync_columns(
        db: AsyncSession,
        table_metadata: VectorTableMetadata,
        table_info: Dict[str, Any],
        force_refresh: bool = False
    ) -> List[VectorColumnMetadata]:
        """Sync columns for a table"""
        columns = []

        # Get column list from table info
        column_list = table_info.get('columns', [])

        for col_info in column_list:
            column_name = col_info.get('name', col_info.get('column_name'))

            # Check if exists
            query = select(VectorColumnMetadata).filter(
                VectorColumnMetadata.table_metadata_id == table_metadata.id,
                VectorColumnMetadata.column_name == column_name
            )
            result = await db.execute(query)
            existing = result.scalar_one_or_none()

            if existing and not force_refresh:
                columns.append(existing)
                continue

            if existing:
                column_metadata = existing
            else:
                column_metadata = VectorColumnMetadata(
                    table_metadata_id=table_metadata.id,
                    column_name=column_name
                )
                db.add(column_metadata)

            # Update metadata
            column_metadata.data_type = col_info.get('type', col_info.get('data_type'))
            column_metadata.is_nullable = col_info.get('nullable', col_info.get('is_nullable'))
            column_metadata.column_description = col_info.get('comment', col_info.get('description'))

            await db.commit()
            await db.refresh(column_metadata)
            columns.append(column_metadata)

        return columns

    @staticmethod
    async def _discover_relationships(
        db: AsyncSession,
        db_alias: str
    ) -> List[VectorRelationshipMetadata]:
        """Discover foreign key relationships"""
        relationships = []

        # Placeholder - would query foreign keys from database
        # TODO: Query information_schema.table_constraints and key_column_usage

        return relationships

    @staticmethod
    async def _create_table_document(
        db: AsyncSession,
        table_metadata: VectorTableMetadata
    ) -> Optional[VectorDocumentEnhanced]:
        """Create vector document for table"""
        # Generate content describing the table
        content = f"Table: {table_metadata.schema_name}.{table_metadata.table_name}\n"
        content += f"Type: {table_metadata.table_type}\n"

        if table_metadata.description:
            content += f"Description: {table_metadata.description}\n"

        # Generate hash
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        # Check if document exists
        query = select(VectorDocumentEnhanced).filter(
            VectorDocumentEnhanced.db_alias == table_metadata.db_alias,
            VectorDocumentEnhanced.document_type == 'table',
            VectorDocumentEnhanced.reference_id == table_metadata.id
        )
        result = await db.execute(query)
        existing = result.scalar_one_or_none()

        if existing and existing.content_hash == content_hash:
            return existing  # No changes

        if existing:
            existing.content = content
            existing.content_hash = content_hash
            existing.status = 'pending'
            await db.commit()
            await db.refresh(existing)
            return existing
        else:
            document = VectorDocumentEnhanced(
                db_alias=table_metadata.db_alias,
                document_type='table',
                reference_id=table_metadata.id,
                content=content,
                content_hash=content_hash,
                status='pending'
            )
            db.add(document)
            await db.commit()
            await db.refresh(document)
            return document

    @staticmethod
    async def _update_job_progress(
        db: AsyncSession,
        job_id: UUID,
        progress: float,
        current_step: str
    ):
        """Update job progress"""
        query = select(VectorRegenerationJob).filter(
            VectorRegenerationJob.id == job_id
        )
        result = await db.execute(query)
        job = result.scalar_one_or_none()

        if job:
            job.progress = progress
            job.current_step = current_step
            if progress > 0 and job.status == 'pending':
                job.status = 'running'
                job.started_at = datetime.utcnow()
            elif progress >= 1.0:
                job.status = 'completed'
                job.completed_at = datetime.utcnow()
            await db.commit()


class VectorJobService:
    """Service for managing vector regeneration jobs"""

    @staticmethod
    async def create_job(
        db: AsyncSession,
        job_type: str,
        db_alias: Optional[str] = None,
        target_type: Optional[str] = None,
        target_id: Optional[UUID] = None,
        parameters: Optional[Dict[str, Any]] = None,
        created_by: Optional[str] = None
    ) -> VectorRegenerationJob:
        """Create a new regeneration job"""
        job = VectorRegenerationJob(
            job_type=job_type,
            db_alias=db_alias,
            target_type=target_type,
            target_id=target_id,
            parameters=parameters or {},
            created_by=created_by
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        return job

    @staticmethod
    async def get_job(db: AsyncSession, job_id: UUID) -> Optional[VectorRegenerationJob]:
        """Get job by ID"""
        query = select(VectorRegenerationJob).filter(
            VectorRegenerationJob.id == job_id
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def list_jobs(
        db: AsyncSession,
        db_alias: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[VectorRegenerationJob]:
        """List jobs"""
        query = select(VectorRegenerationJob)

        if db_alias:
            query = query.filter(VectorRegenerationJob.db_alias == db_alias)
        if status:
            query = query.filter(VectorRegenerationJob.status == status)

        query = query.order_by(
            VectorRegenerationJob.created_at.desc()
        ).limit(limit)

        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def update_job_status(
        db: AsyncSession,
        job_id: UUID,
        status: str,
        error_message: Optional[str] = None,
        results: Optional[Dict[str, Any]] = None
    ) -> Optional[VectorRegenerationJob]:
        """Update job status"""
        query = select(VectorRegenerationJob).filter(
            VectorRegenerationJob.id == job_id
        )
        result = await db.execute(query)
        job = result.scalar_one_or_none()

        if not job:
            return None

        job.status = status
        if error_message:
            job.error_message = error_message
        if results:
            job.results = results

        if status == 'running' and not job.started_at:
            job.started_at = datetime.utcnow()
        elif status in ['completed', 'failed', 'cancelled']:
            job.completed_at = datetime.utcnow()

        await db.commit()
        await db.refresh(job)
        return job
