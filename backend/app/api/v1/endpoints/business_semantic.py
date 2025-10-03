"""
Business Semantic Layer API Endpoints

Provides REST API for managing business entities, metrics, templates, and concept mappings.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.business_semantic import (
    # Business Entity schemas
    BusinessEntity,
    BusinessEntityCreate,
    BusinessEntityUpdate,
    BusinessEntitySearch,
    # Business Metric schemas
    BusinessMetric,
    BusinessMetricCreate,
    BusinessMetricUpdate,
    BusinessMetricSearch,
    BusinessMetricTestRequest,
    BusinessMetricTestResult,
    # Concept Mapping schemas
    ConceptMapping,
    ConceptMappingCreate,
    ConceptMappingUpdate,
    ConceptMappingSearch,
    # Query Template schemas
    QueryTemplate,
    QueryTemplateCreate,
    QueryTemplateUpdate,
    QueryTemplateSearch,
    QueryTemplateExecuteRequest,
    QueryTemplateExecuteResult,
    # Bulk operations
    BulkRegenerateRequest,
    BulkOperationResult
)
from app.services.business_semantic_service import (
    BusinessEntityService,
    BusinessMetricService,
    ConceptMappingService,
    QueryTemplateService
)
from app.services.concept_extraction_service import ConceptExtractionService
from app.core.logging_config import log_method_calls, Logger
import logging

router = APIRouter()
logger = logging.getLogger("business_semantic_api")


# ============================================================================
# Business Entity Endpoints
# ============================================================================

@router.post("/entities", response_model=BusinessEntity, status_code=201)
@log_method_calls
async def create_business_entity(
    entity: BusinessEntityCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new business entity"""
    try:
        # Check if entity already exists
        existing = await BusinessEntityService.get_entity_by_name(
            db, entity.db_alias, entity.entity_name
        )
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Entity '{entity.entity_name}' already exists for database '{entity.db_alias}'"
            )

        # TODO: Generate embedding for entity description + attributes
        # For now, create without embedding
        result = await BusinessEntityService.create_entity(db, entity, embedding=None)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating business entity: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/entities/{entity_id}", response_model=BusinessEntity)
