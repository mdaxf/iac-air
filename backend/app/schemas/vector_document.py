from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID


class VectorDocumentBase(BaseModel):
    resource_id: str = Field(..., description="Unique identifier for the resource")
    resource_type: str = Field(..., description="Type of resource: table_doc, column_doc, faq, conv_msg")
    db_alias: Optional[str] = Field(None, description="Database alias this document belongs to")
    title: Optional[str] = Field(None, description="Title of the document")
    content: str = Field(..., description="Content to be embedded")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    tenant_id: Optional[str] = Field(None, description="Tenant identifier for multi-tenancy")


class VectorDocumentCreate(VectorDocumentBase):
    pass


class VectorDocumentUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class VectorDocument(VectorDocumentBase):
    id: UUID
    embedding: Optional[List[float]] = Field(None, description="Embedding vector")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VectorSearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    db_alias: Optional[str] = Field(None, description="Filter by database alias")
    resource_type: Optional[str] = Field(None, description="Filter by resource type")
    top_k: int = Field(10, description="Number of results to return", ge=1, le=100)
    tenant_id: Optional[str] = Field(None, description="Tenant identifier")


class VectorSearchResult(BaseModel):
    document: VectorDocument
    score: float = Field(..., description="Similarity score")


class VectorDatabaseStats(BaseModel):
    db_alias: str
    total_documents: int
    embedding_model: str = Field(default="text-embedding-ada-002", description="Embedding model used")
    last_updated: Optional[datetime] = Field(None, description="Last time vectors were updated")
    document_types: Dict[str, int] = Field(default_factory=dict, description="Count by document type")


class DatabaseDocumentCreate(BaseModel):
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Document content describing database structure")
    document_type: str = Field(default="database_doc", description="Type of document")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")