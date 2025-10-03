from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel


class DashboardStats(BaseModel):
    """Dashboard statistics aggregating system-wide metrics"""

    # Core Metrics
    total_databases: int
    active_conversations: int
    total_indexed_documents: int
    total_users: int
    active_users_24h: int

    # API Activity (24h)
    api_requests_24h: int
    api_errors_24h: int
    api_error_rate: float
    avg_response_time_ms: float

    # Chat Activity
    conversations_24h: int
    messages_24h: int

    # System Health
    system_status: str  # "healthy", "warning", "error"
    database_status: str
    vector_db_status: str

    # Recent Activity Summary
    recent_activity_count: int


class RecentActivity(BaseModel):
    """Recent system activity entry"""
    id: str
    type: str  # "database_connection", "chat_started", "user_login", "import_completed", etc.
    title: str
    description: Optional[str] = None
    user_id: Optional[str] = None
    username: Optional[str] = None
    status: str  # "success", "warning", "error"
    timestamp: datetime
    metadata: Dict[str, Any] = {}


class DashboardData(BaseModel):
    """Complete dashboard data including stats and recent activity"""
    stats: DashboardStats
    recent_activities: List[RecentActivity]


class SystemHealthCheck(BaseModel):
    """System health check result"""
    service: str
    status: str  # "healthy", "warning", "error"
    message: Optional[str] = None
    response_time_ms: Optional[float] = None
    details: Dict[str, Any] = {}


class SystemHealth(BaseModel):
    """Overall system health status"""
    overall_status: str
    checks: List[SystemHealthCheck]
    timestamp: datetime


class SystemConfiguration(BaseModel):
    """System configuration for admin page"""
    llm_provider: str
    embedding_model: str
    vector_dimension: int
    max_query_results: int
    api_history_enabled: bool
    api_history_retention_days: int
    log_level: str
    environment: str