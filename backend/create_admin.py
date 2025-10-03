#!/usr/bin/env python3
"""
Create an initial admin user for the application.
"""
import asyncio
import sys
import os
import uuid
from datetime import datetime

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text
from passlib.context import CryptContext

from app.models.user import User
from app.core.config import settings
from app.core.database import Base

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

async def create_admin_user():
    """Create an initial admin user"""

    # Create async engine
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=True
    )

    # Create async session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        try:
            # Check if admin user already exists
            result = await session.execute(
                select(User.id).where((User.username == 'admin') | (User.is_admin == True)).limit(1)
            )
            existing_user = result.fetchone()

            if existing_user:
                print("Admin user already exists!")
                return

            # Create admin user
            admin_user = User(
                id=uuid.uuid4(),
                username="admin",
                email="admin@localhost",
                full_name="Administrator",
                hashed_password=hash_password("admin123"),
                is_active=True,
                is_admin=True,
                created_at=datetime.utcnow()
            )

            session.add(admin_user)
            await session.commit()

            print("✓ Admin user created successfully!")
            print("Username: admin")
            print("Password: admin123")
            print("Please change the password after first login.")

        except Exception as e:
            print(f"Error creating admin user: {e}")
            await session.rollback()
        finally:
            await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_admin_user())