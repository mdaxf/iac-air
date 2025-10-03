from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel


class LogLevel(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class LogEntry(BaseModel):
    timestamp: datetime
    level: LogLevel
    logger: str
    message: str
    module: Optional[str] = None
    function: Optional[str] = None
    line_number: Optional[int] = None
    extra_data: Optional[Dict[str, Any]] = None


class LogFileInfo(BaseModel):
    filename: str
    size_mb: float
    modified: datetime
    line_count: int


class LogStats(BaseModel):
    period_hours: int
    total_entries: int
    error_count: int
    warning_count: int
    info_count: int
    debug_count: int
    performance_issues: int
    files: List[LogFileInfo]


class LogConfiguration(BaseModel):
    log_level: str
    log_dir: str
    max_file_size: str
    backup_count: int
    rotation: str
    performance_threshold: float
    log_format: str
    date_format: str


class LogSearchRequest(BaseModel):
    filename: str
    search_term: Optional[str] = None
    log_level: Optional[LogLevel] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    max_lines: int = 1000


class LogSearchResponse(BaseModel):
    filename: str
    total_lines: int
    filtered_lines: int
    entries: List[str]
    search_term: Optional[str] = None
    log_level: Optional[LogLevel] = None