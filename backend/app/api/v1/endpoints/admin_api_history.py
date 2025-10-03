from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import get_current_admin_user,get_current_user
from app.core.logging_config import Logger, debug_logger
from app.models.user import User
from app.services.api_history_service import APIHistoryService
from app.schemas.api_history import (
    APIHistoryFilter, APIHistoryResponse, APIHistoryRecord,
    APIHistoryDetailRecord, APIHistoryStats, APIHistoryCleanupResult,
    APIHistoryConfig, HTTPMethod, StatusRange
)
from app.tasks.cleanup_tasks import cleanup_tasks

router = APIRouter()


@router.get("/api-history", response_model=APIHistoryResponse)
async def get_api_history(
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    method: Optional[str] = Query(None, description="Filter by HTTP method"),
    status_code: Optional[int] = Query(None, ge=100, le=599, description="Filter by status code"),
    status_range: Optional[str] = Query(None, description="Filter by status range"),
    source: Optional[str] = Query(None, description="Filter by request source"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    username: Optional[str] = Query(None, description="Filter by username"),
    path: Optional[str] = Query(None, description="Filter by API path"),
    client_ip: Optional[str] = Query(None, description="Filter by client IP"),
    start_date: Optional[str] = Query(None, description="Filter by start date"),
    end_date: Optional[str] = Query(None, description="Filter by end date"),
    min_duration_ms: Optional[float] = Query(None, ge=0, description="Minimum duration in ms"),
    max_duration_ms: Optional[float] = Query(None, ge=0, description="Maximum duration in ms"),
    has_error: Optional[str] = Query(None, description="Filter by error presence"),
    db: AsyncSession = Depends(get_db)#,
   # current_user: User = Depends(get_current_user)
):
    """Get API call history with filtering and pagination"""

    service = APIHistoryService()

    # Helper function to convert empty strings to None
    def empty_str_to_none(value):
        return None if value == "" else value

    # Parse date strings to datetime objects
    parsed_start_date = None
    parsed_end_date = None

    if start_date and start_date.strip():
        try:
            parsed_start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            debug_logger.warning(f"Invalid start_date format: {start_date}")

    if end_date and end_date.strip():
        try:
            parsed_end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            debug_logger.warning(f"Invalid end_date format: {end_date}")

    # Convert string enum values to proper enum types, handling empty strings
    parsed_method = None
    if method and method.strip():
        try:
            parsed_method = HTTPMethod(method)
        except ValueError:
            debug_logger.warning(f"Invalid method: {method}")

    parsed_status_range = None
    if status_range and status_range.strip():
        try:
            parsed_status_range = StatusRange(status_range)
        except ValueError:
            debug_logger.warning(f"Invalid status_range: {status_range}")

    # Parse boolean value
    parsed_has_error = None
    if has_error and has_error.strip():
        has_error_lower = has_error.lower().strip()
        if has_error_lower in ('true', '1', 'yes'):
            parsed_has_error = True
        elif has_error_lower in ('false', '0', 'no'):
            parsed_has_error = False
        else:
            debug_logger.warning(f"Invalid has_error value: {has_error}")

    # Create filter object
    filter_params = APIHistoryFilter(
        method=parsed_method,
        status_code=status_code,
        status_range=parsed_status_range,
        source=empty_str_to_none(source),
        user_id=empty_str_to_none(user_id),
        username=empty_str_to_none(username),
        path=empty_str_to_none(path),
        client_ip=empty_str_to_none(client_ip),
        start_date=parsed_start_date,
        end_date=parsed_end_date,
        min_duration_ms=min_duration_ms,
        max_duration_ms=max_duration_ms,
        has_error=parsed_has_error
    )

    try:
        debug_logger.debug("Get API Call History List")

        result = await service.get_history_records(db, filter_params, offset, limit)

        Logger.info(f"queried API history: {len(result['records'])} records")

        return APIHistoryResponse(
            records=result["records"],
            total_count=result["total_count"],
            offset=result["offset"],
            limit=result["limit"],
            has_more=result["has_more"]
        )

    except Exception as e:
        Logger.error(f"Error getting API history: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving API history")


@router.get("/api-history/{record_id}", response_model=APIHistoryDetailRecord)
async def get_api_history_detail(
    record_id: str = Path(..., description="API history record ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get detailed information for a specific API history record"""

    service = APIHistoryService()

    try:
        record = await service.get_record_by_id(db, record_id)

        if not record:
            raise HTTPException(status_code=404, detail="API history record not found")

        Logger.info(f"Admin {current_user.username} viewed API history detail: {record_id}")

        # Helper function to parse JSON string fields
        def parse_json_field(field_value):
            if field_value is None:
                return None
            if isinstance(field_value, str):
                try:
                    import json
                    return json.loads(field_value)
                except (json.JSONDecodeError, ValueError):
                    return None
            return field_value

        # Convert to detailed record with all fields
        return APIHistoryDetailRecord(
            id=str(record.id),
            method=record.method,
            path=record.path,
            full_url=record.full_url,
            query_params=parse_json_field(record.query_params),
            client_ip=record.client_ip,
            user_agent=record.user_agent,
            referer=record.referer,
            user_id=str(record.user_id) if record.user_id else None,
            username=record.username,
            is_admin=record.is_admin,
            request_headers=parse_json_field(record.request_headers),
            request_body=parse_json_field(record.request_body),
            request_size=record.request_size,
            status_code=record.status_code,
            response_headers=parse_json_field(record.response_headers),
            response_body=parse_json_field(record.response_body),
            response_size=record.response_size,
            start_time=record.start_time,
            end_time=record.end_time,
            duration_ms=record.duration_ms,
            duration_seconds=record.duration_seconds,
            endpoint_name=record.endpoint_name,
            source=record.source,
            correlation_id=record.correlation_id,
            error_message=record.error_message,
            stack_trace=record.stack_trace,
            is_success=record.is_success,
            is_client_error=record.is_client_error,
            is_server_error=record.is_server_error,
            created_at=record.created_at
        )

    except HTTPException:
        raise
    except Exception as e:
        Logger.error(f"Error getting API history detail: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving API history detail")


@router.get("/api-history-stats", response_model=APIHistoryStats)
async def get_api_history_stats(
    hours: int = Query(24, ge=1, le=8760, description="Hours to analyze (max 1 year)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get API history statistics for the specified time period"""

    service = APIHistoryService()

    try:
        stats = await service.get_history_stats(db, hours)

        Logger.info(f"Admin {current_user.username} requested API history stats for {hours} hours")

        return stats

    except Exception as e:
        Logger.error(f"Error getting API history stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving API history statistics")


@router.post("/api-history/cleanup", response_model=APIHistoryCleanupResult)
async def cleanup_api_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Manually trigger cleanup of old API history records"""

    service = APIHistoryService()

    try:
        result = await service.cleanup_old_records(db)

        Logger.warning(f"Admin {current_user.username} manually triggered API history cleanup")

        return APIHistoryCleanupResult(
            deleted=result["deleted"],
            remaining=result["remaining"],
            cutoff_date=result["cutoff_date"]
        )

    except Exception as e:
        Logger.error(f"Error during manual API history cleanup: {str(e)}")
        raise HTTPException(status_code=500, detail="Error during cleanup operation")


@router.delete("/api-history/{record_id}")
async def delete_api_history_record(
    record_id: str = Path(..., description="API history record ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete a specific API history record"""

    service = APIHistoryService()

    try:
        deleted = await service.delete_record(db, record_id)

        if not deleted:
            raise HTTPException(status_code=404, detail="API history record not found")

        Logger.warning(f"Admin {current_user.username} deleted API history record: {record_id}")

        return {"message": "API history record deleted successfully", "id": record_id}

    except HTTPException:
        raise
    except Exception as e:
        Logger.error(f"Error deleting API history record: {str(e)}")
        raise HTTPException(status_code=500, detail="Error deleting API history record")


@router.get("/api-history-config", response_model=APIHistoryConfig)
async def get_api_history_config(
    current_user: User = Depends(get_current_admin_user)
):
    """Get current API history configuration"""

    from app.core.config import settings

    config = APIHistoryConfig(
        enabled=settings.API_HISTORY_ENABLED,
        retention_days=settings.API_HISTORY_RETENTION_DAYS,
        max_request_size=settings.API_HISTORY_MAX_REQUEST_SIZE,
        max_response_size=settings.API_HISTORY_MAX_RESPONSE_SIZE
    )

    Logger.info(f"Admin {current_user.username} requested API history configuration")

    return config


@router.get("/api-history/export/csv")
async def export_api_history_csv(
    start_date: Optional[str] = Query(None, description="Start date for export"),
    end_date: Optional[str] = Query(None, description="End date for export"),
    method: Optional[str] = Query(None, description="Filter by HTTP method"),
    status_range: Optional[str] = Query(None, description="Filter by status range"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Export API history as CSV (basic implementation)"""

    # This is a basic implementation - in production you might want to use
    # a more sophisticated CSV export with streaming for large datasets

    service = APIHistoryService()

    # Parse date strings to datetime objects
    parsed_start_date = None
    parsed_end_date = None

    if start_date and start_date.strip():
        try:
            parsed_start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            debug_logger.warning(f"Invalid start_date format: {start_date}")

    if end_date and end_date.strip():
        try:
            parsed_end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            debug_logger.warning(f"Invalid end_date format: {end_date}")

    # Convert string enum values to proper enum types, handling empty strings
    parsed_method = None
    if method and method.strip():
        try:
            parsed_method = HTTPMethod(method)
        except ValueError:
            debug_logger.warning(f"Invalid method: {method}")

    parsed_status_range = None
    if status_range and status_range.strip():
        try:
            parsed_status_range = StatusRange(status_range)
        except ValueError:
            debug_logger.warning(f"Invalid status_range: {status_range}")

    filter_params = APIHistoryFilter(
        method=parsed_method,
        status_range=parsed_status_range,
        start_date=parsed_start_date,
        end_date=parsed_end_date
    )

    try:
        # Get records (limit to prevent memory issues)
        result = await service.get_history_records(db, filter_params, 0, 10000)

        if not result["records"]:
            raise HTTPException(status_code=404, detail="No records found for export")

        # Generate CSV content
        import csv
        import io

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            'created_at', 'method', 'path', 'status_code', 'duration_ms',
            'client_ip', 'username', 'source', 'user_agent'
        ])

        writer.writeheader()
        for record in result["records"]:
            writer.writerow({
                'created_at': record['created_at'],
                'method': record['method'],
                'path': record['path'],
                'status_code': record['status_code'],
                'duration_ms': record['duration_ms'],
                'client_ip': record['client_ip'],
                'username': record['username'],
                'source': record['source'],
                'user_agent': record['user_agent']
            })

        csv_content = output.getvalue()
        output.close()

        Logger.info(f"Admin {current_user.username} exported {len(result['records'])} API history records")

        from fastapi.responses import Response

        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=api_history.csv"}
        )

    except HTTPException:
        raise
    except Exception as e:
        Logger.error(f"Error exporting API history: {str(e)}")
        raise HTTPException(status_code=500, detail="Error exporting API history")