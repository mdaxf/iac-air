from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.auth_service import AuthService
from app.models.user import User
from app.core.logging_config import log_method_calls, Logger, log_performance,debug_logger

security = HTTPBearer()

@log_method_calls
async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    debug_logger.debug(f"Get current authenticated user")
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    auth_service = AuthService()
    user = await auth_service.get_user_by_token(db, credentials.credentials)

    if user is None:
        debug_logger.debug("No user from token")
        raise credentials_exception

    debug_logger.debug(f"Get user by token: {user}")

    # Log user activity for API calls
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    await auth_service.log_user_activity(
        db=db,
        user_id=user.id,
        activity_type="api_access",
        description=f"{request.method} {request.url.path}",
        ip_address=client_ip,
        user_agent=user_agent,
        metadata={
            "method": request.method,
            "path": str(request.url.path),
            "query_params": str(request.query_params)
        }
    )

    # Set user in request state for middleware access
    request.state.user = user

    return user

@log_method_calls
async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user"""
    debug_logger.debug(f"get_current_active_user: {current_user}")
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

@log_method_calls
async def get_current_admin_user(current_user: User = Depends(get_current_active_user)) -> User:
    """Get current admin user"""
    debug_logger.debug(f"Validate the user admin role {current_user}")
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

@log_method_calls
def get_optional_current_user():
    """Optional authentication dependency"""
    async def _get_optional_current_user(
        request: Request,
        db: AsyncSession = Depends(get_db)
    ) -> Optional[User]:
        try:
            # Try to get authorization header
            authorization = request.headers.get("authorization")
            if not authorization or not authorization.startswith("Bearer "):
                return None

            token = authorization.split(" ")[1]
            auth_service = AuthService()
            user = await auth_service.get_user_by_token(db, token)

            # Set user in request state for middleware access
            if user:
                request.state.user = user

            return user
        except Exception:
            return None

    return _get_optional_current_user

@log_method_calls
class DatabaseAccessChecker:
    """Check if user has access to specific database"""

    def __init__(self, db_alias: str):
        self.db_alias = db_alias

    async def __call__(self, current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.is_admin:
            # Admins have access to all databases
            return current_user

        # Check if user has access to the specific database
        try:
            user_db_aliases = [db.alias for db in current_user.accessible_databases] if current_user.accessible_databases else []
        except Exception:
            # If relationship is not loaded, assume no access (will be caught by admin check)
            user_db_aliases = []

        if self.db_alias not in user_db_aliases:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied to database '{self.db_alias}'"
            )

        return current_user

@log_method_calls
def require_database_access(db_alias: str):
    """Create a dependency that checks database access for a specific alias"""
    return DatabaseAccessChecker(db_alias)