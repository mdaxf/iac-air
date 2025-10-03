from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class DatabaseType(str, Enum):
    POSTGRES = "postgres"
    MYSQL = "mysql"
    MSSQL = "mssql"
    ORACLE = "oracle"


class DatabaseConnectionBase(BaseModel):
    alias: str = Field(..., description="Unique alias for the database")
    type: DatabaseType = Field(..., description="Database type")
    host: str = Field(..., description="Database host")
    port: int = Field(..., description="Database port")
    database: str = Field(..., description="Database name")
    username: str = Field(..., description="Database username")
    schema_whitelist: Optional[List[str]] = Field(default_factory=list, description="Allowed schemas")
    schema_blacklist: Optional[List[str]] = Field(default_factory=list, description="Blocked schemas")
    domain: Optional[str] = Field(None, description="Business domain (MES, ERP, CRM)")
    description: Optional[str] = Field(None, description="Database description")


class DatabaseConnectionCreate(DatabaseConnectionBase):
    password: str = Field(..., description="Database password")


class DatabaseConnectionUpdate(BaseModel):
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    schema_whitelist: Optional[List[str]] = None
    schema_blacklist: Optional[List[str]] = None
    domain: Optional[str] = None
    description: Optional[str] = None


class DatabaseConnection(DatabaseConnectionBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SchemaImportRequest(BaseModel):
    mode: str = Field("full", description="Import mode: full or incremental")
    sample_size: int = Field(100, description="Number of sample rows to extract")


class ImportJobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ImportJob(BaseModel):
    job_id: str
    db_alias: str
    status: ImportJobStatus
    progress: float = Field(0.0, description="Progress percentage")
    message: Optional[str] = None
    created_at: datetime
    updated_at: datetime