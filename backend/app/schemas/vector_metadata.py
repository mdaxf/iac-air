"""
Pydantic schemas for Vector Metadata Models
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, UUID4


# ============================================================================
# Vector Table Metadata Schemas
# ============================================================================

class VectorTableMetadataBase(BaseModel):
    """Base schema for vector table metadata"""
    db_alias: str
    schema_name: str
    table_name: str
    table_type: Optional[str] = None
    description: Optional[str] = None
    business_metadata: Dict[str, Any] = Field(default_factory=dict)
    technical_metadata: Dict[str, Any] = Field(default_factory=dict)
    sample_queries: List[Dict[str, Any]] = Field(default_factory=list)


class VectorTableMetadataCreate(VectorTableMetadataBase):
    """Schema for creating vector table metadata"""
    pass


class VectorTableMetadataUpdate(BaseModel):
    """Schema for updating vector table metadata"""
    schema_name: Optional[str] = None
    table_name: Optional[str] = None
    table_type: Optional[str] = None
    description: Optional[str] = None
    business_metadata: Optional[Dict[str, Any]] = None
    technical_metadata: Optional[Dict[str, Any]] = None
    sample_queries: Optional[List[Dict[str, Any]]] = None
    quality_score: Optional[float] = None


class VectorTableMetadata(VectorTableMetadataBase):
    """Schema for vector table metadata response"""
    id: UUID4
    embedding: Optional[List[float]] = None
    usage_count: int = 0
    last_used_at: Optional[datetime] = None
    quality_score: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    last_schema_sync: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# Vector Column Metadata Schemas
# ============================================================================

class VectorColumnMetadataBase(BaseModel):
    """Base schema for vector column metadata"""
    table_metadata_id: UUID4
    column_name: str
    data_type: str
    is_nullable: Optional[bool] = None
    column_description: Optional[str] = None
    business_metadata: Dict[str, Any] = Field(default_factory=dict)
    statistics: Dict[str, Any] = Field(default_factory=dict)


class VectorColumnMetadataCreate(VectorColumnMetadataBase):
    """Schema for creating vector column metadata"""
    pass


class VectorColumnMetadataUpdate(BaseModel):
    """Schema for updating vector column metadata"""
    column_name: Optional[str] = None
    data_type: Optional[str] = None
    is_nullable: Optional[bool] = None
    column_description: Optional[str] = None
    business_metadata: Optional[Dict[str, Any]] = None
    statistics: Optional[Dict[str, Any]] = None


class VectorColumnMetadata(VectorColumnMetadataBase):
    """Schema for vector column metadata response"""
    id: UUID4
    embedding: Optional[List[float]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Vector Relationship Metadata Schemas
# ============================================================================

class VectorRelationshipMetadataBase(BaseModel):
    """Base schema for vector relationship metadata"""
    db_alias: str
    source_table_id: UUID4
    target_table_id: UUID4
    relationship_type: str  # 'foreign_key', 'inferred', 'manual'
    cardinality: Optional[str] = None  # '1:1', '1:N', 'N:M'
    description: Optional[str] = None
    join_condition: Dict[str, Any] = Field(default_factory=dict)
    business_metadata: Dict[str, Any] = Field(default_factory=dict)


class VectorRelationshipMetadataCreate(VectorRelationshipMetadataBase):
    """Schema for creating vector relationship metadata"""
    pass


class VectorRelationshipMetadataUpdate(BaseModel):
    """Schema for updating vector relationship metadata"""
    relationship_type: Optional[str] = None
    cardinality: Optional[str] = None
    description: Optional[str] = None
    join_condition: Optional[Dict[str, Any]] = None
    business_metadata: Optional[Dict[str, Any]] = None
    confidence_score: Optional[float] = None


class VectorRelationshipMetadata(VectorRelationshipMetadataBase):
    """Schema for vector relationship metadata response"""
    id: UUID4
    usage_count: int = 0
    last_used_at: Optional[datetime] = None
    confidence_score: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Vector Document Enhanced Schemas
# ============================================================================

class VectorDocumentEnhancedBase(BaseModel):
    """Base schema for enhanced vector document"""
    db_alias: str
    document_type: str  # 'table', 'column', 'relationship', 'entity', 'metric', 'template', 'uploaded_file'
    reference_id: Optional[UUID4] = None
    content: str
    chunk_index: Optional[int] = None
    total_chunks: Optional[int] = None
    parent_document_id: Optional[UUID4] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VectorDocumentEnhancedCreate(VectorDocumentEnhancedBase):
    """Schema for creating enhanced vector document"""
    created_by: Optional[str] = None


class VectorDocumentEnhancedUpdate(BaseModel):
    """Schema for updating enhanced vector document"""
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    error_message: Optional[str] = None
    quality_score: Optional[float] = None
    relevance_score: Optional[float] = None


class VectorDocumentEnhanced(VectorDocumentEnhancedBase):
    """Schema for enhanced vector document response"""
    id: UUID4
    content_hash: Optional[str] = None
    embedding: Optional[List[float]] = None
    status: str = 'pending'
    error_message: Optional[str] = None
    quality_score: Optional[float] = None
    relevance_score: Optional[float] = None
    retrieval_count: int = 0
    last_retrieved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================================================
# Search Schemas
# ============================================================================

class VectorTableSearch(BaseModel):
    """Search criteria for vector table metadata"""
    db_alias: str
    query: Optional[str] = None
    schema_name: Optional[str] = None
    table_type: Optional[str] = None
    limit: int = 50
    offset: int = 0


class VectorColumnSearch(BaseModel):
    """Search criteria for vector column metadata"""
    table_metadata_id: Optional[UUID4] = None
    query: Optional[str] = None
    data_type: Optional[str] = None
    limit: int = 50
    offset: int = 0


class VectorRelationshipSearch(BaseModel):
    """Search criteria for vector relationship metadata"""
    db_alias: str
    source_table_id: Optional[UUID4] = None
    target_table_id: Optional[UUID4] = None
    relationship_type: Optional[str] = None
    limit: int = 50
    offset: int = 0


class VectorDocumentSearch(BaseModel):
    """Search criteria for enhanced vector documents"""
    db_alias: str
    document_type: Optional[str] = None
    reference_id: Optional[UUID4] = None
    status: Optional[str] = None
    limit: int = 50
    offset: int = 0


# ============================================================================
# Schema Sync Schemas
# ============================================================================

class SchemaSyncRequest(BaseModel):
    """Request to sync database schema to vector metadata"""
    db_alias: str
    schema_names: Optional[List[str]] = None  # None means all schemas
    force_refresh: bool = False
    generate_embeddings: bool = True


class SchemaSyncResult(BaseModel):
    """Result of schema sync operation"""
    success: bool
    tables_synced: int
    columns_synced: int
    relationships_synced: int
    documents_created: int
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    sync_time_ms: float


# ============================================================================
# Progressive Retrieval Schemas
# ============================================================================

class ProgressiveRetrievalRequest(BaseModel):
    """Request for progressive retrieval of relevant tables"""
    db_alias: str
    question: str
    max_tables: int = 10
    include_columns: bool = True
    include_relationships: bool = True
    similarity_threshold: float = 0.7


class RelevantTable(BaseModel):
    """A table identified as relevant to the question"""
    table_metadata: VectorTableMetadata
    relevance_score: float
    columns: Optional[List[VectorColumnMetadata]] = None
    relationships: Optional[List[VectorRelationshipMetadata]] = None


class ProgressiveRetrievalResult(BaseModel):
    """Result of progressive retrieval"""
    success: bool
    relevant_tables: List[RelevantTable]
    total_tables_searched: int
    retrieval_time_ms: float
    error: Optional[str] = None
