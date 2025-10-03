import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.auth import get_current_admin_user

from app.models.user import User
from app.schemas.logs import LogEntry, LogLevel, LogStats

from app.core.logging_config import log_method_calls, Logger, log_performance

router = APIRouter()


@router.get("/logs/files", response_model=List[str])
async def list_log_files(
    current_user: User = Depends(get_current_admin_user)
):
    """List all available log files"""
    log_dir = Path(settings.LOG_DIR)
    if not log_dir.exists():
        return []

    log_files = []
    for file_path in log_dir.glob("*.log*"):
        log_files.append(file_path.name)

    Logger.info(f"Admin {current_user.username} requested log files list")
    return sorted(log_files)


@router.get("/logs/{filename}/content")
async def get_log_content(
    filename: str,
    lines: int = Query(100, ge=1, le=10000, description="Number of lines to read"),
    search: Optional[str] = Query(None, description="Search term to filter lines"),
    level: Optional[LogLevel] = Query(None, description="Filter by log level"),
    current_user: User = Depends(get_current_admin_user)
):
    """Get content of a specific log file"""
    log_dir = Path(settings.LOG_DIR)
    log_file = log_dir / filename

    if not log_file.exists():
        raise HTTPException(status_code=404, detail="Log file not found")

    # Security check - ensure file is within logs directory
    if not str(log_file.resolve()).startswith(str(log_dir.resolve())):
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            # Read last N lines
            file_lines = f.readlines()
            recent_lines = file_lines[-lines:] if len(file_lines) > lines else file_lines

        # Filter by search term if provided
        if search:
            recent_lines = [line for line in recent_lines if search.lower() in line.lower()]

        # Filter by log level if provided
        if level:
            level_filter = level.value.upper()
            recent_lines = [line for line in recent_lines if level_filter in line]

        Logger.info(f"Admin {current_user.username} accessed log file: {filename}")
        return {
            "filename": filename,
            "lines": recent_lines,
            "total_lines": len(file_lines),
            "filtered_lines": len(recent_lines)
        }

    except Exception as e:
        Logger.error(f"Error reading log file {filename}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error reading log file")


@router.get("/logs/stats")
async def get_log_statistics(
    hours: int = Query(24, ge=1, le=168, description="Hours to analyze"),
    current_user: User = Depends(get_current_admin_user)
):
    """Get log statistics for the specified time period"""
    log_dir = Path(settings.LOG_DIR)
    if not log_dir.exists():
        return {"error": "Log directory not found"}

    cutoff_time = datetime.now() - timedelta(hours=hours)
    stats = {
        "period_hours": hours,
        "files": {},
        "summary": {
            "total_errors": 0,
            "total_warnings": 0,
            "total_info": 0,
            "total_debug": 0,
            "performance_issues": 0
        }
    }

    for log_file in log_dir.glob("*.log"):
        if log_file.stat().st_mtime < cutoff_time.timestamp():
            continue

        file_stats = {
            "size_mb": round(log_file.stat().st_size / (1024 * 1024), 2),
            "modified": datetime.fromtimestamp(log_file.stat().st_mtime).isoformat(),
            "errors": 0,
            "warnings": 0,
            "info": 0,
            "debug": 0
        }

        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if " ERROR " in line:
                        file_stats["errors"] += 1
                        stats["summary"]["total_errors"] += 1
                    elif " WARNING " in line:
                        file_stats["warnings"] += 1
                        stats["summary"]["total_warnings"] += 1
                    elif " INFO " in line:
                        file_stats["info"] += 1
                        stats["summary"]["total_info"] += 1
                    elif " DEBUG " in line:
                        file_stats["debug"] += 1
                        stats["summary"]["total_debug"] += 1

                    # Check for performance issues
                    if "PERF:" in line and "Duration:" in line:
                        try:
                            duration_str = line.split("Duration: ")[1].split("s")[0]
                            duration = float(duration_str)
                            if duration > settings.PERFORMANCE_LOG_THRESHOLD:
                                stats["summary"]["performance_issues"] += 1
                        except:
                            pass

        except Exception as e:
            Logger.error(f"Error analyzing log file {log_file}: {str(e)}")
            continue

        stats["files"][log_file.name] = file_stats

    Logger.info(f"Admin {current_user.username} requested log statistics")
    return stats


@router.post("/logs/clear/{filename}")
async def clear_log_file(
    filename: str,
    current_user: User = Depends(get_current_admin_user)
):
    """Clear a specific log file"""
    log_dir = Path(settings.LOG_DIR)
    log_file = log_dir / filename

    if not log_file.exists():
        raise HTTPException(status_code=404, detail="Log file not found")

    # Security check
    if not str(log_file.resolve()).startswith(str(log_dir.resolve())):
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        # Backup the file before clearing
        backup_name = f"{filename}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_file = log_dir / backup_name

        # Copy content to backup
        with open(log_file, 'r', encoding='utf-8') as src, \
             open(backup_file, 'w', encoding='utf-8') as dst:
            dst.write(src.read())

        # Clear the original file
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("")

        Logger.warning(f"Admin {current_user.username} cleared log file: {filename} (backup: {backup_name})")
        return {
            "message": f"Log file {filename} cleared successfully",
            "backup_file": backup_name
        }

    except Exception as e:
        Logger.error(f"Error clearing log file {filename}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error clearing log file")


@router.get("/logs/config")
async def get_log_config(
    current_user: User = Depends(get_current_admin_user)
):
    """Get current logging configuration"""
    config = {
        "log_level": settings.LOG_LEVEL,
        "log_dir": settings.LOG_DIR,
        "max_file_size": settings.LOG_MAX_FILE_SIZE,
        "backup_count": settings.LOG_BACKUP_COUNT,
        "rotation": settings.LOG_ROTATION,
        "performance_threshold": settings.PERFORMANCE_LOG_THRESHOLD,
        "log_format": settings.LOG_FORMAT,
        "date_format": settings.LOG_DATE_FORMAT
    }

    Logger.info(f"Admin {current_user.username} requested log configuration")
    return config


@router.post("/logs/level/{level}")
async def set_log_level(
    level: LogLevel,
    current_user: User = Depends(get_current_admin_user)
):
    """Change the application log level"""
    try:
        # Update the root logger level
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, level.value.upper()))

        # Update specific loggers
        for logger_name in ['app', 'debug', 'info', 'warning', 'error']:
            logger = logging.getLogger(logger_name)
            logger.setLevel(getattr(logging, level.value.upper()))

        Logger.warning(f"Admin {current_user.username} changed log level to: {level.value}")
        return {
            "message": f"Log level changed to {level.value}",
            "previous_level": settings.LOG_LEVEL,
            "new_level": level.value
        }

    except Exception as e:
        Logger.error(f"Error changing log level: {str(e)}")
        raise HTTPException(status_code=500, detail="Error changing log level")