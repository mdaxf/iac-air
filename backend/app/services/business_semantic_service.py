"""
Business Semantic Layer Service

Handles CRUD operations and business logic for business entities, metrics,
concept mappings, and query templates.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, func
from pgvector.sqlalchemy import Vector
import json

from app.models.business_semantic import (
    BusinessEntity,
    BusinessMetric,
    ConceptMapping,
    QueryTemplate
)
from app.schemas.business_semantic import (
    BusinessEntityCreate,
    BusinessEntityUpdate,
    BusinessMetricCreate,
    BusinessMetricUpdate,
    ConceptMappingCreate,
    ConceptMappingUpdate,
    QueryTemplateCreate,
    QueryTemplateUpdate,
    BusinessEntitySearch,
    BusinessMetricSearch,
    ConceptMappingSearch,
    QueryTemplateSearch
)


# ============================================================================
# Business Entity Operations
# ============================================================================

class BusinessEntityService:
    """Service for managing business entities"""

    @staticmethod
    async def create_entity(
        db: AsyncSession,
        entity: BusinessEntityCreate,
        embedding: Optional[List[float]] = None
    ) -> BusinessEntity:
        """Create a new business entity"""
        db_entity = BusinessEntity(
            db_alias=entity.db_alias,
            entity_name=entity.entity_name,
            entity_type=entity.entity_type,
            description=entity.description,
            business_owner=entity.business_owner,
            attributes=entity.attributes,
            source_mapping=entity.source_mapping,
            metrics=entity.metrics,
            embedding=embedding,
            created_by=entity.created_by
        )
        db.add(db_entity)
        await db.commit()
        await db.refresh(db_entity)
        return db_entity

    @staticmethod
    async def get_entity(db: AsyncSession, entity_id: UUID) -> Optional[BusinessEntity]:
        """Get a business entity by ID"""
        query = select(BusinessEntity).where(BusinessEntity.id == entity_id)
        result = await db.execute(query)
        return result.scalars().first()

    @staticmethod
    async def get_entity_by_name(
        db: AsyncSession,
        db_alias: str,
        entity_name: str
    ) -> Optional[BusinessEntity]:
        """Get a business entity by database alias and name"""
        query = select(BusinessEntity).where(
            and_(
                BusinessEntity.db_alias == db_alias,
                BusinessEntity.entity_name == entity_name
            )
        )
        result = await db.execute(query)
        return result.scalars().first()

    @staticmethod
    async def list_entities(
        db: AsyncSession,
        db_alias: Optional[str] = None,
        entity_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[BusinessEntity]:
        """List business entities with optional filters"""
        query = select(BusinessEntity)

        if db_alias:
            query = query.where(BusinessEntity.db_alias == db_alias)
        if entity_type:
            query = query.where(BusinessEntity.entity_type == entity_type)

        query = query.order_by(BusinessEntity.entity_name).limit(limit).offset(offset)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def search_entities(
        db: AsyncSession,
        search: BusinessEntitySearch
    ) -> List[BusinessEntity]:
        """Search business entities using filters and semantic search"""
        query = select(BusinessEntity)

        # Apply filters
        if search.db_alias:
            query = query.where(BusinessEntity.db_alias == search.db_alias)
        if search.entity_type:
            query = query.where(BusinessEntity.entity_type == search.entity_type)
        if search.business_domain:
            query = query.where(
                BusinessEntity.attributes['business_domain'].astext == search.business_domain
            )

        # Text search on name and description
        if search.query:
            query = query.where(
                or_(
                    BusinessEntity.entity_name.ilike(f'%{search.query}%'),
                    BusinessEntity.description.ilike(f'%{search.query}%')
                )
            )

        query = query.order_by(BusinessEntity.entity_name).limit(search.limit).offset(search.offset)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def search_entities_by_embedding(
        db: AsyncSession,
        db_alias: str,
        query_embedding: List[float],
        limit: int = 10
    ) -> List[BusinessEntity]:
        """Search business entities using vector similarity"""
        query = select(BusinessEntity).where(
            BusinessEntity.db_alias == db_alias
        ).order_by(
            BusinessEntity.embedding.cosine_distance(query_embedding)
        ).limit(limit)

        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def update_entity(
        db: AsyncSession,
        entity_id: UUID,
        entity_update: BusinessEntityUpdate
    ) -> Optional[BusinessEntity]:
        """Update a business entity"""
        query = select(BusinessEntity).where(BusinessEntity.id == entity_id)
        result = await db.execute(query)
        db_entity = result.scalars().first()
        if not db_entity:
            return None

        update_data = entity_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_entity, field, value)

        await db.commit()
        await db.refresh(db_entity)
        return db_entity

    @staticmethod
    async def update_entity_embedding(
        db: AsyncSession,
        entity_id: UUID,
        embedding: List[float]
    ) -> Optional[BusinessEntity]:
        """Update entity embedding"""
        query = select(BusinessEntity).where(BusinessEntity.id == entity_id)
        result = await db.execute(query)
        db_entity = result.scalars().first()
        if not db_entity:
            return None

        db_entity.embedding = embedding
        await db.commit()
        await db.refresh(db_entity)
        return db_entity

    @staticmethod
    async def delete_entity(db: AsyncSession, entity_id: UUID) -> bool:
        """Delete a business entity"""
        query = select(BusinessEntity).where(BusinessEntity.id == entity_id)
        result = await db.execute(query)
        db_entity = result.scalars().first()
        if not db_entity:
            return False

        db.delete(db_entity)
        await db.commit()
        return True

    @staticmethod
    async def resolve_entity_to_tables(
        db: AsyncSession,
        entity_id: UUID
    ) -> Dict[str, Any]:
        """Resolve entity to underlying database tables"""
        query = select(BusinessEntity).where(BusinessEntity.id == entity_id)
        result = await db.execute(query)
        db_entity = result.scalars().first()
        if not db_entity:
            return {}

        source_mapping = db_entity.source_mapping or {}

        return {
            'primary_table': source_mapping.get('primary_table'),
            'related_tables': source_mapping.get('related_tables', []),
            'denormalized_view': source_mapping.get('denormalized_view'),
            'key_columns': source_mapping.get('key_columns', [])
        }


# ============================================================================
# Business Metric Operations
# ============================================================================

class BusinessMetricService:
    """Service for managing business metrics"""

    @staticmethod
    async def create_metric(
        db: AsyncSession,
        metric: BusinessMetricCreate,
        embedding: Optional[List[float]] = None
    ) -> BusinessMetric:
        """Create a new business metric"""
        db_metric = BusinessMetric(
            db_alias=metric.db_alias,
            metric_name=metric.metric_name,
            entity_id=metric.entity_id,
            metric_definition=metric.metric_definition,
            embedding=embedding,
            created_by=metric.created_by
        )
        db.add(db_metric)
        await db.commit()
        await db.refresh(db_metric)
        return db_metric

    @staticmethod
    async def get_metric(db: AsyncSession, metric_id: UUID) -> Optional[BusinessMetric]:
        """Get a business metric by ID"""
        query = select(BusinessMetric).where(BusinessMetric.id == metric_id)
        result = await db.execute(query)
        return result.scalars().first()

    @staticmethod
    async def get_metric_by_name(
        db: AsyncSession,
        db_alias: str,
        metric_name: str
    ) -> Optional[BusinessMetric]:
        """Get a business metric by database alias and name"""
        query = select(BusinessMetric).where(
            and_(
                BusinessMetric.db_alias == db_alias,
                BusinessMetric.metric_name == metric_name
            )
        )
        result = await db.execute(query)
        return result.scalars().first()

    @staticmethod
    async def list_metrics(
        db: AsyncSession,
        db_alias: Optional[str] = None,
        entity_id: Optional[UUID] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[BusinessMetric]:
        """List business metrics with optional filters"""
        query = select(BusinessMetric)

        if db_alias:
            query = query.where(BusinessMetric.db_alias == db_alias)
        if entity_id:
            query = query.where(BusinessMetric.entity_id == entity_id)

        query = query.order_by(BusinessMetric.metric_name).limit(limit).offset(offset)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def search_metrics(
        db: AsyncSession,
        search: BusinessMetricSearch
    ) -> List[BusinessMetric]:
        """Search business metrics using filters"""
        query = select(BusinessMetric)

        # Apply filters
        if search.db_alias:
            query = query.where(BusinessMetric.db_alias == search.db_alias)
        if search.entity_id:
            query = query.where(BusinessMetric.entity_id == search.entity_id)

        # Text search on name
        if search.query:
            query = query.where(
                or_(
                    BusinessMetric.metric_name.ilike(f'%{search.query}%'),
                    BusinessMetric.metric_definition['description'].astext.ilike(f'%{search.query}%')
                )
            )

        query = query.order_by(BusinessMetric.metric_name).limit(search.limit).offset(search.offset)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def search_metrics_by_embedding(
        db: AsyncSession,
        db_alias: str,
        query_embedding: List[float],
        limit: int = 10
    ) -> List[BusinessMetric]:
        """Search business metrics using vector similarity"""
        query = select(BusinessMetric).where(
            BusinessMetric.db_alias == db_alias
        ).order_by(
            BusinessMetric.embedding.cosine_distance(query_embedding)
        ).limit(limit)

        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def update_metric(
        db: AsyncSession,
        metric_id: UUID,
        metric_update: BusinessMetricUpdate
    ) -> Optional[BusinessMetric]:
        """Update a business metric"""
        query = select(BusinessMetric).where(BusinessMetric.id == metric_id)
        result = await db.execute(query)
        db_metric = result.scalars().first()
        if not db_metric:
            return None

        update_data = metric_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_metric, field, value)

        await db.commit()
        await db.refresh(db_metric)
        return db_metric

    @staticmethod
    async def update_metric_embedding(
        db: AsyncSession,
        metric_id: UUID,
        embedding: List[float]
    ) -> Optional[BusinessMetric]:
        """Update metric embedding"""
        query = select(BusinessMetric).where(BusinessMetric.id == metric_id)
        result = await db.execute(query)
        db_metric = result.scalars().first()
        if not db_metric:
            return None

        db_metric.embedding = embedding
        await db.commit()
        await db.refresh(db_metric)
        return db_metric

    @staticmethod
    async def update_metric_usage(
        db: AsyncSession,
        metric_id: UUID,
        success: bool,
        execution_time_ms: float,
        user: Optional[str] = None
    ) -> Optional[BusinessMetric]:
        """Update metric usage statistics"""
        query = select(BusinessMetric).where(BusinessMetric.id == metric_id)
        result = await db.execute(query)
        db_metric = result.scalars().first()
        if not db_metric:
            return None

        db_metric.usage_count += 1
        if success:
            db_metric.success_count += 1
        else:
            db_metric.failure_count += 1

        # Update average execution time
        if db_metric.avg_execution_time_ms is None:
            db_metric.avg_execution_time_ms = execution_time_ms
        else:
            # Running average
            db_metric.avg_execution_time_ms = (
                (db_metric.avg_execution_time_ms * (db_metric.usage_count - 1) + execution_time_ms)
                / db_metric.usage_count
            )

        db_metric.last_used_at = func.now()
        if user:
            db_metric.last_used_by = user

        await db.commit()
        await db.refresh(db_metric)
        return db_metric

    @staticmethod
    async def delete_metric(db: AsyncSession, metric_id: UUID) -> bool:
        """Delete a business metric"""
        query = select(BusinessMetric).where(BusinessMetric.id == metric_id)
        result = await db.execute(query)
        db_metric = result.scalars().first()
        if not db_metric:
            return False

        db.delete(db_metric)
        await db.commit()
        return True

    @staticmethod
    async def resolve_metric_to_sql(
        db: AsyncSession,
        metric_id: UUID,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Resolve metric to SQL query by replacing parameters"""
        query = select(BusinessMetric).where(BusinessMetric.id == metric_id)
        result = await db.execute(query)
        db_metric = result.scalars().first()
        if not db_metric:
            return None

        metric_def = db_metric.metric_definition or {}
        sql_template = metric_def.get('sql_template', '')

        if not sql_template:
            return None

        # Replace parameters in template
        if parameters:
            for key, value in parameters.items():
                placeholder = '{' + key + '}'
                sql_template = sql_template.replace(placeholder, str(value))

        return sql_template


