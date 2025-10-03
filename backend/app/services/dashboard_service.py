from typing import List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, func

from app.models.api_history import APICallHistory
from app.models.user import User
from app.models.database import DatabaseConnection
from app.schemas.dashboard import DashboardStats, RecentActivity, DashboardData, SystemHealth, SystemHealthCheck, SystemConfiguration
from app.services.api_history_service import APIHistoryService
from app.core.logging_config import Logger


class DashboardService:
    """Service for aggregating dashboard data from various system components"""

    def __init__(self):
        self.api_history_service = APIHistoryService()

    async def get_dashboard_stats(self, db: AsyncSession) -> DashboardStats:
        """Aggregate all dashboard statistics from real system data"""

        # Get total databases count
        total_databases = await self._get_total_databases(db)

        # Get user statistics
        total_users, active_users_24h = await self._get_user_stats(db)

        # Get API statistics from API history
        api_stats = await self._get_api_stats(db)

        # Get conversation statistics
        conversations_24h, messages_24h, active_conversations = await self._get_conversation_stats(db)

        # Get indexed documents count from vector database
        total_indexed_documents = await self._get_indexed_documents_count(db)

        # Get system health status
        system_status, database_status, vector_db_status = await self._get_system_health_status(db)

        # Get recent activity count
        recent_activity_count = await self._get_recent_activity_count(db)

        return DashboardStats(
            total_databases=total_databases,
            active_conversations=active_conversations,
            total_indexed_documents=total_indexed_documents,
            total_users=total_users,
            active_users_24h=active_users_24h,
            api_requests_24h=api_stats["requests_24h"],
            api_errors_24h=api_stats["errors_24h"],
            api_error_rate=api_stats["error_rate"],
            avg_response_time_ms=api_stats["avg_response_time"],
            conversations_24h=conversations_24h,
            messages_24h=messages_24h,
            system_status=system_status,
            database_status=database_status,
            vector_db_status=vector_db_status,
            recent_activity_count=recent_activity_count
        )

    async def _get_total_databases(self, db: AsyncSession) -> int:
        """Get total number of connected databases"""
        try:
            result = await db.execute(text("SELECT COUNT(*) FROM database_connections WHERE is_active = true"))
            count = result.scalar()
            return count if count is not None else 0
        except Exception as e:
            Logger.error(f"Error getting total databases: {str(e)}")
            return 0

    async def _get_user_stats(self, db: AsyncSession) -> tuple[int, int]:
        """Get user statistics"""
        try:
            # Total users
            total_result = await db.execute(text("SELECT COUNT(*) FROM users"))
            total_users = total_result.scalar() or 0

            # Active users in last 24 hours (based on last_login or recent activity)
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            active_result = await db.execute(
                text("SELECT COUNT(*) FROM users WHERE last_login >= :cutoff"),
                {"cutoff": cutoff_time}
            )
            active_users_24h = active_result.scalar() or 0

            return total_users, active_users_24h
        except Exception as e:
            Logger.error(f"Error getting user stats: {str(e)}")
            return 0, 0

    async def _get_api_stats(self, db: AsyncSession) -> Dict[str, Any]:
        """Get API statistics from API history"""
        try:
            stats = await self.api_history_service.get_history_stats(db, 24)
            return {
                "requests_24h": stats.total_requests,
                "errors_24h": stats.error_count,
                "error_rate": stats.error_rate,
                "avg_response_time": stats.avg_response_time
            }
        except Exception as e:
            Logger.error(f"Error getting API stats: {str(e)}")
            return {
                "requests_24h": 0,
                "errors_24h": 0,
                "error_rate": 0.0,
                "avg_response_time": 0.0
            }

    async def _get_conversation_stats(self, db: AsyncSession) -> tuple[int, int, int]:
        """Get conversation and chat statistics"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=24)

            # Count conversations started in last 24 hours
            conversations_result = await db.execute(
                text("""
                    SELECT COUNT(DISTINCT correlation_id)
                    FROM api_call_history
                    WHERE path LIKE '%/chat%'
                    AND created_at >= :cutoff
                    AND correlation_id IS NOT NULL
                """),
                {"cutoff": cutoff_time}
            )
            conversations_24h = conversations_result.scalar() or 0

            # Count total messages (API calls to chat endpoints) in last 24 hours
            messages_result = await db.execute(
                text("""
                    SELECT COUNT(*)
                    FROM api_call_history
                    WHERE path LIKE '%/chat%'
                    AND created_at >= :cutoff
                    AND status_code < 400
                """),
                {"cutoff": cutoff_time}
            )
            messages_24h = messages_result.scalar() or 0

            # Count currently active conversations (conversations with activity in last hour)
            active_cutoff = datetime.utcnow() - timedelta(hours=1)
            active_result = await db.execute(
                text("""
                    SELECT COUNT(DISTINCT correlation_id)
                    FROM api_call_history
                    WHERE path LIKE '%/chat%'
                    AND created_at >= :cutoff
                    AND correlation_id IS NOT NULL
                """),
                {"cutoff": active_cutoff}
            )
            active_conversations = active_result.scalar() or 0

            return conversations_24h, messages_24h, active_conversations

        except Exception as e:
            Logger.error(f"Error getting conversation stats: {str(e)}")
            return 0, 0, 0

    async def _get_indexed_documents_count(self, db: AsyncSession) -> int:
        """Get total indexed documents count from vector database"""
        try:
            # This would typically query the vector database
            # For now, we'll estimate based on database content or use a stored metric
            # You might need to implement vector database query here

            # Placeholder implementation - in real system, query vector database
            # For example, if using Chroma, Pinecone, or Weaviate
            result = await db.execute(
                text("""
                    SELECT SUM(COALESCE(document_count, 0))
                    FROM databases
                    WHERE status = 'connected'
                """)
            )
            count = result.scalar()
            return count if count is not None else 0

        except Exception as e:
            Logger.error(f"Error getting indexed documents count: {str(e)}")
            return 0

    async def _get_system_health_status(self, db: AsyncSession) -> tuple[str, str, str]:
        """Get system health status"""
        try:
            # Check database connectivity
            try:
                await db.execute(text("SELECT 1"))
                database_status = "healthy"
            except Exception:
                database_status = "error"

            # Check vector database status (placeholder)
            vector_db_status = "healthy"  # Implement actual vector DB health check

            # Overall system status
            if database_status == "healthy" and vector_db_status == "healthy":
                system_status = "healthy"
            elif database_status == "error" or vector_db_status == "error":
                system_status = "error"
            else:
                system_status = "warning"

            return system_status, database_status, vector_db_status

        except Exception as e:
            Logger.error(f"Error getting system health: {str(e)}")
            return "error", "error", "error"

    async def _get_recent_activity_count(self, db: AsyncSession) -> int:
        """Get count of recent activities for summary"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            result = await db.execute(
                text("""
                    SELECT COUNT(*) FROM api_call_history
                    WHERE created_at >= :cutoff
                """),
                {"cutoff": cutoff_time}
            )
            return result.scalar() or 0
        except Exception as e:
            Logger.error(f"Error getting recent activity count: {str(e)}")
            return 0

    async def get_recent_activities(self, db: AsyncSession, limit: int = 20) -> List[RecentActivity]:
        """Get recent system activities from user_activities table"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=24)

            # Query recent user activities
            result = await db.execute(
                text("""
                    SELECT
                        ua.id,
                        ua.activity_type,
                        ua.description,
                        ua.user_id,
                        ua.ip_address,
                        ua.user_agent,
                        ua.extra_data,
                        ua.created_at,
                        u.username,
                        u.full_name
                    FROM user_activities ua
                    LEFT JOIN users u ON ua.user_id = u.id
                    WHERE ua.created_at >= :cutoff
                    ORDER BY ua.created_at DESC
                    LIMIT :limit
                """),
                {"cutoff": cutoff_time, "limit": limit}
            )

            activities = []
            for row in result:
                # Determine status based on activity type
                status = "success"  # Most user activities are successful
                if row.activity_type in ["login_failed", "error", "failed"]:
                    status = "error"
                elif row.activity_type in ["logout", "timeout"]:
                    status = "warning"

                # Create activity title
                title = self._create_user_activity_title(row)

                activity = RecentActivity(
                    id=str(row.id),
                    type=row.activity_type,
                    title=title,
                    description=row.description or "",
                    user_id=str(row.user_id) if row.user_id else None,
                    username=row.username or "Anonymous",
                    status=status,
                    timestamp=row.created_at,
                    metadata={
                        "ip_address": row.ip_address,
                        "user_agent": row.user_agent,
                        "extra_data": row.extra_data or {}
                    }
                )
                activities.append(activity)

            return activities

        except Exception as e:
            Logger.error(f"Error getting recent activities: {str(e)}")
            return []

    def _get_activity_type(self, path: str, method: str) -> str:
        """Determine activity type based on API path"""
        if "/auth" in path:
            return "user_login" if method == "POST" else "auth_action"
        elif "/chat" in path:
            return "chat_message" if method == "POST" else "chat_action"
        elif "/databases" in path:
            return "database_connection" if method == "POST" else "database_action"
        elif "/upload" in path or "/import" in path:
            return "file_import"
        elif "/users" in path:
            return "user_management"
        else:
            return "api_call"

    def _create_user_activity_title(self, row) -> str:
        """Create human-readable activity title from user activity"""
        username = row.username or "Anonymous"
        activity_type = row.activity_type

        # Map activity types to friendly titles
        activity_titles = {
            "login": f"User logged in",
            "logout": f"User logged out",
            "api_access": f"API access",
            "query_execution": f"Executed query",
            "file_upload": f"Uploaded file",
            "database_access": f"Accessed database",
            "export_data": f"Exported data",
            "user_created": f"Created user account",
            "user_updated": f"Updated user account",
            "password_change": f"Changed password",
            "settings_change": f"Updated settings",
        }

        return activity_titles.get(activity_type, f"{activity_type.replace('_', ' ').title()}")

    def _create_activity_description(self, row, activity_type: str) -> tuple[str, str]:
        """Create human-readable activity title and description"""
        username = row.username or "Anonymous"

        if activity_type == "chat_message":
            return f"Chat message from {username}", f"User sent a chat message"
        elif activity_type == "database_connection":
            return f"Database connection by {username}", f"User connected to a database"
        elif activity_type == "user_login":
            return f"User login: {username}", f"User logged into the system"
        elif activity_type == "file_import":
            return f"File import by {username}", f"User imported data or files"
        else:
            return f"API call: {row.method} {row.path}", f"User made API request to {row.path}"

    async def get_dashboard_data(self, db: AsyncSession) -> DashboardData:
        """Get complete dashboard data including stats and recent activities"""
        stats = await self.get_dashboard_stats(db)
        recent_activities = await self.get_recent_activities(db)

        return DashboardData(
            stats=stats,
            recent_activities=recent_activities
        )

    async def get_system_configuration(self, db: AsyncSession) -> SystemConfiguration:
        """Get current system configuration for admin page"""
        try:
            from app.core.config import settings

            return SystemConfiguration(
                llm_provider=getattr(settings, 'LLM_PROVIDER', 'openai'),
                embedding_model=getattr(settings, 'EMBEDDING_MODEL', 'text-embedding-ada-002'),
                vector_dimension=getattr(settings, 'VECTOR_DIMENSION', 1536),
                max_query_results=getattr(settings, 'MAX_QUERY_RESULTS', 1000),
                api_history_enabled=getattr(settings, 'API_HISTORY_ENABLED', True),
                api_history_retention_days=getattr(settings, 'API_HISTORY_RETENTION_DAYS', 30),
                log_level=getattr(settings, 'LOG_LEVEL', 'INFO'),
                environment=getattr(settings, 'ENVIRONMENT', 'development')
            )
        except Exception as e:
            Logger.error(f"Error getting system configuration: {str(e)}")
            # Return default configuration
            return SystemConfiguration(
                llm_provider="openai",
                embedding_model="text-embedding-ada-002",
                vector_dimension=1536,
                max_query_results=1000,
                api_history_enabled=True,
                api_history_retention_days=30,
                log_level="INFO",
                environment="development"
            )