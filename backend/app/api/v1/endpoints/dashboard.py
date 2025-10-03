from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import get_current_user, get_current_admin_user
from app.core.logging_config import Logger
from app.models.user import User
from app.services.dashboard_service import DashboardService
from app.schemas.dashboard import (
    DashboardStats, DashboardData, RecentActivity,
    SystemHealth, SystemConfiguration
)

router = APIRouter()


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive dashboard statistics"""

    service = DashboardService()

    try:
        stats = await service.get_dashboard_stats(db)

        Logger.info(f"User {current_user.username} requested dashboard stats")

        return stats

    except Exception as e:
        Logger.error(f"Error getting dashboard stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving dashboard statistics")


@router.get("/", response_model=DashboardData)
async def get_dashboard_data(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get complete dashboard data including stats and recent activities"""

    service = DashboardService()

    try:
        dashboard_data = await service.get_dashboard_data(db)

        Logger.info(f"User {current_user.username} requested complete dashboard data")

        return dashboard_data

    except Exception as e:
        Logger.error(f"Error getting dashboard data: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving dashboard data")


@router.get("/recent-activities", response_model=list[RecentActivity])
async def get_recent_activities(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get recent system activities"""

    service = DashboardService()

    try:
        activities = await service.get_recent_activities(db, limit)

        Logger.info(f"User {current_user.username} requested recent activities (limit: {limit})")

        return activities

    except Exception as e:
        Logger.error(f"Error getting recent activities: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving recent activities")


@router.get("/system-config", response_model=SystemConfiguration)
async def get_system_configuration(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get current system configuration (admin only)"""

    service = DashboardService()

    try:
        config = await service.get_system_configuration(db)

        Logger.info(f"Admin {current_user.username} requested system configuration")

        return config

    except Exception as e:
        Logger.error(f"Error getting system configuration: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving system configuration")


@router.get("/system-health", response_model=SystemHealth)
async def get_system_health(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get system health status (admin only)"""

    service = DashboardService()

    try:
        from datetime import datetime
        from app.schemas.dashboard import SystemHealthCheck

        # Get basic health status
        system_status, database_status, vector_db_status = await service._get_system_health_status(db)

        # Create detailed health checks
        checks = [
            SystemHealthCheck(
                service="Database",
                status=database_status,
                message="Database connectivity check",
                response_time_ms=10.5 if database_status == "healthy" else None
            ),
            SystemHealthCheck(
                service="Vector Database",
                status=vector_db_status,
                message="Vector database connectivity check",
                response_time_ms=25.3 if vector_db_status == "healthy" else None
            ),
            SystemHealthCheck(
                service="API Server",
                status="healthy",
                message="API server is responding",
                response_time_ms=5.2
            )
        ]

        health = SystemHealth(
            overall_status=system_status,
            checks=checks,
            timestamp=datetime.utcnow()
        )

        Logger.info(f"Admin {current_user.username} requested system health status")

        return health

    except Exception as e:
        Logger.error(f"Error getting system health: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving system health")