"""
Report parameter schemas for request/response validation
"""

from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, field_serializer
from datetime import datetime
from uuid import UUID
from app.models.report_parameter import ParameterType


class ReportParameterBase(BaseModel):
    name: str = Field(..., description="Parameter name used in query (@param_name)")
    display_name: str = Field(..., description="Display name for user interface")
    parameter_type: ParameterType = Field(default=ParameterType.TEXT)
    default_value: Optional[str] = Field(None, description="Default value (JSON format for complex types)")
    is_required: bool = Field(default=False, description="Whether parameter is required")
    is_enabled: bool = Field(default=True, description="Whether parameter is enabled")
    validation_rules: Optional[str] = Field(None, description="Validation rules (JSON format)")
    options: Optional[str] = Field(None, description="Options for select/multi-select (JSON format)")
    description: Optional[str] = Field(None, description="Parameter description for users")
    sort_order: str = Field(default="0", description="Display order")


class ReportParameterCreate(ReportParameterBase):
    report_id: str = Field(..., description="Report ID this parameter belongs to")


class ReportParameterUpdate(BaseModel):
    display_name: Optional[str] = None
    parameter_type: Optional[ParameterType] = None
    default_value: Optional[str] = None
    is_required: Optional[bool] = None
    is_enabled: Optional[bool] = None
    validation_rules: Optional[str] = None
    options: Optional[str] = None
    description: Optional[str] = None
    sort_order: Optional[str] = None


class ReportParameterResponse(ReportParameterBase):
    id: UUID
    report_id: UUID
    created_at: datetime
    updated_at: datetime

    @field_serializer('id', 'report_id')
    def serialize_uuid(self, value: UUID) -> str:
        return str(value)

    class Config:
        from_attributes = True


class ReportParameterValueBase(BaseModel):
    parameter_id: str
    execution_id: str = Field(..., description="Execution session ID")
    value: Optional[str] = Field(None, description="Parameter value (JSON format)")


class ReportParameterValueCreate(ReportParameterValueBase):
    pass


class ReportParameterValueResponse(ReportParameterValueBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True


class ReportViewRequest(BaseModel):
    """Request schema for viewing a report with parameters"""
    report_id: str
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameter values for the report")
    execution_id: Optional[str] = Field(None, description="Optional execution ID for tracking")


class ReportDataResponse(BaseModel):
    """Response schema for report data"""
    report_id: str
    execution_id: str
    datasources: Dict[str, Any] = Field(description="Data for each datasource alias")
    components: List[Dict[str, Any]] = Field(description="Component configurations for rendering")
    parameters: Dict[str, Any] = Field(description="Parameter values used")
    execution_time_ms: Optional[int] = None
    generated_at: datetime