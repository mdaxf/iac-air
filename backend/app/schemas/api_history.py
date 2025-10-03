from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class HTTPMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    OPTIONS = "OPTIONS"
    HEAD = "HEAD"


class StatusRange(str, Enum):
    SUCCESS = "2xx"
    CLIENT_ERROR = "4xx"
    SERVER_ERROR = "5xx"


class APIHistoryFilter(BaseModel):
    """Filter parameters for API history queries"""
    method: Optional[HTTPMethod] = None
    status_code: Optional[int] = Field(None, ge=100, le=599)
    status_range: Optional[StatusRange] = None
    source: Optional[str] = None
    user_id: Optional[str] = None
    username: Optional[str] = None
    path: Optional[str] = None
    client_ip: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    min_duration_ms: Optional[float] = Field(None, ge=0)
    max_duration_ms: Optional[float] = Field(None, ge=0)
    has_error: Optional[bool] = None


class APIHistoryRecord(BaseModel):
    """API history record response"""
    id: str
    method: str
    path: str
    full_url: str
    query_params: Optional[Dict[str, Any]] = None
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None
    user_id: Optional[str] = None
    username: Optional[str] = None
    is_admin: Optional[str] = None
    status_code: int
    request_size: Optional[int] = None
    response_size: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    duration_seconds: Optional[float] = None
    endpoint_name: Optional[str] = None
    source: Optional[str] = None
    error_message: Optional[str] = None
    is_success: bool
    is_client_error: bool
    is_server_error: bool
    created_at: datetime

    class Config:
        from_attributes = True


class APIHistoryDetailRecord(APIHistoryRecord):
    """Detailed API history record with request/response data"""
    request_headers: Optional[Dict[str, str]] = None
    request_body: Optional[Any] = None
    response_headers: Optional[Dict[str, str]] = None
    response_body: Optional[Any] = None
    referer: Optional[str] = None
    correlation_id: Optional[str] = None
    stack_trace: Optional[str] = None


class APIHistoryResponse(BaseModel):
    """Paginated API history response"""
    records: List[APIHistoryRecord]
    total_count: int
    offset: int
    limit: int
    has_more: bool


class APIHistoryStats(BaseModel):
    """API history statistics"""
    period_hours: int
    total_requests: int
    status_breakdown: Dict[str, int]
    method_breakdown: Dict[str, int]
    source_breakdown: Dict[str, int]
    avg_duration_ms: float
    min_duration_ms: float
    max_duration_ms: float
    error_count: int
    error_rate: float
    top_paths: List[Dict[str, Any]]
    active_users: int


class APIHistoryCleanupResult(BaseModel):
    """Result of API history cleanup operation"""
    deleted: int
    remaining: int
    cutoff_date: str


class APIHistoryConfig(BaseModel):
    """API history configuration"""
    enabled: bool
    retention_days: int
    max_request_size: int
    max_response_size: int


class TopPath(BaseModel):
    """Top API path statistics"""
    path: str
    count: int
    avg_duration_ms: Optional[float] = None
    error_rate: Optional[float] = None


class UserActivity(BaseModel):
    """User activity summary"""
    user_id: str
    username: str
    request_count: int
    error_count: int
    avg_duration_ms: float
    last_activity: datetime


class APIHealthMetrics(BaseModel):
    """API health metrics"""
    total_requests_last_hour: int
    total_requests_last_24h: int
    avg_response_time_ms: float
    error_rate_percent: float
    top_error_paths: List[TopPath]
    slowest_endpoints: List[TopPath]
    most_active_users: List[UserActivity]