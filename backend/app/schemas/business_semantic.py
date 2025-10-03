"""
Pydantic schemas for Business Semantic Layer
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, UUID4


# ============================================================================
# Business Entity Schemas
# ============================================================================

class BusinessEntityAttributes(BaseModel):
    """Semantic attributes for a business entity"""
    display_name: Optional[str] = None
    plural_name: Optional[str] = None
    synonyms: List[str] = Field(default_factory=list)
    business_domain: Optional[str] = None
    sensitivity_level: Optional[str] = None
    common_questions: List[str] = Field(default_factory=list)


class BusinessEntitySourceMapping(BaseModel):
    """Source table mapping for a business entity"""
    primary_table: Optional[str] = None
    related_tables: List[Dict[str, Any]] = Field(default_factory=list)
    # Each related table: {"table": "...", "relationship": "1:N", "join_key": "..."}
    denormalized_view: Optional[str] = None
    key_columns: List[str] = Field(default_factory=list)


class BusinessEntityMetric(BaseModel):
    """Metric definition within an entity"""
    name: str
    calculation: str
    description: Optional[str] = None


class BusinessEntityBase(BaseModel):
    """Base schema for business entity"""
    db_alias: str
    entity_name: str
    entity_type: Optional[str] = None  # 'dimension', 'fact', 'metric'
    description: Optional[str] = None
    business_owner: Optional[str] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)
    source_mapping: Dict[str, Any] = Field(default_factory=dict)
    metrics: List[Dict[str, Any]] = Field(default_factory=list)


class BusinessEntityCreate(BusinessEntityBase):
    """Schema for creating a business entity"""
    created_by: Optional[str] = None


class BusinessEntityUpdate(BaseModel):
    """Schema for updating a business entity"""
    entity_name: Optional[str] = None
    entity_type: Optional[str] = None
    description: Optional[str] = None
    business_owner: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None
    source_mapping: Optional[Dict[str, Any]] = None
    metrics: Optional[List[Dict[str, Any]]] = None
    updated_by: Optional[str] = None


class BusinessEntity(BusinessEntityBase):
    """Schema for business entity response"""
    id: UUID4
    embedding: Optional[List[float]] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================================================
# Business Metric Schemas
# ============================================================================

class BusinessMetricDefinition(BaseModel):
    """Metric definition details"""
    display_name: Optional[str] = None
    description: Optional[str] = None
    business_formula: Optional[str] = None
    sql_template: Optional[str] = None
    parameters: List[Dict[str, Any]] = Field(default_factory=list)
    dimensions: List[str] = Field(default_factory=list)
    aggregation_type: Optional[str] = None
    unit: Optional[str] = None
    refresh_frequency: Optional[str] = None
    business_rules: List[str] = Field(default_factory=list)
    min_value: Optional[float] = None
    max_value: Optional[float] = None


class BusinessMetricBase(BaseModel):
    """Base schema for business metric"""
    db_alias: str
    metric_name: str
    entity_id: Optional[UUID4] = None
    metric_definition: Dict[str, Any] = Field(default_factory=dict)


class BusinessMetricCreate(BusinessMetricBase):
    """Schema for creating a business metric"""
    created_by: Optional[str] = None


class BusinessMetricUpdate(BaseModel):
    """Schema for updating a business metric"""
    metric_name: Optional[str] = None
    entity_id: Optional[UUID4] = None
    metric_definition: Optional[Dict[str, Any]] = None
    updated_by: Optional[str] = None


class BusinessMetric(BusinessMetricBase):
    """Schema for business metric response"""
    id: UUID4
    embedding: Optional[List[float]] = None
    usage_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    avg_execution_time_ms: Optional[float] = None
    last_used_at: Optional[datetime] = None
    last_used_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    class Config:
        from_attributes = True


class BusinessMetricTestRequest(BaseModel):
    """Request to test a business metric"""
    parameters: Dict[str, Any] = Field(default_factory=dict)


class BusinessMetricTestResult(BaseModel):
    """Result of testing a business metric"""
    success: bool
    execution_time_ms: float
    result: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None


# ============================================================================
# Concept Mapping Schemas
# ============================================================================

class ConceptMappingBase(BaseModel):
    """Base schema for concept mapping"""
    db_alias: str
    canonical_term: str
    synonyms: List[str] = Field(default_factory=list)
    entity_id: Optional[UUID4] = None
    metric_id: Optional[UUID4] = None
    template_id: Optional[UUID4] = None
    context: Optional[str] = None
    category: Optional[str] = None


class ConceptMappingCreate(ConceptMappingBase):
    """Schema for creating a concept mapping"""
    created_by: Optional[str] = None


class ConceptMappingUpdate(BaseModel):
    """Schema for updating a concept mapping"""
    canonical_term: Optional[str] = None
    synonyms: Optional[List[str]] = None
    entity_id: Optional[UUID4] = None
    metric_id: Optional[UUID4] = None
    template_id: Optional[UUID4] = None
    context: Optional[str] = None
    category: Optional[str] = None


class ConceptMapping(ConceptMappingBase):
    """Schema for concept mapping response"""
    id: UUID4
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================================================
# Query Template Schemas
# ============================================================================

class QueryTemplateParameter(BaseModel):
    """Parameter definition for a query template"""
    name: str
    type: str  # 'string', 'integer', 'date', 'select', etc.
    required: bool = False
    default: Optional[Any] = None
    options: Optional[List[Any]] = None
    description: Optional[str] = None


class QueryTemplateBase(BaseModel):
    """Base schema for query template"""
    db_alias: Optional[str] = None
    template_name: str
    description: Optional[str] = None
    category: Optional[str] = None
    example_questions: List[str] = Field(default_factory=list)
    sql_template: str
    parameters: List[Dict[str, Any]] = Field(default_factory=list)
    required_entities: List[str] = Field(default_factory=list)
    required_metrics: List[str] = Field(default_factory=list)
    status: str = 'active'


class QueryTemplateCreate(QueryTemplateBase):
    """Schema for creating a query template"""
    created_by: Optional[str] = None


class QueryTemplateUpdate(BaseModel):
    """Schema for updating a query template"""
    template_name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    example_questions: Optional[List[str]] = None
    sql_template: Optional[str] = None
    parameters: Optional[List[Dict[str, Any]]] = None
    required_entities: Optional[List[str]] = None
    required_metrics: Optional[List[str]] = None
    status: Optional[str] = None
    updated_by: Optional[str] = None


class QueryTemplate(QueryTemplateBase):
    """Schema for query template response"""
    id: UUID4
    embedding: Optional[List[float]] = None
    usage_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    avg_execution_time_ms: Optional[float] = None
    last_used_at: Optional[datetime] = None
    last_used_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    class Config:
        from_attributes = True


class QueryTemplateExecuteRequest(BaseModel):
    """Request to execute a query template"""
    parameter_values: Dict[str, Any] = Field(default_factory=dict)


class QueryTemplateExecuteResult(BaseModel):
    """Result of executing a query template"""
    success: bool
    sql_generated: str
    execution_time_ms: float
    result: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None


# ============================================================================
# Search and List Schemas
# ============================================================================

class BusinessEntitySearch(BaseModel):
    """Search criteria for business entities"""
    query: Optional[str] = None
    db_alias: Optional[str] = None
    entity_type: Optional[str] = None
    business_domain: Optional[str] = None
    limit: int = 50
    offset: int = 0


class BusinessMetricSearch(BaseModel):
    """Search criteria for business metrics"""
    query: Optional[str] = None
    db_alias: Optional[str] = None
    entity_id: Optional[UUID4] = None
    limit: int = 50
    offset: int = 0


class QueryTemplateSearch(BaseModel):
    """Search criteria for query templates"""
    query: Optional[str] = None
    db_alias: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    limit: int = 50
    offset: int = 0


class ConceptMappingSearch(BaseModel):
    """Search criteria for concept mappings"""
    query: Optional[str] = None
    db_alias: Optional[str] = None
    category: Optional[str] = None
    limit: int = 50
    offset: int = 0


# ============================================================================
# Bulk Operation Schemas
# ============================================================================

class BulkRegenerateRequest(BaseModel):
    """Request to regenerate embeddings for multiple items"""
    entity_ids: List[UUID4] = Field(default_factory=list)
    metric_ids: List[UUID4] = Field(default_factory=list)
    template_ids: List[UUID4] = Field(default_factory=list)
    force: bool = False


class BulkOperationResult(BaseModel):
    """Result of a bulk operation"""
    total: int
    succeeded: int
    failed: int
    errors: List[Dict[str, Any]] = Field(default_factory=list)
