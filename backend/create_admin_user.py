#!/usr/bin/env python3
"""
Simple script to create an admin user for the AIR Analytics platform.
Run this once to bootstrap the application with an initial admin user.
"""

import asyncio
import sys
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

# Add the app directory to Python path
sys.path.append('.')

from app.core.config import settings
from app.models.user import User

async def create_admin_user():
    # Create database connection
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Initialize password hashing
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    async with async_session() as session:
        # Check if any admin users exist
        result = await session.execute(
            select(User).where(User.is_admin == True).limit(1)
        )
        existing_admin = result.scalar_one_or_none()

        if existing_admin:
            print(f"Admin user already exists: {existing_admin.username} ({existing_admin.email})")
            return

        # Create admin user
        admin_username = "admin"
        admin_email = "admin@example.com"
        admin_password = "admin123"  # Change this in production!

        # Check if username already exists
        result = await session.execute(
            select(User).where(User.username == admin_username)
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print(f"User {admin_username} already exists")
            return

        # Hash password
        hashed_password = pwd_context.hash(admin_password)

        # Create the admin user
        admin_user = User(
            username=admin_username,
            email=admin_email,
            full_name="System Administrator",
            hashed_password=hashed_password,
            is_active=True,
            is_admin=True
        )

        session.add(admin_user)
        await session.commit()
        await session.refresh(admin_user)

        print(f"""
Admin user created successfully!

Username: {admin_username}
Email: {admin_email}
Password: {admin_password}

⚠️  IMPORTANT: Change the default password after first login!

You can now login at the frontend using these credentials.
        """)

if __name__ == "__main__":
    asyncio.run(create_admin_user())