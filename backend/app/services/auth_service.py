from typing import Optional, Dict, Any, List
import secrets
import string
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
import uuid

from app.core.config import settings
from app.core.logging_config import Logger, log_method_calls, debug_logger
from app.models.user import User, UserSession, UserActivity
from app.schemas.auth import UserCreateRequest, UserProfile, UserLogin, TokenResponse


class AuthService:
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES

    @log_method_calls
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a plain password against its hash"""
        return self.pwd_context.verify(plain_password, hashed_password)

    @log_method_calls
    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        return self.pwd_context.hash(password)

    @log_method_calls
    def generate_random_password(self, length: int = 12) -> str:
        """Generate a random password"""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        return password

    @log_method_calls
    async def authenticate_user(self, db: AsyncSession, username: str, password: str) -> Optional[User]:
        """Authenticate user by username/email and password"""
        # Try to find user by username or email
        query = select(User).where(
            and_(
                or_(User.username == username, User.email == username),
                User.is_active == True
            )
        )
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if user and self.verify_password(password, user.hashed_password):
            # Update last login
            user.last_login = datetime.utcnow()
            await db.commit()
            Logger.security(f"Successful login for user: {user.username}")
            return user

        Logger.security(f"Failed login attempt for username: {username}")
        return None

    @log_method_calls
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)

        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "jti": str(uuid.uuid4())  # JWT ID for session management
        })
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    @log_method_calls
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            Logger.warning("Failed to verify JWT token")
            return None

    @log_method_calls
    async def create_user_session(
        self,
        db: AsyncSession,
        user: User,
        token_jti: str,
        device_info: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        remember_me: bool = False
    ) -> UserSession:
        """Create a user session record"""
        expires_delta = timedelta(days=30) if remember_me else timedelta(minutes=self.access_token_expire_minutes)
        expires_at = datetime.utcnow() + expires_delta

        session = UserSession(
            user_id=user.id,
            token_jti=token_jti,
            device_info=device_info,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires_at
        )

        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session

    @log_method_calls
    async def get_user_by_token(self, db: AsyncSession, token: str) -> Optional[User]:
        """Get user from JWT token"""
        debug_logger.debug(f"Get user from JWT token {token}")
        payload = self.verify_token(token)
        if not payload:
            debug_logger.debug(f"token is not a validate token")
            return None

        debug_logger.debug(f"token payload: {payload}")
        user_id = payload.get("sub")

        if not user_id:
            debug_logger.debug(f"There is no userid from token")
            return None

        debug_logger.debug(f"userid from token: {user_id}")
        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            return None

        # Check if session is still active
        token_jti = payload.get("jti")

        if token_jti:
            session_query = select(UserSession).where(
                and_(
                    UserSession.token_jti == token_jti,
                    UserSession.is_active == True,
                    UserSession.expires_at > datetime.utcnow()
                )
            )
            session_result = await db.execute(session_query)
            session = session_result.scalar_one_or_none()

            if not session:
                debug_logger.debug(f"Token is not a session ")
                return None

            # Update last activity
            session.last_activity = datetime.utcnow()
            await db.commit()

        # Get user with accessible_databases relationship loaded
        user_query = select(User).where(
            User.id == user_uuid
        #    and_(User.id == user_uuid, User.is_active == True)
        ).options(selectinload(User.accessible_databases))

        debug_logger.debug(f"Query to get user: {user_query}")
        result = await db.execute(user_query)
        user = result.scalar_one_or_none()
        user.id = user_uuid
        debug_logger.debug(f"query user by id: {user_uuid}, {user}")
        return user

    @log_method_calls
    async def logout_user(self, db: AsyncSession, token: str) -> bool:
        """Logout user by deactivating session"""
        payload = self.verify_token(token)
        if not payload:
            return False

        token_jti = payload.get("jti")
        if not token_jti:
            return False

        # Deactivate session
        query = select(UserSession).where(UserSession.token_jti == token_jti)
        result = await db.execute(query)
        session = result.scalar_one_or_none()

        if session:
            session.is_active = False
            await db.commit()
            return True

        return False

    @log_method_calls
    async def create_user(self, db: AsyncSession, user_data: UserCreateRequest) -> User:
        """Create a new user (admin only)"""
        # Check if username or email already exists
        existing_query = select(User).where(
            or_(User.username == user_data.username, User.email == user_data.email)
        )
        result = await db.execute(existing_query)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            if existing_user.username == user_data.username:
                raise ValueError("Username already exists")
            else:
                raise ValueError("Email already exists")

        # Create user
        hashed_password = self.get_password_hash(user_data.password)
        user = User(
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name,
            hashed_password=hashed_password,
            is_admin=user_data.is_admin,
            department=user_data.department,
            job_title=user_data.job_title,
            phone=user_data.phone
        )

        db.add(user)
        await db.commit()
        await db.refresh(user)

        # Set database access if provided
        if user_data.accessible_databases:
            await self.update_user_database_access(db, user.id, user_data.accessible_databases)

        return user

    @log_method_calls
    async def update_user_database_access(self, db: AsyncSession, user_id: uuid.UUID, database_aliases: List[str]) -> None:
        """Update user's database access permissions"""
        from app.models.database import DatabaseConnection
        from app.models.user import user_database_access
        from sqlalchemy import delete, insert

        # Verify user exists
        user_query = select(User).where(User.id == user_id)
        result = await db.execute(user_query)
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("User not found")

        # Delete existing access records
        delete_stmt = delete(user_database_access).where(user_database_access.c.user_id == user_id)
        await db.execute(delete_stmt)

        # Insert new access records if any databases specified
        if database_aliases:
            # Verify database connections exist
            db_query = select(DatabaseConnection.alias).where(DatabaseConnection.alias.in_(database_aliases))
            db_result = await db.execute(db_query)
            existing_aliases = db_result.scalars().all()

            # Insert new records
            for alias in existing_aliases:
                insert_stmt = insert(user_database_access).values(
                    user_id=user_id,
                    database_connection_id=alias
                )
                await db.execute(insert_stmt)

        await db.commit()

    @log_method_calls
    async def reset_user_password(self, db: AsyncSession, user_id: uuid.UUID, new_password: Optional[str] = None) -> str:
        """Reset user password (admin only)"""
        user_query = select(User).where(User.id == user_id)
        result = await db.execute(user_query)
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("User not found")

        if not new_password:
            new_password = self.generate_random_password()

        user.hashed_password = self.get_password_hash(new_password)

        # Invalidate all user sessions
        sessions_query = select(UserSession).where(UserSession.user_id == user_id)
        sessions_result = await db.execute(sessions_query)
        sessions = sessions_result.scalars().all()

        for session in sessions:
            session.is_active = False

        await db.commit()
        return new_password

    @log_method_calls
    async def change_password(self, db: AsyncSession, user_id: uuid.UUID, current_password: str, new_password: str) -> bool:
        """Change user password (user self-service)"""
        user_query = select(User).where(User.id == user_id)
        result = await db.execute(user_query)
        user = result.scalar_one_or_none()

        if not user:
            return False

        if not self.verify_password(current_password, user.hashed_password):
            return False

        user.hashed_password = self.get_password_hash(new_password)
        await db.commit()
        return True

    @log_method_calls
    async def log_user_activity(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        activity_type: str,
        description: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UserActivity:
        """Log user activity"""
        activity = UserActivity(
            user_id=user_id,
            activity_type=activity_type,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata or {}
        )

        db.add(activity)
        await db.commit()
        await db.refresh(activity)
        return activity


    @log_method_calls
    async def get_user_sessions(self, db: AsyncSession, user_id: uuid.UUID) -> List[UserSession]:
        """Get all active sessions for a user"""
        query = select(UserSession).where(
            and_(
                UserSession.user_id == user_id,
                UserSession.is_active == True,
                UserSession.expires_at > datetime.utcnow()
            )
        ).order_by(UserSession.last_activity.desc())

        result = await db.execute(query)
        return result.scalars().all()

    @log_method_calls
    async def revoke_user_session(self, db: AsyncSession, session_id: uuid.UUID, current_user_id: uuid.UUID) -> bool:
        """Revoke a specific user session"""
        query = select(UserSession).where(UserSession.id == session_id)
        result = await db.execute(query)
        session = result.scalar_one_or_none()

        if not session or session.user_id != current_user_id:
            return False

        session.is_active = False
        await db.commit()
        return True

    def get_user_profile(self, user: User) -> UserProfile:
        """Convert User model to UserProfile schema (sync version)"""
        # Try to get accessible databases if the relationship is loaded
        try:
            accessible_db_aliases = [db.alias for db in user.accessible_databases] if user.accessible_databases else []
        except Exception:
            # If relationship is not loaded, return empty list
            accessible_db_aliases = []

        return UserProfile(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            is_admin=user.is_admin,
            department=user.department,
            job_title=user.job_title,
            phone=user.phone,
            preferences=user.preferences,
            accessible_databases=accessible_db_aliases,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login
        )

    @log_method_calls
    async def get_user_profile_with_databases(self, db: AsyncSession, user: User) -> UserProfile:
        """Convert User model to UserProfile schema with database loading"""
        # Load accessible_databases relationship asynchronously
        # Refresh user with accessible_databases loaded
        user_query = select(User).where(User.id == user.id).options(selectinload(User.accessible_databases))
        result = await db.execute(user_query)
        user_with_dbs = result.scalar_one_or_none()

        if not user_with_dbs:
            user_with_dbs = user
            accessible_db_aliases = []
        else:
            accessible_db_aliases = [db.alias for db in user_with_dbs.accessible_databases] if user_with_dbs.accessible_databases else []

        return UserProfile(
            id=user_with_dbs.id,
            username=user_with_dbs.username,
            email=user_with_dbs.email,
            full_name=user_with_dbs.full_name,
            is_active=user_with_dbs.is_active,
            is_admin=user_with_dbs.is_admin,
            department=user_with_dbs.department,
            job_title=user_with_dbs.job_title,
            phone=user_with_dbs.phone,
            preferences=user_with_dbs.preferences,
            accessible_databases=accessible_db_aliases,
            created_at=user_with_dbs.created_at,
            updated_at=user_with_dbs.updated_at,
            last_login=user_with_dbs.last_login
        )