# ============================================================================
# Concept Mapping Operations
# ============================================================================

class ConceptMappingService:
    """Service for managing concept mappings"""

    @staticmethod
    async def create_mapping(
        db: AsyncSession,
        mapping: ConceptMappingCreate
    ) -> ConceptMapping:
        """Create a new concept mapping"""
        db_mapping = ConceptMapping(
            db_alias=mapping.db_alias,
            canonical_term=mapping.canonical_term,
            synonyms=mapping.synonyms,
            entity_id=mapping.entity_id,
            metric_id=mapping.metric_id,
            template_id=mapping.template_id,
            context=mapping.context,
            category=mapping.category,
            created_by=mapping.created_by
        )
        db.add(db_mapping)
        await db.commit()
        await db.refresh(db_mapping)
        return db_mapping

    @staticmethod
    async def get_mapping(db: AsyncSession, mapping_id: UUID) -> Optional[ConceptMapping]:
        """Get a concept mapping by ID"""
        query = select(ConceptMapping).where(ConceptMapping.id == mapping_id)
        result = await db.execute(query)
        return result.scalars().first()

    @staticmethod
    async def get_mapping_by_term(
        db: AsyncSession,
        db_alias: str,
        term: str
    ) -> Optional[ConceptMapping]:
        """Find concept mapping by canonical term or synonym"""
        # First check canonical term
        query = select(ConceptMapping).where(
            and_(
                ConceptMapping.db_alias == db_alias,
                ConceptMapping.canonical_term == term
            )
        )
        result = await db.execute(query)
        mapping = result.scalars().first()

        if mapping:
            return mapping

        # Then check synonyms array
        query = select(ConceptMapping).where(
            and_(
                ConceptMapping.db_alias == db_alias,
                ConceptMapping.synonyms.contains([term])
            )
        )
        result = await db.execute(query)
        return result.scalars().first()

    @staticmethod
    async def list_mappings(
        db: AsyncSession,
        db_alias: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[ConceptMapping]:
        """List concept mappings with optional filters"""
        query = select(ConceptMapping)

        if db_alias:
            query = query.where(ConceptMapping.db_alias == db_alias)
        if category:
            query = query.where(ConceptMapping.category == category)

        query = query.order_by(ConceptMapping.canonical_term).limit(limit).offset(offset)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def search_mappings(
        db: AsyncSession,
        search: ConceptMappingSearch
    ) -> List[ConceptMapping]:
        """Search concept mappings"""
        query = select(ConceptMapping)

        # Apply filters
        if search.db_alias:
            query = query.where(ConceptMapping.db_alias == search.db_alias)
        if search.category:
            query = query.where(ConceptMapping.category == search.category)

        # Text search on canonical term and synonyms
        if search.query:
            query = query.where(
                or_(
                    ConceptMapping.canonical_term.ilike(f'%{search.query}%'),
                    ConceptMapping.synonyms.contains([search.query])
                )
            )

        query = query.order_by(ConceptMapping.canonical_term).limit(search.limit).offset(search.offset)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def update_mapping(
        db: AsyncSession,
        mapping_id: UUID,
        mapping_update: ConceptMappingUpdate
    ) -> Optional[ConceptMapping]:
        """Update a concept mapping"""
        query = select(ConceptMapping).where(ConceptMapping.id == mapping_id)
        result = await db.execute(query)
        db_mapping = result.scalars().first()
        if not db_mapping:
            return None

        update_data = mapping_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_mapping, field, value)

        await db.commit()
        await db.refresh(db_mapping)
        return db_mapping

    @staticmethod
    async def delete_mapping(db: AsyncSession, mapping_id: UUID) -> bool:
        """Delete a concept mapping"""
        query = select(ConceptMapping).where(ConceptMapping.id == mapping_id)
        result = await db.execute(query)
        db_mapping = result.scalars().first()
        if not db_mapping:
            return False

        db.delete(db_mapping)
        await db.commit()
        return True


