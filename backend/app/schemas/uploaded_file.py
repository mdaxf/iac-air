"""
Pydantic schemas for Uploaded Files
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, UUID4


class UploadedFileBase(BaseModel):
    """Base schema for uploaded file"""
    db_alias: str
    file_name: str
    file_type: str
    file_size_bytes: int
    mime_type: Optional[str] = None
    content_metadata: Dict[str, Any] = Field(default_factory=dict)


class UploadedFileCreate(UploadedFileBase):
    """Schema for creating uploaded file record"""
    file_path: str
    uploaded_by: Optional[str] = None


class UploadedFileUpdate(BaseModel):
    """Schema for updating uploaded file"""
    status: Optional[str] = None
    processing_progress: Optional[float] = None
    error_message: Optional[str] = None
    content_metadata: Optional[Dict[str, Any]] = None
    processing_results: Optional[Dict[str, Any]] = None
    processed_at: Optional[datetime] = None


class UploadedFile(UploadedFileBase):
    """Schema for uploaded file response"""
    id: UUID4
    file_path: str
    status: str
    processing_progress: float = 0.0
    error_message: Optional[str] = None
    processing_results: Dict[str, Any] = Field(default_factory=dict)
    uploaded_at: datetime
    uploaded_by: Optional[str] = None
    processed_at: Optional[datetime] = None
    updated_at: datetime

    class Config:
        from_attributes = True


class FileUploadRequest(BaseModel):
    """Request for file upload"""
    db_alias: str
    uploaded_by: Optional[str] = None
    content_metadata: Dict[str, Any] = Field(default_factory=dict)


class FileUploadResponse(BaseModel):
    """Response after file upload"""
    success: bool
    file_id: Optional[UUID4] = None
    file_name: str
    file_size_bytes: int
    status: str
    message: Optional[str] = None


class FileProcessRequest(BaseModel):
    """Request to process uploaded file"""
    file_id: UUID4
    chunk_size: int = 1000
    chunk_overlap: int = 200
    generate_embeddings: bool = True


class FileProcessResult(BaseModel):
    """Result of file processing"""
    success: bool
    file_id: UUID4
    chunks_created: int
    embeddings_generated: int
    tables_mentioned: List[str] = Field(default_factory=list)
    processing_time_ms: float
    error: Optional[str] = None


class UploadedFileSearch(BaseModel):
    """Search criteria for uploaded files"""
    db_alias: Optional[str] = None
    file_type: Optional[str] = None
    status: Optional[str] = None
    uploaded_by: Optional[str] = None
    limit: int = 50
    offset: int = 0