@log_method_calls
async def get_business_entity(
    entity_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a business entity by ID"""
    entity = await BusinessEntityService.get_entity(db, entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity


@router.get("/entities", response_model=List[BusinessEntity])
@log_method_calls
async def list_business_entities(
    db_alias: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """List business entities with optional filters"""
    entities = await BusinessEntityService.list_entities(
        db, db_alias=db_alias, entity_type=entity_type, limit=limit, offset=offset
    )
    return entities


@router.post("/entities/search", response_model=List[BusinessEntity])
@log_method_calls
async def search_business_entities(
    search: BusinessEntitySearch,
    db: AsyncSession = Depends(get_db)
):
    """Search business entities"""
    entities = await BusinessEntityService.search_entities(db, search)
    return entities


@router.put("/entities/{entity_id}", response_model=BusinessEntity)
@log_method_calls
async def update_business_entity(
    entity_id: UUID,
    entity_update: BusinessEntityUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a business entity"""
    entity = await BusinessEntityService.update_entity(db, entity_id, entity_update)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity


@router.delete("/entities/{entity_id}", status_code=204)
@log_method_calls
async def delete_business_entity(
    entity_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete a business entity"""
    success = await BusinessEntityService.delete_entity(db, entity_id)
    if not success:
        raise HTTPException(status_code=404, detail="Entity not found")
    return None


# ============================================================================
# Business Metric Endpoints
# ============================================================================

@router.post("/metrics", response_model=BusinessMetric, status_code=201)
@log_method_calls
async def create_business_metric(
    metric: BusinessMetricCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new business metric"""
    try:
        # Check if metric already exists
        existing = await BusinessMetricService.get_metric_by_name(
            db, metric.db_alias, metric.metric_name
        )
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Metric '{metric.metric_name}' already exists for database '{metric.db_alias}'"
            )

        # TODO: Generate embedding for metric definition
        result = await BusinessMetricService.create_metric(db, metric, embedding=None)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating business metric: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/{metric_id}", response_model=BusinessMetric)
@log_method_calls
async def get_business_metric(
    metric_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a business metric by ID"""
    metric = await BusinessMetricService.get_metric(db, metric_id)
    if not metric:
        raise HTTPException(status_code=404, detail="Metric not found")
    return metric


@router.get("/metrics", response_model=List[BusinessMetric])
@log_method_calls
async def list_business_metrics(
    db_alias: Optional[str] = Query(None),
    entity_id: Optional[UUID] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """List business metrics with optional filters"""
    metrics = await BusinessMetricService.list_metrics(
        db, db_alias=db_alias, entity_id=entity_id, limit=limit, offset=offset
    )
    return metrics


@router.post("/metrics/search", response_model=List[BusinessMetric])
@log_method_calls
async def search_business_metrics(
    search: BusinessMetricSearch,
    db: AsyncSession = Depends(get_db)
):
    """Search business metrics"""
    metrics = await BusinessMetricService.search_metrics(db, search)
    return metrics


@router.put("/metrics/{metric_id}", response_model=BusinessMetric)
@log_method_calls
async def update_business_metric(
    metric_id: UUID,
    metric_update: BusinessMetricUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a business metric"""
    metric = await BusinessMetricService.update_metric(db, metric_id, metric_update)
    if not metric:
        raise HTTPException(status_code=404, detail="Metric not found")
    return metric


@router.delete("/metrics/{metric_id}", status_code=204)
@log_method_calls
async def delete_business_metric(
    metric_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete a business metric"""
    success = await BusinessMetricService.delete_metric(db, metric_id)
    if not success:
        raise HTTPException(status_code=404, detail="Metric not found")
    return None


@router.post("/metrics/{metric_id}/test", response_model=BusinessMetricTestResult)
@log_method_calls
async def test_business_metric(
    metric_id: UUID,
    test_request: BusinessMetricTestRequest,
    db: AsyncSession = Depends(get_db)
):
    """Test a business metric by executing it with provided parameters"""
    try:
        import time
        start_time = time.time()

        # Get the metric
        metric = await BusinessMetricService.get_metric(db, metric_id)
        if not metric:
            raise HTTPException(status_code=404, detail="Metric not found")

        # Resolve to SQL
        sql = await BusinessMetricService.resolve_metric_to_sql(
            db, metric_id, test_request.parameters
        )

        if not sql:
            return BusinessMetricTestResult(
                success=False,
                execution_time_ms=0,
                error="No SQL template found for metric"
            )

        # TODO: Execute SQL against database and return results
        # For now, return the SQL as success
        execution_time_ms = (time.time() - start_time) * 1000

        return BusinessMetricTestResult(
            success=True,
            execution_time_ms=execution_time_ms,
            result=[{"sql": sql}],
            error=None
        )

    except Exception as e:
        logger.error(f"Error testing metric: {e}")
        return BusinessMetricTestResult(
            success=False,
            execution_time_ms=0,
            error=str(e)
        )


# ============================================================================
# Concept Mapping Endpoints
# ============================================================================

@router.post("/concept-mappings", response_model=ConceptMapping, status_code=201)
@log_method_calls
async def create_concept_mapping(
    mapping: ConceptMappingCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new concept mapping"""
    try:
        result = await ConceptMappingService.create_mapping(db, mapping)
        return result
    except Exception as e:
        logger.error(f"Error creating concept mapping: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/concept-mappings/{mapping_id}", response_model=ConceptMapping)
@log_method_calls
async def get_concept_mapping(
    mapping_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a concept mapping by ID"""
    mapping = await ConceptMappingService.get_mapping(db, mapping_id)
    if not mapping:
        raise HTTPException(status_code=404, detail="Concept mapping not found")
    return mapping


@router.get("/concept-mappings", response_model=List[ConceptMapping])
@log_method_calls
async def list_concept_mappings(
    db_alias: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """List concept mappings with optional filters"""
    mappings = await ConceptMappingService.list_mappings(
        db, db_alias=db_alias, category=category, limit=limit, offset=offset
    )
    return mappings


@router.post("/concept-mappings/search", response_model=List[ConceptMapping])
@log_method_calls
async def search_concept_mappings(
    search: ConceptMappingSearch,
    db: AsyncSession = Depends(get_db)
):
    """Search concept mappings"""
    mappings = await ConceptMappingService.search_mappings(db, search)
    return mappings


@router.put("/concept-mappings/{mapping_id}", response_model=ConceptMapping)
@log_method_calls
async def update_concept_mapping(
    mapping_id: UUID,
    mapping_update: ConceptMappingUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a concept mapping"""
    mapping = await ConceptMappingService.update_mapping(db, mapping_id, mapping_update)
    if not mapping:
        raise HTTPException(status_code=404, detail="Concept mapping not found")
    return mapping


@router.delete("/concept-mappings/{mapping_id}", status_code=204)
@log_method_calls
async def delete_concept_mapping(
    mapping_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete a concept mapping"""
    success = await ConceptMappingService.delete_mapping(db, mapping_id)
    if not success:
        raise HTTPException(status_code=404, detail="Concept mapping not found")
    return None


# ============================================================================
# Query Template Endpoints
# ============================================================================

@router.post("/query-templates", response_model=QueryTemplate, status_code=201)
@log_method_calls
async def create_query_template(
    template: QueryTemplateCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new query template"""
    try:
        # Check if template already exists
        existing = await QueryTemplateService.get_template_by_name(
            db, template.template_name, template.db_alias
        )
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Template '{template.template_name}' already exists"
            )

        # TODO: Generate embedding for template
        result = await QueryTemplateService.create_template(db, template, embedding=None)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating query template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/query-templates/{template_id}", response_model=QueryTemplate)
@log_method_calls
async def get_query_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a query template by ID"""
    template = await QueryTemplateService.get_template(db, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.get("/query-templates", response_model=List[QueryTemplate])
@log_method_calls
async def list_query_templates(
    db_alias: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """List query templates with optional filters"""
    templates = await QueryTemplateService.list_templates(
        db, db_alias=db_alias, category=category, status=status, limit=limit, offset=offset
    )
    return templates


@router.post("/query-templates/search", response_model=List[QueryTemplate])
@log_method_calls
async def search_query_templates(
    search: QueryTemplateSearch,
    db: AsyncSession = Depends(get_db)
):
    """Search query templates"""
    templates = await QueryTemplateService.search_templates(db, search)
    return templates


@router.put("/query-templates/{template_id}", response_model=QueryTemplate)
@log_method_calls
async def update_query_template(
    template_id: UUID,
    template_update: QueryTemplateUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a query template"""
    template = await QueryTemplateService.update_template(db, template_id, template_update)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.delete("/query-templates/{template_id}", status_code=204)
@log_method_calls
async def delete_query_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete a query template"""
    success = await QueryTemplateService.delete_template(db, template_id)
    if not success:
        raise HTTPException(status_code=404, detail="Template not found")
    return None


@router.post("/query-templates/{template_id}/execute", response_model=QueryTemplateExecuteResult)
@log_method_calls
async def execute_query_template(
    template_id: UUID,
    execute_request: QueryTemplateExecuteRequest,
    db: AsyncSession = Depends(get_db)
):
    """Execute a query template with provided parameter values"""
    try:
        import time
        start_time = time.time()

        # Get the template
        template = await QueryTemplateService.get_template(db, template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        # Resolve to SQL
        sql = await QueryTemplateService.resolve_template_to_sql(
            db, template_id, execute_request.parameter_values
        )

        if not sql:
            return QueryTemplateExecuteResult(
                success=False,
                sql_generated="",
                execution_time_ms=0,
                error="Failed to generate SQL from template"
            )

        # TODO: Execute SQL against database and return results
        # For now, return the SQL as success
        execution_time_ms = (time.time() - start_time) * 1000

        return QueryTemplateExecuteResult(
            success=True,
            sql_generated=sql,
            execution_time_ms=execution_time_ms,
            result=[],
            error=None
        )

    except Exception as e:
        logger.error(f"Error executing template: {e}")
        return QueryTemplateExecuteResult(
            success=False,
            sql_generated="",
            execution_time_ms=0,
            error=str(e)
        )


# ============================================================================
# Concept Extraction Endpoints
# ============================================================================

@router.post("/extract-concepts")
@log_method_calls
async def extract_concepts(
    db_alias: str = Query(..., description="Database alias to use for concept extraction"),
    question: str = Query(..., description="Natural language question to analyze"),
    db: AsyncSession = Depends(get_db)
):
    """Extract business concepts from a natural language question"""
    try:
        concepts = await ConceptExtractionService.extract_concepts(db, db_alias, question)
        return concepts
    except Exception as e:
        logger.error(f"Error extracting concepts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/normalize-question")
@log_method_calls
async def normalize_question(
    db_alias: str = Query(..., description="Database alias to use for normalization"),
    question: str = Query(..., description="Natural language question to normalize"),
    db: AsyncSession = Depends(get_db)
):
    """Normalize a natural language question by replacing synonyms with canonical terms"""
    try:
        normalized = await ConceptExtractionService.normalize_question(db, db_alias, question)
        return {"original": question, "normalized": normalized}
    except Exception as e:
        logger.error(f"Error normalizing question: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query-intent")
@log_method_calls
async def detect_query_intent(
    db_alias: str = Query(..., description="Database alias to use for intent detection"),
    question: str = Query(..., description="Natural language question to analyze"),
    db: AsyncSession = Depends(get_db)
):
    """Detect the intent of a natural language query"""
    try:
        intent = await ConceptExtractionService.extract_query_intent(db, db_alias, question)
        return intent
    except Exception as e:
        logger.error(f"Error detecting query intent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Bulk Operations
# ============================================================================

@router.post("/bulk/regenerate-embeddings", response_model=BulkOperationResult)
@log_method_calls
async def bulk_regenerate_embeddings(
    request: BulkRegenerateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Regenerate embeddings for multiple items"""
    # TODO: Implement bulk embedding regeneration
    # This will be implemented in Phase 3: Vector Regeneration System
    return BulkOperationResult(
        total=0,
        succeeded=0,
        failed=0,
        errors=[]
    )
