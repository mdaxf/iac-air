"""
Enhanced Vector Service

Integrates with embedding service to generate and manage embeddings for all metadata types.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.vector_metadata import (
    VectorTableMetadata,
    VectorColumnMetadata,
    VectorDocumentEnhanced
)
from app.models.business_semantic import (
    BusinessEntity,
    BusinessMetric,
    QueryTemplate
)


class EnhancedVectorService:
    """Service for generating and managing vector embeddings"""

    def __init__(self, embedding_service):
        """Initialize with embedding service"""
        self.embedding_service = embedding_service

    async def generate_table_embedding(
        self,
        db: Session,
        table: VectorTableMetadata
    ) -> List[float]:
        """Generate embedding for table metadata"""

        # Build text representation
        text_parts = [
            f"Table: {table.schema_name}.{table.table_name}",
            f"Type: {table.table_type}"
        ]

        if table.description:
            text_parts.append(f"Description: {table.description}")

        # Add business metadata
        business_meta = table.business_metadata or {}
        if business_meta.get('display_name'):
            text_parts.append(f"Display Name: {business_meta['display_name']}")
        if business_meta.get('category'):
            text_parts.append(f"Category: {business_meta['category']}")
        if business_meta.get('tags'):
            text_parts.append(f"Tags: {', '.join(business_meta['tags'])}")

        text = "\n".join(text_parts)

        # Generate embedding
        embedding = await self.embedding_service.generate_embedding(text)

        # Update table
        table.embedding = embedding
        db.commit()
        db.refresh(table)

        return embedding

    async def generate_column_embedding(
        self,
        db: Session,
        column: VectorColumnMetadata
    ) -> List[float]:
        """Generate embedding for column metadata"""

        # Build text representation
        text_parts = [
            f"Column: {column.column_name}",
            f"Data Type: {column.data_type}"
        ]

        if column.column_description:
            text_parts.append(f"Description: {column.column_description}")

        # Add business metadata
        business_meta = column.business_metadata or {}
        if business_meta.get('display_name'):
            text_parts.append(f"Display Name: {business_meta['display_name']}")
        if business_meta.get('business_definition'):
            text_parts.append(f"Business Definition: {business_meta['business_definition']}")
        if business_meta.get('data_classification'):
            text_parts.append(f"Classification: {business_meta['data_classification']}")

        text = "\n".join(text_parts)

        # Generate embedding
        embedding = await self.embedding_service.generate_embedding(text)

        # Update column
        column.embedding = embedding
        db.commit()
        db.refresh(column)

        return embedding

    async def generate_entity_embedding(
        self,
        db: Session,
        entity: BusinessEntity
    ) -> List[float]:
        """Generate embedding for business entity"""

        text_parts = [
            f"Business Entity: {entity.entity_name}",
            f"Type: {entity.entity_type}"
        ]

        if entity.description:
            text_parts.append(f"Description: {entity.description}")

        # Add attributes
        attributes = entity.attributes or {}
        if attributes.get('display_name'):
            text_parts.append(f"Display Name: {attributes['display_name']}")
        if attributes.get('synonyms'):
            text_parts.append(f"Synonyms: {', '.join(attributes['synonyms'])}")
        if attributes.get('common_questions'):
            text_parts.append(f"Common Questions: {', '.join(attributes['common_questions'])}")

        text = "\n".join(text_parts)

        # Generate embedding
        embedding = await self.embedding_service.generate_embedding(text)

        # Update entity
        entity.embedding = embedding
        db.commit()
        db.refresh(entity)

        return embedding

    async def generate_metric_embedding(
        self,
        db: Session,
        metric: BusinessMetric
    ) -> List[float]:
        """Generate embedding for business metric"""

        text_parts = [f"Business Metric: {metric.metric_name}"]

        # Add metric definition
        definition = metric.metric_definition or {}
        if definition.get('display_name'):
            text_parts.append(f"Display Name: {definition['display_name']}")
        if definition.get('description'):
            text_parts.append(f"Description: {definition['description']}")
        if definition.get('business_formula'):
            text_parts.append(f"Formula: {definition['business_formula']}")
        if definition.get('unit'):
            text_parts.append(f"Unit: {definition['unit']}")

        text = "\n".join(text_parts)

        # Generate embedding
        embedding = await self.embedding_service.generate_embedding(text)

        # Update metric
        metric.embedding = embedding
        db.commit()
        db.refresh(metric)

        return embedding

    async def generate_template_embedding(
        self,
        db: Session,
        template: QueryTemplate
    ) -> List[float]:
        """Generate embedding for query template"""

        text_parts = [
            f"Query Template: {template.template_name}",
            f"Category: {template.category}"
        ]

        if template.description:
            text_parts.append(f"Description: {template.description}")

        # Add example questions
        if template.example_questions:
            text_parts.append(f"Example Questions: {', '.join(template.example_questions)}")

        text = "\n".join(text_parts)

        # Generate embedding
        embedding = await self.embedding_service.generate_embedding(text)

        # Update template
        template.embedding = embedding
        db.commit()
        db.refresh(template)

        return embedding

    async def generate_document_embedding(
        self,
        db: Session,
        document: VectorDocumentEnhanced
    ) -> List[float]:
        """Generate embedding for vector document"""

        # Use document content directly
        text = document.content

        # Generate embedding
        embedding = await self.embedding_service.generate_embedding(text)

        # Update document
        document.embedding = embedding
        document.status = 'ready'
        db.commit()
        db.refresh(document)

        return embedding

    async def batch_generate_embeddings(
        self,
        db: Session,
        items: List[Any],
        item_type: str
    ) -> Dict[str, Any]:
        """Batch generate embeddings for multiple items"""

        results = {
            'total': len(items),
            'succeeded': 0,
            'failed': 0,
            'errors': []
        }

        generators = {
            'table': self.generate_table_embedding,
            'column': self.generate_column_embedding,
            'entity': self.generate_entity_embedding,
            'metric': self.generate_metric_embedding,
            'template': self.generate_template_embedding,
            'document': self.generate_document_embedding
        }

        generator = generators.get(item_type)
        if not generator:
            raise ValueError(f"Unknown item type: {item_type}")

        for item in items:
            try:
                await generator(db, item)
                results['succeeded'] += 1
            except Exception as e:
                results['failed'] += 1
                results['errors'].append({
                    'item_id': str(item.id),
                    'error': str(e)
                })

        return results

    async def search_similar_tables(
        self,
        db: Session,
        query_text: str,
        db_alias: str,
        limit: int = 10
    ) -> List[VectorTableMetadata]:
        """Search similar tables using text query"""

        # Generate query embedding
        query_embedding = await self.embedding_service.generate_embedding(query_text)

        # Search
        tables = db.query(VectorTableMetadata).filter(
            VectorTableMetadata.db_alias == db_alias
        ).order_by(
            VectorTableMetadata.embedding.cosine_distance(query_embedding)
        ).limit(limit).all()

        return tables

    async def search_similar_entities(
        self,
        db: Session,
        query_text: str,
        db_alias: str,
        limit: int = 10
    ) -> List[BusinessEntity]:
        """Search similar entities using text query"""

        # Generate query embedding
        query_embedding = await self.embedding_service.generate_embedding(query_text)

        # Search
        entities = db.query(BusinessEntity).filter(
            BusinessEntity.db_alias == db_alias
        ).order_by(
            BusinessEntity.embedding.cosine_distance(query_embedding)
        ).limit(limit).all()

        return entities

    async def search_similar_metrics(
        self,
        db: Session,
        query_text: str,
        db_alias: str,
        limit: int = 10
    ) -> List[BusinessMetric]:
        """Search similar metrics using text query"""

        # Generate query embedding
        query_embedding = await self.embedding_service.generate_embedding(query_text)

        # Search
        metrics = db.query(BusinessMetric).filter(
            BusinessMetric.db_alias == db_alias
        ).order_by(
            BusinessMetric.embedding.cosine_distance(query_embedding)
        ).limit(limit).all()

        return metrics

    async def search_similar_templates(
        self,
        db: Session,
        query_text: str,
        db_alias: Optional[str] = None,
        limit: int = 10
    ) -> List[QueryTemplate]:
        """Search similar templates using text query"""

        # Generate query embedding
        query_embedding = await self.embedding_service.generate_embedding(query_text)

        # Search
        query = db.query(QueryTemplate).filter(
            QueryTemplate.status == 'active'
        )

        if db_alias:
            query = query.filter(
                (QueryTemplate.db_alias == db_alias) | (QueryTemplate.db_alias == None)
            )

        templates = query.order_by(
            QueryTemplate.embedding.cosine_distance(query_embedding)
        ).limit(limit).all()

        return templates
