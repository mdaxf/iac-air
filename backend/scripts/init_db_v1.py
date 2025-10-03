"""
Database Initialization Script v1.0

This script initializes the database with all tables and creates the initial
migration version stamp at v1.0.

Usage:
    python scripts/init_db_v1.py
"""
import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings
from app.core.database import Base
from app.core.logging_config import debug_logger as logger

# Import all models to ensure they're registered with Base.metadata
from app.models.database_connection import DatabaseConnection
from app.models.query_history import QueryHistory
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.report import Report
from app.models.report_version import ReportVersion
from app.models.report_component import ReportComponent
from app.models.report_layout import ReportLayout
from app.models.report_parameters import ReportParameter, ReportParameterValue
from app.models.user import User
from app.models.api_call_history import APICallHistory
from app.models.vector_document import VectorDocument
from app.models.vector_metadata import (
    VectorTableMetadata,
    VectorColumnMetadata,
    VectorRelationshipMetadata
)
from app.models.business_semantic import (
    BusinessEntity,
    BusinessMetric,
    ConceptMapping,
    QueryTemplate
)
from app.models.uploaded_file import UploadedFile
from app.models.import_job import ImportJob
from app.models.vector_job import VectorRegenerationJob


async def check_database_exists(engine):
    """Check if the database has any tables"""
    async with engine.connect() as conn:
        result = await conn.execute(text("""
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
        """))
        count = result.scalar()
        return count > 0


async def drop_all_tables(engine):
    """Drop all existing tables"""
    logger.info("Dropping all existing tables...")
    async with engine.connect() as conn:
        # Drop alembic version table
        await conn.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE"))

        # Get all tables
        result = await conn.execute(text("""
            SELECT tablename FROM pg_tables
            WHERE schemaname = 'public'
        """))
        tables = result.fetchall()

        # Drop each table
        for table in tables:
            await conn.execute(text(f"DROP TABLE IF EXISTS {table[0]} CASCADE"))

        await conn.commit()
    logger.info("All tables dropped successfully")


async def create_all_tables(engine):
    """Create all tables from models"""
    logger.info("Creating all tables from models...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("All tables created successfully")


async def create_alembic_version_table(engine):
    """Create alembic_version table and mark as v1.0"""
    logger.info("Creating alembic_version table and marking as v1.0...")
    async with engine.connect() as conn:
        # Create alembic_version table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS alembic_version (
                version_num VARCHAR(32) NOT NULL,
                CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
            )
        """))

        # Mark current version as v1.0
        await conn.execute(text("""
            INSERT INTO alembic_version (version_num)
            VALUES ('v1.0')
            ON CONFLICT DO NOTHING
        """))

        await conn.commit()
    logger.info("Database marked as v1.0")


async def create_extensions(engine):
    """Create required PostgreSQL extensions"""
    logger.info("Creating PostgreSQL extensions...")
    async with engine.connect() as conn:
        # Create pgvector extension for vector operations
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

        # Create uuid extension
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\""))

        await conn.commit()
    logger.info("Extensions created successfully")


async def initialize_database():
    """Main initialization function"""
    try:
        logger.info("=" * 80)
        logger.info("Starting Database Initialization v1.0")
        logger.info("=" * 80)
        logger.info(f"Database URL: {settings.DATABASE_URL.split('@')[1]}")  # Hide password

        # Create async engine
        engine = create_async_engine(
            settings.DATABASE_URL,
            echo=False,
            pool_pre_ping=True
        )

        # Check if database has tables
        has_tables = await check_database_exists(engine)

        if has_tables:
            logger.warning("Database already contains tables!")
            response = input("Do you want to drop all existing tables and reinitialize? (yes/no): ")
            if response.lower() != 'yes':
                logger.info("Initialization cancelled by user")
                return

            # Drop all tables
            await drop_all_tables(engine)

        # Create extensions
        await create_extensions(engine)

        # Create all tables
        await create_all_tables(engine)

        # Create alembic version table
        await create_alembic_version_table(engine)

        # Close engine
        await engine.dispose()

        logger.info("=" * 80)
        logger.info("Database Initialization v1.0 Completed Successfully!")
        logger.info("=" * 80)
        logger.info("")
        logger.info("Next steps:")
        logger.info("1. Run the backend server: uvicorn app.main:app --reload")
        logger.info("2. Create database connections via the UI")
        logger.info("3. Import schemas and generate embeddings")
        logger.info("")

    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(initialize_database())
