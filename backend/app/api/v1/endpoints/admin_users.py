from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload
import uuid

from app.core.database import get_db
from app.core.auth import get_current_admin_user
from app.services.auth_service import AuthService
from app.schemas.auth import (
    UserCreateRequest, UserUpdateRequest, UserListResponse, UserProfile,
    AdminPasswordResetRequest, UserDatabaseAccessUpdate
)
from app.models.user import User, UserActivity
from app.models.database import DatabaseConnection
from app.core.logging_config import log_method_calls, Logger, log_performance

router = APIRouter()


@router.get("/users", response_model=List[UserListResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    is_admin: Optional[bool] = None,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """List all users (admin only)"""
    # Build query with filters
    conditions = []

    if search:
        search_pattern = f"%{search}%"
        conditions.append(
            or_(
                User.username.ilike(search_pattern),
                User.email.ilike(search_pattern),
                User.full_name.ilike(search_pattern)
            )
        )

    if is_active is not None:
        conditions.append(User.is_active == is_active)

    if is_admin is not None:
        conditions.append(User.is_admin == is_admin)

    query = select(User).options(selectinload(User.accessible_databases))
    if conditions:
        query = query.where(and_(*conditions))

    query = query.order_by(User.created_at.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    users = result.scalars().all()

    # Convert to response format
    user_list = []
    for user in users:
        user_data = UserListResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            is_admin=user.is_admin,
            department=user.department,
            job_title=user.job_title,
            accessible_databases_count=len(user.accessible_databases) if user.accessible_databases else 0,
            created_at=user.created_at,
            last_login=user.last_login
        )
        user_list.append(user_data)

    return user_list


@router.post("/users", response_model=UserProfile)
async def create_user(
    request: Request,
    user_data: UserCreateRequest,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new user (admin only)"""
    auth_service = AuthService()

    try:
        new_user = await auth_service.create_user(db, user_data)

        # Log admin activity
        await auth_service.log_user_activity(
            db=db,
            user_id=current_admin.id,
            activity_type="user_create",
            description=f"Created user: {new_user.username}",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            metadata={
                "created_user_id": str(new_user.id),
                "created_username": new_user.username
            }
        )

        return auth_service.get_user_profile(new_user)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/users/{user_id}", response_model=UserProfile)
async def get_user(
    user_id: str,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user details (admin only)"""
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )

    query = select(User).where(User.id == user_uuid).options(selectinload(User.accessible_databases))
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    auth_service = AuthService()
    return auth_service.get_user_profile(user)


@router.put("/users/{user_id}", response_model=UserProfile)
async def update_user(
    user_id: str,
    request: Request,
    user_data: UserUpdateRequest,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user (admin only)"""
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )

    query = select(User).where(User.id == user_uuid)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Update user fields
    update_data = user_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field == "accessible_databases":
            continue  # Handle separately
        if hasattr(user, field):
            setattr(user, field, value)

    # Update database access if provided
    if user_data.accessible_databases is not None:
        auth_service = AuthService()
        await auth_service.update_user_database_access(db, user_uuid, user_data.accessible_databases)

    await db.commit()

    # Reload user with accessible_databases relationship
    user_query = select(User).where(User.id == user_uuid).options(selectinload(User.accessible_databases))
    result = await db.execute(user_query)
    updated_user = result.scalar_one_or_none()

    # Log admin activity
    auth_service = AuthService()
    await auth_service.log_user_activity(
        db=db,
        user_id=current_admin.id,
        activity_type="user_update",
        description=f"Updated user: {updated_user.username}",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        metadata={
            "updated_user_id": str(updated_user.id),
            "updated_fields": list(update_data.keys())
        }
    )

    return auth_service.get_user_profile(updated_user)


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    request: Request,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete user (admin only)"""
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )

    # Prevent admin from deleting themselves
    if user_uuid == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )

    query = select(User).where(User.id == user_uuid)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    username = user.username  # Store for logging

    # Delete user
    await db.delete(user)
    await db.commit()

    # Log admin activity
    auth_service = AuthService()
    await auth_service.log_user_activity(
        db=db,
        user_id=current_admin.id,
        activity_type="user_delete",
        description=f"Deleted user: {username}",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        metadata={
            "deleted_user_id": str(user_uuid),
            "deleted_username": username
        }
    )

    return {"message": f"User {username} deleted successfully"}


@router.post("/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: str,
    request: Request,
    reset_data: AdminPasswordResetRequest,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Reset user password (admin only)"""
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )

    auth_service = AuthService()

    try:
        new_password = await auth_service.reset_user_password(
            db=db,
            user_id=user_uuid,
            new_password=reset_data.new_password
        )

        # Get user for logging
        user_query = select(User).where(User.id == user_uuid)
        user_result = await db.execute(user_query)
        user = user_result.scalar_one_or_none()

        # Log admin activity
        await auth_service.log_user_activity(
            db=db,
            user_id=current_admin.id,
            activity_type="password_reset",
            description=f"Reset password for user: {user.username if user else 'unknown'}",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            metadata={
                "target_user_id": str(user_uuid),
                "password_generated": reset_data.new_password is None
            }
        )

        return {
            "message": "Password reset successfully",
            "new_password": new_password if reset_data.new_password is None else None
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.put("/users/{user_id}/database-access")
async def update_user_database_access(
    user_id: str,
    request: Request,
    access_data: UserDatabaseAccessUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user database access (admin only)"""
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )

    auth_service = AuthService()

    try:
        await auth_service.update_user_database_access(
            db=db,
            user_id=user_uuid,
            database_aliases=access_data.database_aliases
        )

        # Get user for logging
        user_query = select(User).where(User.id == user_uuid)
        user_result = await db.execute(user_query)
        user = user_result.scalar_one_or_none()

        # Log admin activity
        await auth_service.log_user_activity(
            db=db,
            user_id=current_admin.id,
            activity_type="database_access_update",
            description=f"Updated database access for user: {user.username if user else 'unknown'}",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            metadata={
                "target_user_id": str(user_uuid),
                "granted_databases": access_data.database_aliases
            }
        )

        return {"message": "Database access updated successfully"}

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/activity-logs", response_model=List[dict])
async def get_system_activity_logs(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[str] = None,
    activity_type: Optional[str] = None,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get system activity logs (admin only)"""
    conditions = []

    if user_id:
        try:
            user_uuid = uuid.UUID(user_id)
            conditions.append(UserActivity.user_id == user_uuid)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user ID format"
            )

    if activity_type:
        conditions.append(UserActivity.activity_type == activity_type)

    query = select(UserActivity, User.username).join(
        User, UserActivity.user_id == User.id, isouter=True
    )

    if conditions:
        query = query.where(and_(*conditions))

    query = query.order_by(UserActivity.created_at.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    activities = result.all()

    activity_logs = []
    for activity, username in activities:
        activity_logs.append({
            "id": str(activity.id),
            "user_id": str(activity.user_id) if activity.user_id else None,
            "username": username,
            "activity_type": activity.activity_type,
            "description": activity.description,
            "ip_address": activity.ip_address,
            "user_agent": activity.user_agent,
            "metadata": activity.metadata,
            "created_at": activity.created_at
        })

    return activity_logs


@router.get("/stats")
async def get_user_stats(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user statistics (admin only)"""
    # Total users
    total_users_query = select(func.count(User.id))
    total_users_result = await db.execute(total_users_query)
    total_users = total_users_result.scalar()

    # Active users
    active_users_query = select(func.count(User.id)).where(User.is_active == True)
    active_users_result = await db.execute(active_users_query)
    active_users = active_users_result.scalar()

    # Admin users
    admin_users_query = select(func.count(User.id)).where(User.is_admin == True)
    admin_users_result = await db.execute(admin_users_query)
    admin_users = admin_users_result.scalar()

    # Users created in last 30 days
    from datetime import datetime, timedelta
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_users_query = select(func.count(User.id)).where(User.created_at >= thirty_days_ago)
    recent_users_result = await db.execute(recent_users_query)
    recent_users = recent_users_result.scalar()

    return {
        "total_users": total_users,
        "active_users": active_users,
        "inactive_users": total_users - active_users,
        "admin_users": admin_users,
        "recent_users_30d": recent_users
    }