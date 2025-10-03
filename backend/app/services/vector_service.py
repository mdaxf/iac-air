from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, func
from pgvector.sqlalchemy import Vector

from app.models.vector_document import VectorDocument
from app.schemas.vector_document import VectorDocumentCreate, VectorSearchRequest, VectorSearchResult, VectorDatabaseStats
from app.services.embedding_service import EmbeddingService


class VectorService:
    def __init__(self, embedding_service: EmbeddingService):
        self.embedding_service = embedding_service

    async def create_document(self, db: AsyncSession, document_data: VectorDocumentCreate) -> VectorDocument:
        # Generate embedding for the content
        embedding = await self.embedding_service.get_embedding(document_data.content)

        db_document = VectorDocument(
            resource_id=document_data.resource_id,
            resource_type=document_data.resource_type,
            db_alias=document_data.db_alias,
            title=document_data.title,
            content=document_data.content,
            embedding=embedding,
            metadata=document_data.metadata,
            tenant_id=document_data.tenant_id
        )

        db.add(db_document)
        await db.commit()
        await db.refresh(db_document)
        return db_document

    async def search_similar(
        self,
        db: AsyncSession,
        search_request: VectorSearchRequest
    ) -> List[VectorSearchResult]:
        # Generate embedding for the search query
        query_embedding = await self.embedding_service.get_embedding(search_request.query)

        # Build the SQL query with filters
        query_parts = [
            "SELECT *, embedding <-> %(query_embedding)s AS distance",
            "FROM vector_documents"
        ]

        where_conditions = []
        params = {"query_embedding": str(query_embedding)}

        if search_request.db_alias:
            where_conditions.append("db_alias = %(db_alias)s")
            params["db_alias"] = search_request.db_alias

        if search_request.resource_type:
            where_conditions.append("resource_type = %(resource_type)s")
            params["resource_type"] = search_request.resource_type

        if search_request.tenant_id:
            where_conditions.append("tenant_id = %(tenant_id)s")
            params["tenant_id"] = search_request.tenant_id

        if where_conditions:
            query_parts.append("WHERE " + " AND ".join(where_conditions))

        query_parts.extend([
            "ORDER BY embedding <-> %(query_embedding)s",
            f"LIMIT {search_request.top_k}"
        ])

        sql_query = " ".join(query_parts)

        result = await db.execute(text(sql_query), params)
        rows = result.fetchall()

        search_results = []
        for row in rows:
            document = VectorDocument(
                id=row.id,
                resource_id=row.resource_id,
                resource_type=row.resource_type,
                db_alias=row.db_alias,
                title=row.title,
                content=row.content,
                embedding=row.embedding,
                metadata=row.metadata,
                tenant_id=row.tenant_id,
                created_at=row.created_at,
                updated_at=row.updated_at
            )

            search_results.append(VectorSearchResult(
                document=document,
                score=1.0 - float(row.distance)  # Convert distance to similarity score
            ))

        return search_results

    async def get_document_by_resource_id(
        self,
        db: AsyncSession,
        resource_id: str,
        db_alias: Optional[str] = None
    ) -> Optional[VectorDocument]:
        query = select(VectorDocument).where(VectorDocument.resource_id == resource_id)

        if db_alias:
            query = query.where(VectorDocument.db_alias == db_alias)

        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def update_document(
        self,
        db: AsyncSession,
        document_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[VectorDocument]:
        query = select(VectorDocument).where(VectorDocument.id == document_id)
        result = await db.execute(query)
        document = result.scalar_one_or_none()

        if document:
            # Update content and regenerate embedding
            document.content = content
            document.embedding = await self.embedding_service.get_embedding(content)

            if metadata:
                document.metadata = metadata

            await db.commit()
            await db.refresh(document)

        return document

    async def delete_documents_by_db_alias(self, db: AsyncSession, db_alias: str) -> int:
        query = select(VectorDocument).where(VectorDocument.db_alias == db_alias)
        result = await db.execute(query)
        documents = result.scalars().all()

        count = len(documents)
        for document in documents:
            await db.delete(document)

        await db.commit()
        return count

    async def get_database_stats(self, db: AsyncSession, db_alias: str) -> VectorDatabaseStats:
        """Get statistics for vector documents and embeddings in a database"""
        from app.models.vector_job import VectorRegenerationJob
        from app.models.vector_metadata import VectorTableMetadata, VectorColumnMetadata
        from app.models.business_semantic import BusinessEntity, BusinessMetric, QueryTemplate

        # Get total count of uploaded documents
        total_query = select(func.count(VectorDocument.id)).where(VectorDocument.db_alias == db_alias)
        total_result = await db.execute(total_query)
        total_documents = total_result.scalar() or 0

        # Get count of metadata with embeddings
        table_count_query = select(func.count(VectorTableMetadata.id)).where(
            VectorTableMetadata.db_alias == db_alias,
            VectorTableMetadata.embedding.isnot(None)
        )
        table_count = (await db.execute(table_count_query)).scalar() or 0

        column_count_query = select(func.count(VectorColumnMetadata.id)).join(
            VectorTableMetadata, VectorColumnMetadata.table_metadata_id == VectorTableMetadata.id
        ).where(
            VectorTableMetadata.db_alias == db_alias,
            VectorColumnMetadata.embedding.isnot(None)
        )
        column_count = (await db.execute(column_count_query)).scalar() or 0

        entity_count_query = select(func.count(BusinessEntity.id)).where(
            BusinessEntity.db_alias == db_alias,
            BusinessEntity.embedding.isnot(None)
        )
        entity_count = (await db.execute(entity_count_query)).scalar() or 0

        metric_count_query = select(func.count(BusinessMetric.id)).where(
            BusinessMetric.db_alias == db_alias,
            BusinessMetric.embedding.isnot(None)
        )
        metric_count = (await db.execute(metric_count_query)).scalar() or 0

        template_count_query = select(func.count(QueryTemplate.id)).where(
            QueryTemplate.db_alias == db_alias,
            QueryTemplate.embedding.isnot(None)
        )
        template_count = (await db.execute(template_count_query)).scalar() or 0

        # Total embeddings = documents + metadata embeddings
        total_embeddings = total_documents + table_count + column_count + entity_count + metric_count + template_count

        # Get document types breakdown (for uploaded documents)
        type_query = select(
            VectorDocument.resource_type,
            func.count(VectorDocument.id)
        ).where(
            VectorDocument.db_alias == db_alias
        ).group_by(VectorDocument.resource_type)

        type_result = await db.execute(type_query)
        document_types = dict(type_result.fetchall())

        # Add metadata counts to document_types
        if table_count > 0:
            document_types['tables'] = table_count
        if column_count > 0:
            document_types['columns'] = column_count
        if entity_count > 0:
            document_types['entities'] = entity_count
        if metric_count > 0:
            document_types['metrics'] = metric_count
        if template_count > 0:
            document_types['templates'] = template_count

        # Get last completed embedding job time
        job_query = select(VectorRegenerationJob).where(
            VectorRegenerationJob.db_alias == db_alias,
            VectorRegenerationJob.job_type == 'regenerate_embeddings',
            VectorRegenerationJob.status == 'completed'
        ).order_by(VectorRegenerationJob.completed_at.desc()).limit(1)

        job_result = await db.execute(job_query)
        last_job = job_result.scalar_one_or_none()

        # Get last updated time from either job or documents
        last_updated = None
        if last_job and last_job.completed_at:
            last_updated = last_job.completed_at
        else:
            # Fallback to document update time
            last_updated_query = select(
                func.max(VectorDocument.updated_at)
            ).where(VectorDocument.db_alias == db_alias)
            last_updated_result = await db.execute(last_updated_query)
            last_updated = last_updated_result.scalar()

        return VectorDatabaseStats(
            db_alias=db_alias,
            total_documents=total_embeddings,  # Changed to include all embeddings
            embedding_model="text-embedding-ada-002",
            last_updated=last_updated,
            document_types=document_types
        )

    async def create_database_document(
        self,
        db: AsyncSession,
        db_alias: str,
        title: str,
        content: str,
        document_type: str = "database_doc",
        metadata: Optional[Dict[str, Any]] = None
    ) -> VectorDocument:
        """Create a database documentation document with vector embedding"""

        document_data = VectorDocumentCreate(
            resource_id=f"{db_alias}_{document_type}_{title}",
            resource_type=document_type,
            db_alias=db_alias,
            title=title,
            content=content,
            metadata=metadata or {}
        )

        return await self.create_document(db, document_data)