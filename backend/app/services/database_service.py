from typing import List, Optional, Dict, Any, Tuple
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import asyncpg
# import aiomysql  # Commented out for testing
# import pyodbc    # Commented out for testing
# import cx_Oracle # Commented out for testing
from cryptography.fernet import Fernet

from app.core.logging_config import Logger, log_method_calls
from app.models.database import DatabaseConnection
from app.schemas.database import DatabaseConnectionCreate, DatabaseType
from app.core.config import settings


class DatabaseConnector:
    """Base class for database connectors"""

    @log_method_calls
    async def test_connection(self, connection_params: Dict[str, Any]) -> bool:
        """Test if connection parameters are valid"""
        raise NotImplementedError

    @log_method_calls
    async def get_schemas(self, connection_params: Dict[str, Any]) -> List[str]:
        """Get list of schemas in the database"""
        raise NotImplementedError

    @log_method_calls
    async def get_tables(self, connection_params: Dict[str, Any], schema: str) -> List[Dict[str, Any]]:
        """Get list of tables in a schema with metadata"""
        raise NotImplementedError

    async def get_columns(self, connection_params: Dict[str, Any], schema: str, table: str) -> List[Dict[str, Any]]:
        """Get list of columns in a table with metadata"""
        raise NotImplementedError

    async def sample_data(self, connection_params: Dict[str, Any], schema: str, table: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get sample data from a table"""
        raise NotImplementedError


class PostgreSQLConnector(DatabaseConnector):
    async def test_connection(self, connection_params: Dict[str, Any]) -> bool:
        try:
            conn = await asyncpg.connect(**connection_params)
            await conn.close()
            return True
        except Exception:
            return False

    async def get_schemas(self, connection_params: Dict[str, Any]) -> List[str]:
        conn = await asyncpg.connect(**connection_params)
        try:
            rows = await conn.fetch(
                "SELECT schema_name FROM information_schema.schemata "
                "WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast') "
                "ORDER BY schema_name"
            )
            return [row['schema_name'] for row in rows]
        finally:
            await conn.close()

    async def get_tables(self, connection_params: Dict[str, Any], schema: str) -> List[Dict[str, Any]]:
        conn = await asyncpg.connect(**connection_params)
        try:
            rows = await conn.fetch("""
                SELECT
                    table_name,
                    table_type,
                    COALESCE(obj_description(c.oid), '') as table_comment
                FROM information_schema.tables t
                LEFT JOIN pg_class c ON c.relname = t.table_name
                LEFT JOIN pg_namespace n ON n.oid = c.relnamespace AND n.nspname = t.table_schema
                WHERE table_schema = $1
                ORDER BY table_name
            """, schema)

            return [
                {
                    "name": row['table_name'],
                    "type": row['table_type'],
                    "comment": row['table_comment'] or "",
                    "schema": schema
                }
                for row in rows
            ]
        finally:
            await conn.close()

    async def get_columns(self, connection_params: Dict[str, Any], schema: str, table: str) -> List[Dict[str, Any]]:
        conn = await asyncpg.connect(**connection_params)
        try:
            rows = await conn.fetch("""
                SELECT
                    column_name,
                    data_type,
                    is_nullable,
                    column_default,
                    character_maximum_length,
                    numeric_precision,
                    numeric_scale,
                    COALESCE(col_description(pgc.oid, c.ordinal_position), '') as column_comment
                FROM information_schema.columns c
                LEFT JOIN pg_class pgc ON pgc.relname = c.table_name
                LEFT JOIN pg_namespace pgn ON pgn.oid = pgc.relnamespace AND pgn.nspname = c.table_schema
                WHERE c.table_schema = $1 AND c.table_name = $2
                ORDER BY c.ordinal_position
            """, schema, table)

            return [
                {
                    "name": row['column_name'],
                    "data_type": row['data_type'],
                    "is_nullable": row['is_nullable'] == 'YES',
                    "default_value": row['column_default'],
                    "max_length": row['character_maximum_length'],
                    "precision": row['numeric_precision'],
                    "scale": row['numeric_scale'],
                    "comment": row['column_comment'] or ""
                }
                for row in rows
            ]
        finally:
            await conn.close()

    async def sample_data(self, connection_params: Dict[str, Any], schema: str, table: str, limit: int = 100) -> List[Dict[str, Any]]:
        conn = await asyncpg.connect(**connection_params)
        try:
            # Get column names first
            columns = await self.get_columns(connection_params, schema, table)
            column_names = [col['name'] for col in columns]

            # Sample data
            query = f'SELECT * FROM "{schema}"."{table}" LIMIT $1'
            rows = await conn.fetch(query, limit)

            return [dict(zip(column_names, row)) for row in rows]
        finally:
            await conn.close()


class DatabaseService:
    def __init__(self):
        self.connectors = {
            DatabaseType.POSTGRES: PostgreSQLConnector(),
            # Add other connectors as needed
        }
        self.cipher = Fernet(settings.SECRET_KEY)

    def _encrypt_password(self, password: str) -> str:
        """Encrypt password for storage"""
        return self.cipher.encrypt(password.encode()).decode()

    def _decrypt_password(self, encrypted_password: str) -> str:
        """Decrypt password for use"""
        return self.cipher.decrypt(encrypted_password.encode()).decode()

    def _get_connection_params(self, db_conn: DatabaseConnection) -> Dict[str, Any]:
        """Convert DatabaseConnection to connection parameters"""
        password = self._decrypt_password(db_conn.password_hash)

        if db_conn.type == DatabaseType.POSTGRES:
            return {
                'host': db_conn.host,
                'port': db_conn.port,
                'database': db_conn.database,
                'user': db_conn.username,
                'password': password
            }
        # Add other database types as needed
        else:
            raise ValueError(f"Unsupported database type: {db_conn.type}")

    async def create_database_connection(
        self,
        db: AsyncSession,
        connection_data: DatabaseConnectionCreate
    ) -> DatabaseConnection:
        """Create a new database connection"""
        # Test connection first
        connector = self.connectors.get(connection_data.type)
        if not connector:
            raise ValueError(f"Unsupported database type: {connection_data.type}")

        connection_params = {
            'host': connection_data.host,
            'port': connection_data.port,
            'database': connection_data.database,
            'user': connection_data.username,
            'password': connection_data.password
        }

        if not await connector.test_connection(connection_params):
            raise ValueError("Failed to connect to database with provided credentials")

        # Encrypt password and create record
        encrypted_password = self._encrypt_password(connection_data.password)

        db_connection = DatabaseConnection(
            alias=connection_data.alias,
            type=connection_data.type.value,
            host=connection_data.host,
            port=connection_data.port,
            database=connection_data.database,
            username=connection_data.username,
            password_hash=encrypted_password,
            schema_whitelist=connection_data.schema_whitelist,
            schema_blacklist=connection_data.schema_blacklist,
            domain=connection_data.domain,
            description=connection_data.description
        )

        db.add(db_connection)
        await db.commit()
        await db.refresh(db_connection)
        return db_connection

    async def get_database_connection(self, db: AsyncSession, alias: str) -> Optional[DatabaseConnection]:
        """Get database connection by alias"""
        query = select(DatabaseConnection).where(
            DatabaseConnection.alias == alias,
            DatabaseConnection.is_active == True
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def list_database_connections(self, db: AsyncSession) -> List[DatabaseConnection]:
        """List all active database connections"""
        query = select(DatabaseConnection).where(DatabaseConnection.is_active == True)
        result = await db.execute(query)
        return result.scalars().all()

    async def introspect_database(self, db_conn: DatabaseConnection) -> Dict[str, Any]:
        """Introspect a database and return schema information"""
        connector = self.connectors.get(DatabaseType(db_conn.type))
        if not connector:
            raise ValueError(f"Unsupported database type: {db_conn.type}")

        connection_params = self._get_connection_params(db_conn)

        # Get schemas
        all_schemas = await connector.get_schemas(connection_params)

        # Filter schemas based on whitelist/blacklist
        schemas = self._filter_schemas(all_schemas, db_conn.schema_whitelist, db_conn.schema_blacklist)

        schema_info = {}
        for schema in schemas:
            # Get tables for each schema
            tables = await connector.get_tables(connection_params, schema)

            table_info = {}
            for table in tables:
                # Get columns for each table
                columns = await connector.get_columns(connection_params, schema, table['name'])

                # Get sample data
                try:
                    sample_data = await connector.sample_data(connection_params, schema, table['name'], 10)
                except Exception:
                    sample_data = []

                table_info[table['name']] = {
                    'metadata': table,
                    'columns': columns,
                    'sample_data': sample_data
                }

            schema_info[schema] = table_info

        return {
            'db_alias': db_conn.alias,
            'database_type': db_conn.type,
            'schemas': schema_info
        }

    def _filter_schemas(self, schemas: List[str], whitelist: List[str], blacklist: List[str]) -> List[str]:
        """Filter schemas based on whitelist and blacklist"""
        if whitelist:
            # If whitelist is provided, only include schemas that match
            schemas = [s for s in schemas if any(s.startswith(pattern.rstrip('*')) for pattern in whitelist)]

        if blacklist:
            # Remove schemas that match blacklist patterns
            schemas = [s for s in schemas if not any(s.startswith(pattern.rstrip('*')) for pattern in blacklist)]

        return schemas

    async def get_connection(self, db: AsyncSession, database_alias: str) -> DatabaseConnection:
        """Get database connection by alias"""
        from sqlalchemy import select
        from app.models.database import DatabaseConnection

        query = select(DatabaseConnection).where(DatabaseConnection.alias == database_alias)
        result = await db.execute(query)
        connection = result.scalar_one_or_none()

        if not connection:
            raise ValueError(f"Database connection '{database_alias}' not found")

        return connection

    def get_database_session(self, db_connection: DatabaseConnection):
        """Get database session for the specified database connection"""
        from contextlib import asynccontextmanager
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy.orm import sessionmaker

        @asynccontextmanager
        async def session_context():
            # Create connection string based on database type
            if db_connection.type == DatabaseType.POSTGRES:
                password = self._decrypt_password(db_connection.password_hash)
                connection_string = f"postgresql+asyncpg://{db_connection.username}:{password}@{db_connection.host}:{db_connection.port}/{db_connection.database}"
            else:
                raise ValueError(f"Unsupported database type: {db_connection.type}")

            # Create engine and session
            engine = create_async_engine(connection_string)
            session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

            async with session_maker() as session:
                try:
                    yield session
                finally:
                    await session.close()
                    await engine.dispose()

        return session_context()

    def get_sync_engine(self, db_connection: DatabaseConnection):
        """Get a synchronous SQLAlchemy engine for the specified database connection"""
        from sqlalchemy import create_engine

        # Create connection string based on database type
        if db_connection.type == DatabaseType.POSTGRES:
            password = self._decrypt_password(db_connection.password_hash)
            connection_string = f"postgresql://{db_connection.username}:{password}@{db_connection.host}:{db_connection.port}/{db_connection.database}"
        else:
            raise ValueError(f"Unsupported database type: {db_connection.type}")

        # Create synchronous engine
        engine = create_engine(connection_string)
        return engine

    async def update_database_connection(
        self,
        db: AsyncSession,
        alias: str,
        update_data: DatabaseConnectionCreate
    ) -> DatabaseConnection:
        """Update an existing database connection"""
        # Get existing connection
        existing_conn = await self.get_database_connection(db, alias)
        if not existing_conn:
            raise ValueError(f"Database connection '{alias}' not found")

        # Test new connection first
        connector = self.connectors.get(update_data.type)
        if not connector:
            raise ValueError(f"Unsupported database type: {update_data.type}")

        connection_params = {
            'host': update_data.host,
            'port': update_data.port,
            'database': update_data.database,
            'user': update_data.username,
            'password': update_data.password
        }

        if not await connector.test_connection(connection_params):
            raise ValueError("Failed to connect to database with provided credentials")

        # Update existing connection
        existing_conn.alias = update_data.alias
        existing_conn.type = update_data.type.value
        existing_conn.host = update_data.host
        existing_conn.port = update_data.port
        existing_conn.database = update_data.database
        existing_conn.username = update_data.username
        existing_conn.password_hash = self._encrypt_password(update_data.password)
        existing_conn.schema_whitelist = update_data.schema_whitelist
        existing_conn.schema_blacklist = update_data.schema_blacklist
        existing_conn.domain = update_data.domain
        existing_conn.description = update_data.description

        await db.commit()
        await db.refresh(existing_conn)
        return existing_conn

    async def delete_database_connection(self, db: AsyncSession, alias: str) -> bool:
        """Delete a database connection (soft delete by setting is_active to False)"""
        existing_conn = await self.get_database_connection(db, alias)
        if not existing_conn:
            raise ValueError(f"Database connection '{alias}' not found")

        # Soft delete by setting is_active to False
        existing_conn.is_active = False
        await db.commit()

        # Also clean up related vector documents
        try:
            from app.services.vector_service import VectorService
            from app.services.embedding_service import EmbeddingService

            embedding_service = EmbeddingService()
            vector_service = VectorService(embedding_service)

            # Delete vector documents for this database
            from app.api.v1.endpoints.vector import delete_documents_by_database
            await delete_documents_by_database(alias, db)

        except Exception as e:
            Logger.warning(f"Failed to clean up vector documents for {alias}: {str(e)}")

        return True