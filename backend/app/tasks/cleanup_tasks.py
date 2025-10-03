import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.logging_config import Logger
from app.services.api_history_service import APIHistoryService


class CleanupTasks:
    """Background cleanup tasks"""

    def __init__(self):
        self.api_history_service = APIHistoryService()

    async def cleanup_api_history(self):
        """Clean up old API history records"""
        try:
            async with get_db_session() as db:
                result = await self.api_history_service.cleanup_old_records(db)
                Logger.info(f"API history cleanup completed: {result}")
                return result
        except Exception as e:
            Logger.error(f"Error in API history cleanup task: {str(e)}")
            raise

    async def run_daily_cleanup(self):
        """Run all daily cleanup tasks"""
        Logger.info("Starting daily cleanup tasks")

        try:
            # Cleanup API history
            api_result = await self.cleanup_api_history()

            Logger.info(f"Daily cleanup completed successfully. API history: {api_result}")
            return {
                "success": True,
                "api_history": api_result,
                "completed_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            Logger.error(f"Error during daily cleanup: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "completed_at": datetime.utcnow().isoformat()
            }


# Global instance
cleanup_tasks = CleanupTasks()


async def schedule_cleanup_tasks():
    """Schedule cleanup tasks to run periodically"""
    while True:
        try:
            # Calculate time until next midnight
            now = datetime.utcnow()
            tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            sleep_seconds = (tomorrow - now).total_seconds()

            Logger.info(f"Scheduled next cleanup in {sleep_seconds/3600:.1f} hours")

            # Sleep until midnight
            await asyncio.sleep(sleep_seconds)

            # Run cleanup
            await cleanup_tasks.run_daily_cleanup()

        except Exception as e:
            Logger.error(f"Error in cleanup scheduler: {str(e)}")
            # Sleep for an hour before retrying
            await asyncio.sleep(3600)