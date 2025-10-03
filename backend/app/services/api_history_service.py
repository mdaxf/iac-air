from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func, and_, or_
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.logging_config import Logger, log_method_calls, debug_logger
from app.models.api_history import APICallHistory
from app.schemas.api_history import APIHistoryFilter, APIHistoryStats


class APIHistoryService:
    """Service for managing API call history"""

    @log_method_calls
    async def cleanup_old_records(self, db: AsyncSession) -> Dict[str, int]:
        """Delete API history records older than retention period"""
        cutoff_date = datetime.utcnow() - timedelta(days=settings.API_HISTORY_RETENTION_DAYS)

        try:
            # Count records to be deleted
            count_query = select(func.count(APICallHistory.id)).where(
                APICallHistory.created_at < cutoff_date
            )
            result = await db.execute(count_query)
            records_to_delete = result.scalar() or 0

            if records_to_delete == 0:
                Logger.info("No old API history records to cleanup")
                return {"deleted": 0, "remaining": await self._count_total_records(db)}

            # Delete old records in batches to avoid locking the table too long
            batch_size = 1000
            total_deleted = 0

            while True:
                # Delete a batch
                delete_query = delete(APICallHistory).where(
                    APICallHistory.id.in_(
                        select(APICallHistory.id)
                        .where(APICallHistory.created_at < cutoff_date)
                        .limit(batch_size)
                    )
                )

                result = await db.execute(delete_query)
                batch_deleted = result.rowcount

                if batch_deleted == 0:
                    break

                total_deleted += batch_deleted
                await db.commit()

                Logger.debug(f"Deleted batch of {batch_deleted} old API history records")

                # If we deleted less than the batch size, we're done
                if batch_deleted < batch_size:
                    break

            remaining_records = await self._count_total_records(db)

            Logger.info(
                f"API history cleanup completed: deleted {total_deleted} records, "
                f"{remaining_records} records remaining"
            )

            return {
                "deleted": total_deleted,
                "remaining": remaining_records,
                "cutoff_date": cutoff_date.isoformat()
            }

        except Exception as e:
            Logger.error(f"Error during API history cleanup: {str(e)}")
            await db.rollback()
            raise

    @log_method_calls
    async def get_history_records(
        self,
        db: AsyncSession,
        filter_params: APIHistoryFilter,
        offset: int = 0,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Get API history records with filtering and pagination"""
        debug_logger.debug(f"Get API history records with filtering and pagination {offset} {limit}")
        # Build base query
        query = select(APICallHistory)

        # Apply filters
        conditions = []

        if filter_params.method:
            conditions.append(APICallHistory.method == filter_params.method.upper())

        if filter_params.status_code:
            conditions.append(APICallHistory.status_code == filter_params.status_code)

        if filter_params.status_range:
            if filter_params.status_range == "2xx":
                conditions.append(and_(APICallHistory.status_code >= 200, APICallHistory.status_code < 300))
            elif filter_params.status_range == "4xx":
                conditions.append(and_(APICallHistory.status_code >= 400, APICallHistory.status_code < 500))
            elif filter_params.status_range == "5xx":
                conditions.append(and_(APICallHistory.status_code >= 500, APICallHistory.status_code < 600))

        if filter_params.source:
            conditions.append(APICallHistory.source == filter_params.source)

        if filter_params.user_id:
            conditions.append(APICallHistory.user_id == filter_params.user_id)

        if filter_params.username:
            conditions.append(APICallHistory.username.ilike(f"%{filter_params.username}%"))

        if filter_params.path:
            conditions.append(APICallHistory.path.ilike(f"%{filter_params.path}%"))

        if filter_params.client_ip:
            conditions.append(APICallHistory.client_ip == filter_params.client_ip)

        if filter_params.start_date:
            conditions.append(APICallHistory.created_at >= filter_params.start_date)

        if filter_params.end_date:
            conditions.append(APICallHistory.created_at <= filter_params.end_date)

        if filter_params.min_duration_ms:
            conditions.append(APICallHistory.duration_ms >= filter_params.min_duration_ms)

        if filter_params.max_duration_ms:
            conditions.append(APICallHistory.duration_ms <= filter_params.max_duration_ms)

        if filter_params.has_error:
            if filter_params.has_error:
                conditions.append(APICallHistory.error_message.isnot(None))
            else:
                conditions.append(APICallHistory.error_message.is_(None))

        # Apply all conditions
        if conditions:
            query = query.where(and_(*conditions))

        # Get total count for pagination
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total_count = total_result.scalar() or 0

        debug_logger.debug(f"Summary: {count_query}, {total_result}, {total_count}")
        # Apply sorting (most recent first by default)
        query = query.order_by(APICallHistory.created_at.desc())

        # Apply pagination
        query = query.offset(offset).limit(limit)
        debug_logger.debug(f"API History query {query}")
        # Execute query
        result = await db.execute(query)
        records = result.scalars().all()

        debug_logger.debug(f"Query result: {records}")
        return {
            "records": [record.to_dict() for record in records],
            "total_count": total_count,
            "offset": offset,
            "limit": limit,
            "has_more": (offset + limit) < total_count
        }

    @log_method_calls
    async def get_history_stats(
        self,
        db: AsyncSession,
        hours: int = 24
    ) -> APIHistoryStats:
        """Get API history statistics for the specified time period"""

        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        # Base query for the time period
        base_query = select(APICallHistory).where(APICallHistory.created_at >= cutoff_time)

        # Total requests
        total_result = await db.execute(
            select(func.count()).select_from(base_query.subquery())
        )
        total_requests = total_result.scalar() or 0

        # Status code breakdown
        status_breakdown = {}
        status_result = await db.execute(
            select(APICallHistory.status_code, func.count(APICallHistory.status_code))
            .where(APICallHistory.created_at >= cutoff_time)
            .group_by(APICallHistory.status_code)
        )
        for status_code, count in status_result.fetchall():
            status_breakdown[str(status_code)] = count

        # Method breakdown
        method_breakdown = {}
        method_result = await db.execute(
            select(APICallHistory.method, func.count(APICallHistory.method))
            .where(APICallHistory.created_at >= cutoff_time)
            .group_by(APICallHistory.method)
        )
        for method, count in method_result.fetchall():
            method_breakdown[method] = count

        # Source breakdown
        source_breakdown = {}
        source_result = await db.execute(
            select(APICallHistory.source, func.count(APICallHistory.source))
            .where(APICallHistory.created_at >= cutoff_time)
            .group_by(APICallHistory.source)
        )
        for source, count in source_result.fetchall():
            if source:
                source_breakdown[source] = count

        # Performance stats
        perf_result = await db.execute(
            select(
                func.avg(APICallHistory.duration_ms),
                func.min(APICallHistory.duration_ms),
                func.max(APICallHistory.duration_ms)
            )
            .where(and_(
                APICallHistory.created_at >= cutoff_time,
                APICallHistory.duration_ms.isnot(None)
            ))
        )
        avg_duration, min_duration, max_duration = perf_result.fetchone()

        # Error count
        error_result = await db.execute(
            select(func.count())
            .where(and_(
                APICallHistory.created_at >= cutoff_time,
                APICallHistory.error_message.isnot(None)
            ))
        )
        error_count = error_result.scalar() or 0

        # Top paths
        top_paths_result = await db.execute(
            select(APICallHistory.path, func.count(APICallHistory.path))
            .where(APICallHistory.created_at >= cutoff_time)
            .group_by(APICallHistory.path)
            .order_by(func.count(APICallHistory.path).desc())
            .limit(10)
        )
        top_paths = [{"path": path, "count": count} for path, count in top_paths_result.fetchall()]

        # Active users
        active_users_result = await db.execute(
            select(func.count(func.distinct(APICallHistory.user_id)))
            .where(and_(
                APICallHistory.created_at >= cutoff_time,
                APICallHistory.user_id.isnot(None)
            ))
        )
        active_users = active_users_result.scalar() or 0

        return APIHistoryStats(
            period_hours=hours,
            total_requests=total_requests,
            status_breakdown=status_breakdown,
            method_breakdown=method_breakdown,
            source_breakdown=source_breakdown,
            avg_duration_ms=float(avg_duration) if avg_duration else 0.0,
            min_duration_ms=float(min_duration) if min_duration else 0.0,
            max_duration_ms=float(max_duration) if max_duration else 0.0,
            error_count=error_count,
            error_rate=error_count / total_requests if total_requests > 0 else 0.0,
            top_paths=top_paths,
            active_users=active_users
        )

    @log_method_calls
    async def get_record_by_id(self, db: AsyncSession, record_id: str) -> Optional[APICallHistory]:
        """Get a specific API history record by ID"""
        query = select(APICallHistory).where(APICallHistory.id == record_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @log_method_calls
    async def delete_record(self, db: AsyncSession, record_id: str) -> bool:
        """Delete a specific API history record"""
        try:
            delete_query = delete(APICallHistory).where(APICallHistory.id == record_id)
            result = await db.execute(delete_query)
            await db.commit()

            deleted = result.rowcount > 0
            if deleted:
                Logger.info(f"Deleted API history record: {record_id}")

            return deleted
        except Exception as e:
            Logger.error(f"Error deleting API history record {record_id}: {str(e)}")
            await db.rollback()
            raise

    async def _count_total_records(self, db: AsyncSession) -> int:
        """Count total number of API history records"""
        result = await db.execute(select(func.count(APICallHistory.id)))
        return result.scalar() or 0