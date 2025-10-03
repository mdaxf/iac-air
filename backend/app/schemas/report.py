from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID

from app.models.report import ReportType, ComponentType, ChartType, BarcodeType


# Base schemas
class ReportBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    report_type: ReportType = ReportType.MANUAL
    is_public: bool = False
    is_template: bool = False
    layout_config: Dict[str, Any] = Field(default_factory=dict)
    page_settings: Dict[str, Any] = Field(default_factory=dict)
    ai_prompt: Optional[str] = None
    ai_analysis: Optional[Dict[str, Any]] = None
    template_source_id: Optional[UUID] = None
    tags: List[str] = Field(default_factory=list)


class ReportCreate(ReportBase):
    pass


class ReportUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_public: Optional[bool] = None
    is_template: Optional[bool] = None
    layout_config: Optional[Dict[str, Any]] = None
    page_settings: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


class Report(ReportBase):
    id: UUID
    created_by: UUID
    version: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_executed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Datasource schemas
class ReportDatasourceBase(BaseModel):
    alias: str = Field(..., min_length=1, max_length=100)
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    database_alias: str
    query_type: str = Field(default="visual", pattern="^(visual|custom)$")
    custom_sql: Optional[str] = None
    selected_tables: List[Dict[str, Any]] = Field(default_factory=list)
    selected_fields: List[Dict[str, Any]] = Field(default_factory=list)
    joins: List[Dict[str, Any]] = Field(default_factory=list)
    filters: List[Dict[str, Any]] = Field(default_factory=list)
    sorting: List[Dict[str, Any]] = Field(default_factory=list)
    grouping: List[Dict[str, Any]] = Field(default_factory=list)
    parameters: List[Dict[str, Any]] = Field(default_factory=list)


class ReportDatasourceCreate(ReportDatasourceBase):
    report_id: UUID


class ReportDatasourceUpdate(BaseModel):
    alias: Optional[str] = Field(None, min_length=1, max_length=100)
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    database_alias: Optional[str] = None
    query_type: Optional[str] = Field(None, pattern="^(visual|custom)$")
    custom_sql: Optional[str] = None
    selected_tables: Optional[List[Dict[str, Any]]] = None
    selected_fields: Optional[List[Dict[str, Any]]] = None
    joins: Optional[List[Dict[str, Any]]] = None
    filters: Optional[List[Dict[str, Any]]] = None
    sorting: Optional[List[Dict[str, Any]]] = None
    grouping: Optional[List[Dict[str, Any]]] = None
    parameters: Optional[List[Dict[str, Any]]] = None


class ReportDatasource(ReportDatasourceBase):
    id: UUID
    report_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Component schemas
class ReportComponentBase(BaseModel):
    component_type: ComponentType
    name: str = Field(..., min_length=1, max_length=255)
    x: float = 0
    y: float = 0
    width: float = 100
    height: float = 100
    z_index: int = 1
    datasource_alias: Optional[str] = None
    data_config: Dict[str, Any] = Field(default_factory=dict)
    component_config: Dict[str, Any] = Field(default_factory=dict)
    style_config: Dict[str, Any] = Field(default_factory=dict)
    chart_type: Optional[ChartType] = None
    chart_config: Dict[str, Any] = Field(default_factory=dict)
    barcode_type: Optional[BarcodeType] = None
    barcode_config: Dict[str, Any] = Field(default_factory=dict)
    drill_down_config: Dict[str, Any] = Field(default_factory=dict)
    conditional_formatting: List[Dict[str, Any]] = Field(default_factory=list)
    is_visible: bool = True


class ReportComponentCreate(ReportComponentBase):
    report_id: Optional[UUID] = None  # Will be set from URL parameter


class ReportComponentUpdate(BaseModel):
    component_type: Optional[ComponentType] = None
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    x: Optional[float] = None
    y: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    z_index: Optional[int] = None
    datasource_alias: Optional[str] = None
    data_config: Optional[Dict[str, Any]] = None
    component_config: Optional[Dict[str, Any]] = None
    style_config: Optional[Dict[str, Any]] = None
    chart_type: Optional[ChartType] = None
    chart_config: Optional[Dict[str, Any]] = None
    barcode_type: Optional[BarcodeType] = None
    barcode_config: Optional[Dict[str, Any]] = None
    drill_down_config: Optional[Dict[str, Any]] = None
    conditional_formatting: Optional[List[Dict[str, Any]]] = None
    is_visible: Optional[bool] = None


class ReportComponent(ReportComponentBase):
    id: UUID
    report_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Template schemas
class ReportTemplateBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    template_config: Dict[str, Any]
    preview_image: Optional[str] = None
    ai_compatible: bool = True
    ai_tags: List[str] = Field(default_factory=list)
    suggested_use_cases: List[str] = Field(default_factory=list)
    is_public: bool = True
    is_system: bool = False


