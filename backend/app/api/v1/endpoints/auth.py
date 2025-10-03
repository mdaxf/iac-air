from typing import List, Optional
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import get_current_active_user, get_current_admin_user
from app.services.auth_service import AuthService
from app.schemas.auth import (
    UserLogin, TokenResponse, UserProfile, ChangePasswordRequest,
    UserSessionInfo, UserActivityLog, ActivityLogQuery
)
from app.models.user import User

from app.core.logging_config  import Logger,app_logger

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    login_data: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """Authenticate user and return JWT token"""
    
    app_logger.debug(f"DEBUG: Authenticate user and return JWT token for {login_data}")

    auth_service = AuthService()

    # Authenticate user
    user = await auth_service.authenticate_user(db, login_data.username, login_data.password)
    if not user:
        # Log failed login attempt
        app_logger.debug(f"ERROR: User login failed with data {login_data}")
        await auth_service.log_user_activity(
            db=db,
            user_id=None,  # No user ID for failed login
            activity_type="login_failed",
            description=f"Failed login attempt for username: {login_data.username}",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            metadata={"username": login_data.username}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    app_logger.debug(f"DEBUG: Create access token for the user {user.username}")
    # Create access token
    if login_data.remember_me:
        access_token_expires = timedelta(days=30)
    else:
        access_token_expires = timedelta(minutes=auth_service.access_token_expire_minutes)

    access_token = auth_service.create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )

    # Extract JWT ID for session management
    token_payload = auth_service.verify_token(access_token)
    token_jti = token_payload.get("jti") if token_payload else None

    # Create user session
    app_logger.debug(f"DEBUG: Create user session for user {user.username}")
    if token_jti:
        await auth_service.create_user_session(
            db=db,
            user=user,
            token_jti=token_jti,
            device_info=f"Web Browser",  # Could be enhanced with device detection
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            remember_me=login_data.remember_me
        )

    # Log successful login
    app_logger.debug(f"DEBUG: User {user.username} login success!")
    await auth_service.log_user_activity(
        db=db,
        user_id=user.id,
        activity_type="login_success",
        description="User logged in successfully",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )

    # Return token and user profile
    user_profile = await auth_service.get_user_profile_with_databases(db, user)
    expires_in = int(access_token_expires.total_seconds())

    app_logger.debug(f"DEBUG: Return the user's profile & token!")
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in,
        user=user_profile
    )


@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Logout current user"""
    auth_service = AuthService()

    # Extract token from authorization header
    authorization = request.headers.get("authorization", "")
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else ""

    if token:
        await auth_service.logout_user(db, token)

    # Log logout
    await auth_service.log_user_activity(
        db=db,
        user_id=current_user.id,
        activity_type="logout",
        description="User logged out",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )

    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user profile"""
    auth_service = AuthService()
    return await auth_service.get_user_profile_with_databases(db, current_user)


@router.put("/me", response_model=UserProfile)
async def update_current_user_profile(
    profile_data: dict,  # Using dict for now, could be more specific schema
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user profile"""
    # Update allowed fields
    allowed_fields = ["full_name", "department", "job_title", "phone", "preferences"]

    for field, value in profile_data.items():
        if field in allowed_fields and hasattr(current_user, field):
            setattr(current_user, field, value)

    await db.commit()
    await db.refresh(current_user)

    auth_service = AuthService()
    return await auth_service.get_user_profile_with_databases(db, current_user)


@router.post("/change-password")
async def change_password(
    request: Request,
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Change current user password"""
    auth_service = AuthService()

    success = await auth_service.change_password(
        db=db,
        user_id=current_user.id,
        current_password=password_data.current_password,
        new_password=password_data.new_password
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # Log password change
    await auth_service.log_user_activity(
        db=db,
        user_id=current_user.id,
        activity_type="password_change",
        description="User changed password",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )

    return {"message": "Password changed successfully"}


@router.get("/sessions", response_model=List[UserSessionInfo])
async def get_user_sessions(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's active sessions"""
    auth_service = AuthService()
    sessions = await auth_service.get_user_sessions(db, current_user.id)

    # Get current session token for comparison
    authorization = request.headers.get("authorization", "")
    current_token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else ""
    current_token_payload = auth_service.verify_token(current_token) if current_token else None
    current_jti = current_token_payload.get("jti") if current_token_payload else None

    session_infos = []
    for session in sessions:
        session_info = UserSessionInfo(
            id=session.id,
            device_info=session.device_info,
            ip_address=session.ip_address,
            user_agent=session.user_agent,
            created_at=session.created_at,
            last_activity=session.last_activity,
            expires_at=session.expires_at,
            is_current=session.token_jti == current_jti
        )
        session_infos.append(session_info)

    return session_infos


@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Revoke a specific session"""
    auth_service = AuthService()

    try:
        from uuid import UUID
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session ID format"
        )

    success = await auth_service.revoke_user_session(db, session_uuid, current_user.id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    return {"message": "Session revoked successfully"}


@router.get("/activity", response_model=List[UserActivityLog])
async def get_user_activity(
    current_user: User = Depends(get_current_active_user),
    limit: int = 50,
    offset: int = 0,
    activity_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get current user's activity log"""
    from sqlalchemy import select, and_
    from app.models.user import UserActivity

    # Build query
    conditions = [UserActivity.user_id == current_user.id]
    if activity_type:
        conditions.append(UserActivity.activity_type == activity_type)

    query = select(UserActivity).where(and_(*conditions)).order_by(
        UserActivity.created_at.desc()
    ).offset(offset).limit(limit)

    result = await db.execute(query)
    activities = result.scalars().all()

    return [
        UserActivityLog(
            id=activity.id,
            activity_type=activity.activity_type,
            description=activity.description,
            ip_address=activity.ip_address,
            metadata=activity.metadata,
            created_at=activity.created_at
        )
        for activity in activities
    ]


@router.get("/verify-token")
async def verify_token(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Verify token validity (used by frontend to check auth status)"""
    auth_service = AuthService()
    return {
        "valid": True,
        "user": await auth_service.get_user_profile_with_databases(db, current_user)
    }