# ============================================================================
# Query Template Operations
# ============================================================================

class QueryTemplateService:
    """Service for managing query templates"""

    @staticmethod
    async def create_template(
        db: AsyncSession,
        template: QueryTemplateCreate,
        embedding: Optional[List[float]] = None
    ) -> QueryTemplate:
        """Create a new query template"""
        db_template = QueryTemplate(
            db_alias=template.db_alias,
            template_name=template.template_name,
            description=template.description,
            category=template.category,
            example_questions=template.example_questions,
            sql_template=template.sql_template,
            parameters=template.parameters,
            required_entities=template.required_entities,
            required_metrics=template.required_metrics,
            status=template.status,
            embedding=embedding,
            created_by=template.created_by
        )
        db.add(db_template)
        await db.commit()
        await db.refresh(db_template)
        return db_template

    @staticmethod
    async def get_template(db: AsyncSession, template_id: UUID) -> Optional[QueryTemplate]:
        """Get a query template by ID"""
        query = select(QueryTemplate).where(QueryTemplate.id == template_id)
        result = await db.execute(query)
        return result.scalars().first()

    @staticmethod
    async def get_template_by_name(
        db: AsyncSession,
        template_name: str,
        db_alias: Optional[str] = None
    ) -> Optional[QueryTemplate]:
        """Get a query template by name"""
        query = select(QueryTemplate).where(QueryTemplate.template_name == template_name)
        if db_alias:
            query = query.where(QueryTemplate.db_alias == db_alias)
        result = await db.execute(query)
        return result.scalars().first()

    @staticmethod
    async def list_templates(
        db: AsyncSession,
        db_alias: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[QueryTemplate]:
        """List query templates with optional filters"""
        query = select(QueryTemplate)

        if db_alias:
            query = query.where(QueryTemplate.db_alias == db_alias)
        if category:
            query = query.where(QueryTemplate.category == category)
        if status:
            query = query.where(QueryTemplate.status == status)

        query = query.order_by(QueryTemplate.template_name).limit(limit).offset(offset)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def search_templates(
        db: AsyncSession,
        search: QueryTemplateSearch
    ) -> List[QueryTemplate]:
        """Search query templates"""
        query = select(QueryTemplate)

        # Apply filters
        if search.db_alias:
            query = query.where(QueryTemplate.db_alias == search.db_alias)
        if search.category:
            query = query.where(QueryTemplate.category == search.category)
        if search.status:
            query = query.where(QueryTemplate.status == search.status)

        # Text search on name and description
        if search.query:
            query = query.where(
                or_(
                    QueryTemplate.template_name.ilike(f'%{search.query}%'),
                    QueryTemplate.description.ilike(f'%{search.query}%')
                )
            )

        query = query.order_by(QueryTemplate.template_name).limit(search.limit).offset(search.offset)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def search_templates_by_embedding(
        db: AsyncSession,
        query_embedding: List[float],
        db_alias: Optional[str] = None,
        limit: int = 10
    ) -> List[QueryTemplate]:
        """Search query templates using vector similarity"""
        query = select(QueryTemplate).where(QueryTemplate.status == 'active')

        if db_alias:
            query = query.where(QueryTemplate.db_alias == db_alias)

        query = query.order_by(
            QueryTemplate.embedding.cosine_distance(query_embedding)
        ).limit(limit)

        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def update_template(
        db: AsyncSession,
        template_id: UUID,
        template_update: QueryTemplateUpdate
    ) -> Optional[QueryTemplate]:
        """Update a query template"""
        query = select(QueryTemplate).where(QueryTemplate.id == template_id)
        result = await db.execute(query)
        db_template = result.scalars().first()
        if not db_template:
            return None

        update_data = template_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_template, field, value)

        await db.commit()
        await db.refresh(db_template)
        return db_template

    @staticmethod
    async def update_template_embedding(
        db: AsyncSession,
        template_id: UUID,
        embedding: List[float]
    ) -> Optional[QueryTemplate]:
        """Update template embedding"""
        query = select(QueryTemplate).where(QueryTemplate.id == template_id)
        result = await db.execute(query)
        db_template = result.scalars().first()
        if not db_template:
            return None

        db_template.embedding = embedding
        await db.commit()
        await db.refresh(db_template)
        return db_template

    @staticmethod
    async def update_template_usage(
        db: AsyncSession,
        template_id: UUID,
        success: bool,
        execution_time_ms: float,
        user: Optional[str] = None
    ) -> Optional[QueryTemplate]:
        """Update template usage statistics"""
        query = select(QueryTemplate).where(QueryTemplate.id == template_id)
        result = await db.execute(query)
        db_template = result.scalars().first()
        if not db_template:
            return None

        db_template.usage_count += 1
        if success:
            db_template.success_count += 1
        else:
            db_template.failure_count += 1

        # Update average execution time
        if db_template.avg_execution_time_ms is None:
            db_template.avg_execution_time_ms = execution_time_ms
        else:
            # Running average
            db_template.avg_execution_time_ms = (
                (db_template.avg_execution_time_ms * (db_template.usage_count - 1) + execution_time_ms)
                / db_template.usage_count
            )

        db_template.last_used_at = func.now()
        if user:
            db_template.last_used_by = user

        await db.commit()
        await db.refresh(db_template)
        return db_template

    @staticmethod
    async def delete_template(db: AsyncSession, template_id: UUID) -> bool:
        """Delete a query template"""
        query = select(QueryTemplate).where(QueryTemplate.id == template_id)
        result = await db.execute(query)
        db_template = result.scalars().first()
        if not db_template:
            return False

        db.delete(db_template)
        await db.commit()
        return True

    @staticmethod
    async def resolve_template_to_sql(
        db: AsyncSession,
        template_id: UUID,
        parameter_values: Dict[str, Any]
    ) -> Optional[str]:
        """Resolve template to SQL query by replacing parameters"""
        query = select(QueryTemplate).where(QueryTemplate.id == template_id)
        result = await db.execute(query)
        db_template = result.scalars().first()
        if not db_template:
            return None

        sql_template = db_template.sql_template

        # Replace parameters in template
        for key, value in parameter_values.items():
            placeholder = '{' + key + '}'
            sql_template = sql_template.replace(placeholder, str(value))

        return sql_template
