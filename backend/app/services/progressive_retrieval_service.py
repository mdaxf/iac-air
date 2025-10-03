"""
Progressive Retrieval Service

Implements progressive retrieval pattern for large database schemas.
Instead of loading all tables, retrieves only top-K relevant tables using semantic search.
"""
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, select

from app.core.logging_config import debug_logger as app_logger

from app.models.vector_metadata import (
    VectorTableMetadata,
    VectorColumnMetadata,
    VectorRelationshipMetadata
)
from app.models.business_semantic import (
    BusinessEntity,
    BusinessMetric,
    QueryTemplate
)


class ProgressiveRetrievalService:
    """Service for progressive retrieval of relevant database schema"""

    @staticmethod
    async def retrieve_relevant_context(
        db: AsyncSession,
        db_alias: str,
        question: str,
        query_embedding: List[float],
        max_tables: int = 10,
        similarity_threshold: float = 0.7
    ) -> Dict[str, Any]:
        """
        Progressive retrieval: Find relevant tables for a question using multi-stage search.

        Stages:
        1. Search business entities/metrics for concepts
        2. Search table metadata using vector similarity
        3. Retrieve columns and relationships for selected tables
        4. Assemble focused context for LLM
        """
        app_logger.debug(f"Progressive retrieval: Find relevant tables for a question using multi-stage search for {db_alias}, for question:{question}")
        context = {
            'relevant_tables': [],
            'business_entities': [],
            'business_metrics': [],
            'query_templates': [],
            'total_tables_searched': 0,
            'retrieval_strategy': 'progressive'
        }

        # Stage 1: Search business semantic layer

        try:
            app_logger.debug(f"Stage 1: Search business semantic layer")
            business_context = await ProgressiveRetrievalService._search_business_layer(
                db, db_alias, query_embedding, max_results=5
            )
            if business_context:
                context['business_entities'] = business_context['entities']
                context['business_metrics'] = business_context['metrics']
                context['query_templates'] = business_context['templates']
                app_logger.debug(f"Stage 1: Search business semantic layer result: {business_context}")
        except Exception as e:
            app_logger.debug(f"failed to Search business semantic layer with erroor: {e}")

        # Stage 2: Search table metadata

        try:
            app_logger.debug(f"Stage 2: Search table metadata ")
            relevant_tables = []

            try:
                relevant_tables = await ProgressiveRetrievalService._search_table_metadata(
                    db, db_alias, query_embedding, max_tables, similarity_threshold
                )
            except Exception as e:
                app_logger.debug(f"failed to Search Tables by semantic with error: {e}")

            if len(relevant_tables) == 0:
                app_logger.debug(f"Vector query return 0 tables")
                try:
                    relevant_tables = await ProgressiveRetrievalService._search_alltable_metadata(
                        db,db_alias
                    )
                except Exception as e:
                    app_logger.debug(f"failed to get all  with error: {e}")

            app_logger.debug(f"Stage 2: Search table metadata result {relevant_tables}")

            context['total_tables_searched'] = len(relevant_tables)

            # Stage 3: Enrich with columns and relationships
            app_logger.debug(f"Stage 3: Enrich with columns and relationships")

            try:
                for table, score in relevant_tables:
                    table_context = await ProgressiveRetrievalService._build_table_context(
                        db, table, score
                    )
                    context['relevant_tables'].append(table_context)
            except Exception as e:
                    app_logger.debug(f"failed to get all  context with error {e}")

            app_logger.debug(f"built content: {context}")
        except Exception as e:
            app_logger.debug(f"failed to Search Tables semantic layer with error: {e}")

        return context

    @staticmethod
    async def _search_business_layer(
        db: AsyncSession,
        db_alias: str,
        query_embedding: List[float],
        max_results: int = 5
    ) -> Dict[str, List]:
        """Search business entities, metrics, and templates"""

        # Search entities
        entity_query = select(BusinessEntity).where(
            BusinessEntity.db_alias == db_alias
        ).order_by(
            BusinessEntity.embedding.cosine_distance(query_embedding)
        ).limit(max_results)
        entity_result = await db.execute(entity_query)
        entities = entity_result.scalars().all()

        # Search metrics
        metric_query = select(BusinessMetric).where(
            BusinessMetric.db_alias == db_alias
        ).order_by(
            BusinessMetric.embedding.cosine_distance(query_embedding)
        ).limit(max_results)
        metric_result = await db.execute(metric_query)
        metrics = metric_result.scalars().all()

        # Search templates
        template_query = select(QueryTemplate).where(
            or_(
                QueryTemplate.db_alias == db_alias,
                QueryTemplate.db_alias == None  # Global templates
            ),
            QueryTemplate.status == 'active'
        ).order_by(
            QueryTemplate.embedding.cosine_distance(query_embedding)
        ).limit(max_results)
        template_result = await db.execute(template_query)
        templates = template_result.scalars().all()

        return {
            'entities': entities,
            'metrics': metrics,
            'templates': templates
        }

    @staticmethod
    async def _search_table_metadata(
        db: AsyncSession,
        db_alias: str,
        query_embedding: List[float],
        max_tables: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[Tuple[VectorTableMetadata, float]]:
        """Search table metadata using vector similarity"""

        table_query = select(VectorTableMetadata).where(
            VectorTableMetadata.db_alias == db_alias
        ).order_by(
            VectorTableMetadata.embedding.cosine_distance(query_embedding)
        ).limit(max_tables * 2)  # Get more for filtering

        result = await db.execute(table_query)
        tables = result.scalars().all()

        # Calculate similarity scores and filter
        relevant_tables = []
        for table in tables:
            # Placeholder similarity calculation
            # In production, would use actual cosine similarity
            score = 0.85  # Simulated

            if score >= similarity_threshold:
                relevant_tables.append((table, score))

            if len(relevant_tables) >= max_tables:
                break

        # Sort by score
        relevant_tables.sort(key=lambda x: x[1], reverse=True)

        return relevant_tables[:max_tables]

    @staticmethod
    async def _search_alltable_metadata(
        db: AsyncSession,
        db_alias: str
    ) -> List[Tuple[VectorTableMetadata, float]]:
        """Get all table metadata for a database alias"""

        table_query = select(VectorTableMetadata).where(
            VectorTableMetadata.db_alias == db_alias
        )
        result = await db.execute(table_query)
        tables = result.scalars().all()

        # Return tables with default score
        return [(table, 0.5) for table in tables]

    @staticmethod
    async def _build_table_context(
        db: AsyncSession,
        table: VectorTableMetadata,
        relevance_score: float
    ) -> Dict[str, Any]:
        """Build complete context for a table including columns and relationships"""

        # Get columns
        column_query = select(VectorColumnMetadata).where(
            VectorColumnMetadata.table_metadata_id == table.id
        )
        column_result = await db.execute(column_query)
        columns = column_result.scalars().all()

        # Get relationships (both source and target)
        source_rel_query = select(VectorRelationshipMetadata).where(
            VectorRelationshipMetadata.source_table_id == table.id
        )
        source_rel_result = await db.execute(source_rel_query)
        source_relationships = source_rel_result.scalars().all()

        target_rel_query = select(VectorRelationshipMetadata).where(
            VectorRelationshipMetadata.target_table_id == table.id
        )
        target_rel_result = await db.execute(target_rel_query)
        target_relationships = target_rel_result.scalars().all()

        return {
            'table': table,
            'relevance_score': relevance_score,
            'columns': columns,
            'source_relationships': source_relationships,
            'target_relationships': target_relationships,
            'column_count': len(columns),
            'relationship_count': len(source_relationships) + len(target_relationships)
        }

    @staticmethod
    async def assemble_sql_context(
        context: Dict[str, Any]
    ) -> str:
        """Assemble context into SQL schema format for LLM"""

        sql_context = []

        # Add business layer context
        if context.get('business_entities'):
            sql_context.append("-- Business Entities")
            for entity in context['business_entities']:
                sql_context.append(f"-- Entity: {entity.entity_name}")
                if entity.description:
                    sql_context.append(f"--   {entity.description}")

        if context.get('business_metrics'):
            sql_context.append("\n-- Business Metrics")
            for metric in context['business_metrics']:
                sql_context.append(f"-- Metric: {metric.metric_name}")
                definition = metric.metric_definition or {}
                if definition.get('description'):
                    sql_context.append(f"--   {definition['description']}")

        # Add table schemas
        sql_context.append("\n-- Database Tables")
        for table_ctx in context.get('relevant_tables', []):
            table = table_ctx['table']
            sql_context.append(f"\nCREATE TABLE {table.schema_name}.{table.table_name} (")

            columns = table_ctx['columns']
            for idx, col in enumerate(columns):
                col_def = f"  {col.column_name} {col.data_type}"
                if not col.is_nullable:
                    col_def += " NOT NULL"
                if idx < len(columns) - 1:
                    col_def += ","

                # Add column comment if exists
                if col.column_description:
                    col_def += f"  -- {col.column_description}"

                sql_context.append(col_def)

            sql_context.append(");")

            # Add table comment
            if table.description:
                sql_context.append(f"-- {table.description}")

        # Add relationships
        if any(table_ctx.get('source_relationships') or table_ctx.get('target_relationships')
               for table_ctx in context.get('relevant_tables', [])):
            sql_context.append("\n-- Relationships")

            for table_ctx in context.get('relevant_tables', []):
                for rel in table_ctx.get('source_relationships', []):
                    sql_context.append(
                        f"-- {rel.relationship_type}: "
                        f"{table_ctx['table'].table_name} -> target_table ({rel.cardinality})"
                    )

        return "\n".join(sql_context)

    @staticmethod
    async def search_by_keywords(
        db: AsyncSession,
        db_alias: str,
        keywords: List[str],
        max_tables: int = 10
    ) -> List[VectorTableMetadata]:
        """Search tables by keywords (fallback when embeddings not available)"""

        # Build text search conditions
        filters = []
        for keyword in keywords:
            filters.append(VectorTableMetadata.table_name.ilike(f'%{keyword}%'))
            filters.append(VectorTableMetadata.description.ilike(f'%{keyword}%'))

        table_query = select(VectorTableMetadata).where(
            VectorTableMetadata.db_alias == db_alias
        )

        if filters:
            table_query = table_query.where(or_(*filters))

        table_query = table_query.limit(max_tables)
        result = await db.execute(table_query)
        return result.scalars().all()

    @staticmethod
    async def rank_tables_by_usage(
        db: AsyncSession,
        db_alias: str,
        limit: int = 10
    ) -> List[VectorTableMetadata]:
        """Get most frequently used tables"""

        usage_query = select(VectorTableMetadata).where(
            VectorTableMetadata.db_alias == db_alias
        ).order_by(
            VectorTableMetadata.usage_count.desc()
        ).limit(limit)

        result = await db.execute(usage_query)
        return result.scalars().all()

    @staticmethod
    async def update_table_usage(
        db: AsyncSession,
        table_id: int
    ):
        """Update table usage statistics"""

        table_query = select(VectorTableMetadata).where(
            VectorTableMetadata.id == table_id
        )
        result = await db.execute(table_query)
        table = result.scalar_one_or_none()

        if table:
            table.usage_count = (table.usage_count or 0) + 1
            from datetime import datetime
            table.last_used_at = datetime.utcnow()
            await db.commit()