class ReportTemplateCreate(ReportTemplateBase):
    pass


class ReportTemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    template_config: Optional[Dict[str, Any]] = None
    preview_image: Optional[str] = None
    ai_compatible: Optional[bool] = None
    ai_tags: Optional[List[str]] = None
    suggested_use_cases: Optional[List[str]] = None
    is_public: Optional[bool] = None


class ReportTemplate(ReportTemplateBase):
    id: UUID
    created_by: Optional[UUID] = None
    usage_count: int
    rating: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Execution schemas
class ReportExecutionRequest(BaseModel):
    parameters: Dict[str, Any] = Field(default_factory=dict)
    output_format: str = Field(default="html", pattern="^(html|pdf|excel|csv)$")


class ReportExecution(BaseModel):
    id: UUID
    report_id: UUID
    executed_by: UUID
    execution_status: str
    execution_time_ms: Optional[int] = None
    error_message: Optional[str] = None
    parameters: Dict[str, Any]
    output_format: str
    output_size_bytes: Optional[int] = None
    output_path: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Share schemas
class ReportShareCreate(BaseModel):
    shared_with: Optional[UUID] = None  # None for public share
    can_view: bool = True
    can_edit: bool = False
    can_execute: bool = True
    can_share: bool = False
    expires_at: Optional[datetime] = None


class ReportShare(BaseModel):
    id: UUID
    report_id: UUID
    shared_by: UUID
    shared_with: Optional[UUID] = None
    can_view: bool
    can_edit: bool
    can_execute: bool
    can_share: bool
    share_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Database metadata schemas
class DatabaseTable(BaseModel):
    name: str
    schema: Optional[str] = None
    type: str  # 'table' or 'view'
    comment: Optional[str] = None


class DatabaseField(BaseModel):
    name: str
    data_type: str
    is_nullable: bool
    is_primary_key: bool = False
    is_foreign_key: bool = False
    default_value: Optional[str] = None
    comment: Optional[str] = None


class DatabaseTableDetail(DatabaseTable):
    fields: List[DatabaseField]
    row_count: Optional[int] = None


class DatabaseSchema(BaseModel):
    name: str
    tables: List[DatabaseTable]


class DatabaseMetadata(BaseModel):
    database_alias: str
    schemas: List[DatabaseSchema]


# Query builder schemas
class QueryBuilderField(BaseModel):
    table: Optional[str] = None  # Optional for custom SQL queries
    field: str
    alias: Optional[str] = None
    aggregation: Optional[str] = None  # SUM, COUNT, AVG, etc.


class QueryBuilderJoin(BaseModel):
    left_table: str
    right_table: str
    left_field: str
    right_field: str
    join_type: str = "INNER"  # INNER, LEFT, RIGHT, FULL


class QueryBuilderFilter(BaseModel):
    field: str
    operator: str  # =, !=, >, <, >=, <=, LIKE, IN, etc.
    value: Union[str, int, float, List[Any]]
    condition: str = "AND"  # AND, OR


class QueryBuilderSort(BaseModel):
    field: str
    direction: str = "ASC"  # ASC, DESC


class VisualQuery(BaseModel):
    tables: List[str]
    fields: List[QueryBuilderField]
    joins: List[QueryBuilderJoin] = Field(default_factory=list)
    filters: List[QueryBuilderFilter] = Field(default_factory=list)
    sorting: List[QueryBuilderSort] = Field(default_factory=list)
    grouping: List[str] = Field(default_factory=list)
    limit: Optional[int] = None


class QueryResult(BaseModel):
    sql: str
    columns: List[str]
    data: List[Dict[str, Any]]
    total_rows: int
    execution_time_ms: int


# Complete report response with relationships
class ReportDetail(Report):
    datasources: List[ReportDatasource] = Field(default_factory=list)
    components: List[ReportComponent] = Field(default_factory=list)
    creator_name: Optional[str] = None
    template_source_name: Optional[str] = None


class ReportListItem(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    report_type: ReportType
    is_template: bool
    is_public: bool
    created_by: UUID
    creator_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_executed_at: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)

    class Config:
        from_attributes = True


# AI integration schemas
class AIReportRequest(BaseModel):
    prompt: str = Field(..., min_length=10)
    database_aliases: List[str] = Field(..., min_items=1)
    preferred_template_id: Optional[UUID] = None
    output_type: str = Field(default="dashboard", pattern="^(report|dashboard|chart|table)$")
    complexity_level: str = Field(default="medium", pattern="^(simple|medium|complex)$")


class AIReportResponse(BaseModel):
    report_id: UUID
    analysis: Dict[str, Any]
    suggested_templates: List[ReportTemplate] = Field(default_factory=list)
    confidence_score: float
    processing_time_ms: int