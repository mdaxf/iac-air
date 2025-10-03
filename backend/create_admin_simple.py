#!/usr/bin/env python3
"""
Create an initial admin user using direct SQL.
"""
import asyncio
import sys
import os
import uuid
from datetime import datetime
import asyncpg
from passlib.context import CryptContext

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

async def create_admin_user():
    """Create an initial admin user using direct SQL"""

    # Default database connection (adjust if needed)
    DATABASE_URL = "postgresql://postgres:password@localhost:5432/air_analytics"

    try:
        # Connect to database
        conn = await asyncpg.connect(DATABASE_URL)

        # Check if admin user already exists
        existing_user = await conn.fetchrow(
            "SELECT id FROM users WHERE username = 'admin' OR is_admin = true LIMIT 1"
        )

        if existing_user:
            print("Admin user already exists!")
            return

        # Create admin user
        user_id = str(uuid.uuid4())
        hashed_pwd = hash_password("admin123")
        now = datetime.utcnow()

        await conn.execute("""
            INSERT INTO users (
                id, username, email, full_name, hashed_password,
                is_active, is_admin, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """, user_id, "admin", "admin@localhost", "Administrator",
             hashed_pwd, True, True, now, now)

        print("✓ Admin user created successfully!")
        print("Username: admin")
        print("Password: admin123")
        print("Please change the password after first login.")

    except Exception as e:
        print(f"Error creating admin user: {e}")
        print("Make sure PostgreSQL is running and the database exists.")
    finally:
        if 'conn' in locals():
            await conn.close()

if __name__ == "__main__":
    asyncio.run(create_admin_user())