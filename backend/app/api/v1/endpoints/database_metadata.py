from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.schemas.report import (
    DatabaseMetadata, DatabaseTableDetail, QueryResult,
    VisualQuery
)
from app.services.database_metadata_service import DatabaseMetadataService
from app.core.logging_config import log_method_calls, Logger, log_performance

router = APIRouter()
metadata_service = DatabaseMetadataService()

def check_database_access(current_user: User, database_alias: str):
    """Check if user has access to the specified database"""
    if not current_user.is_admin:
        try:
            user_db_aliases = [db_conn.alias for db_conn in current_user.accessible_databases] if current_user.accessible_databases else []
        except Exception:
            user_db_aliases = []

        if database_alias not in user_db_aliases:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied to database '{database_alias}'"
            )


@router.get("/databases/{database_alias}/metadata", response_model=DatabaseMetadata)
async def get_database_metadata(
    database_alias: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get complete metadata for a database including schemas, tables, and views
    """
    try:
        # Check if user has access to this database
        check_database_access(current_user, database_alias)

        metadata = await metadata_service.get_database_metadata(db, database_alias)
        return metadata
    except Exception as e:
        Logger.error(f"Error getting database metadata: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get database metadata")


@router.get("/databases/{database_alias}/tables/{table_name}", response_model=DatabaseTableDetail)
async def get_table_detail(
    database_alias: str,
    table_name: str,
    schema: Optional[str] = Query(None, description="Database schema name"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed information about a specific table including columns and metadata
    """
    try:
        # Check if user has access to this database
        check_database_access(current_user, database_alias)

        table_detail = await metadata_service.get_table_detail(db, database_alias, schema, table_name)
        return table_detail
    except Exception as e:
        Logger.error(f"Error getting table detail: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get table detail")


@router.post("/databases/{database_alias}/query/visual", response_model=QueryResult)
async def execute_visual_query(
    database_alias: str,
    query: VisualQuery,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Execute a visual query built from the query builder interface
    """
    try:
        # Check if user has access to this database
        check_database_access(current_user, database_alias)

        result = await metadata_service.execute_visual_query(db, database_alias, query)
        return result
    except Exception as e:
        Logger.error(f"Error executing visual query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to execute query: {str(e)}")


@router.post("/databases/{database_alias}/query/sql", response_model=QueryResult)
async def execute_custom_sql(
    database_alias: str,
    request_body: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Execute custom SQL query
    """
    try:
        # Check if user has access to this database
        check_database_access(current_user, database_alias)

        sql = request_body.get("sql")
        parameters = request_body.get("parameters", {})

        if not sql:
            raise HTTPException(status_code=400, detail="SQL query is required")

        # Basic SQL injection protection - in production, use more sophisticated validation
        forbidden_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'CREATE', 'ALTER', 'TRUNCATE']
        sql_upper = sql.upper()
        for keyword in forbidden_keywords:
            if keyword in sql_upper:
                raise HTTPException(status_code=400, detail=f"Forbidden SQL keyword: {keyword}")

        result = await metadata_service.execute_custom_sql(db, database_alias, sql, parameters)
        return result
    except HTTPException:
        raise
    except Exception as e:
        Logger.error(f"Error executing custom SQL: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to execute query: {str(e)}")


@router.get("/databases/{database_alias}/schemas", response_model=List[str])
async def get_database_schemas(
    database_alias: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of schemas in the database
    """
    try:
        # Check if user has access to this database
        check_database_access(current_user, database_alias)

        metadata = await metadata_service.get_database_metadata(db, database_alias)
        return [schema.name for schema in metadata.schemas]
    except Exception as e:
        Logger.error(f"Error getting database schemas: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get database schemas")


@router.get("/databases/{database_alias}/schemas/{schema_name}/tables", response_model=List[str])
async def get_schema_tables(
    database_alias: str,
    schema_name: str,
    table_type: Optional[str] = Query(None, description="Filter by table type (table, view)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of tables/views in a specific schema
    """
    try:
        # Check if user has access to this database
        check_database_access(current_user, database_alias)

        metadata = await metadata_service.get_database_metadata(db, database_alias)

        for schema in metadata.schemas:
            if schema.name == schema_name:
                tables = schema.tables
                if table_type:
                    tables = [table for table in tables if table.type == table_type]
                return [table.name for table in tables]

        raise HTTPException(status_code=404, detail=f"Schema '{schema_name}' not found")
    except HTTPException:
        raise
    except Exception as e:
        Logger.error(f"Error getting schema tables: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get schema tables")


@router.post("/databases/{database_alias}/query/preview")
async def preview_query_data(
    database_alias: str,
    request_body: dict,
    limit: int = Query(10, ge=1, le=100, description="Number of rows to preview"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Preview data from a table or query with limited rows
    """
    try:
        # Check if user has access to this database
        check_database_access(current_user, database_alias)

        query_type = request_body.get("type", "table")  # "table" or "query"

        if query_type == "table":
            schema = request_body.get("schema")
            table_name = request_body.get("table")
            if not table_name:
                raise HTTPException(status_code=400, detail="Table name is required")

            schema_prefix = f'"{schema}".' if schema else ""
            sql = f'SELECT * FROM {schema_prefix}"{table_name}" LIMIT {limit}'

        elif query_type == "query":
            sql = request_body.get("sql")
            if not sql:
                raise HTTPException(status_code=400, detail="SQL query is required")

            # Add LIMIT if not present
            if "LIMIT" not in sql.upper():
                sql += f" LIMIT {limit}"
        else:
            raise HTTPException(status_code=400, detail="Invalid query type")

        result = await metadata_service.execute_custom_sql(db, database_alias, sql)
        return {
            "columns": result.columns,
            "data": result.data,
            "total_rows": result.total_rows,
            "is_preview": True,
            "preview_limit": limit
        }
    except HTTPException:
        raise
    except Exception as e:
        Logger.error(f"Error previewing query data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to preview data: {str(e)}")


@router.post("/databases/{database_alias}/query/validate")
async def validate_sql_query(
    database_alias: str,
    request_body: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Validate SQL query syntax without executing it
    """
    try:
        # Check if user has access to this database
        check_database_access(current_user, database_alias)

        sql = request_body.get("sql")
        if not sql:
            raise HTTPException(status_code=400, detail="SQL query is required")

        # Basic validation
        sql_upper = sql.upper().strip()

        # Check if it's a SELECT statement
        if not sql_upper.startswith("SELECT"):
            return {
                "is_valid": False,
                "error": "Only SELECT statements are allowed"
            }

        # Check for forbidden keywords
        forbidden_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'CREATE', 'ALTER', 'TRUNCATE']
        for keyword in forbidden_keywords:
            if keyword in sql_upper:
                return {
                    "is_valid": False,
                    "error": f"Forbidden SQL keyword: {keyword}"
                }

        # Try to prepare the query (this validates syntax)
        try:
            # Add LIMIT 0 to avoid executing the query but still validate syntax
            validation_sql = f"SELECT * FROM ({sql}) AS validation_query LIMIT 0"
            await metadata_service.execute_custom_sql(db, database_alias, validation_sql)

            return {
                "is_valid": True,
                "message": "Query syntax is valid"
            }
        except Exception as syntax_error:
            return {
                "is_valid": False,
                "error": f"Syntax error: {str(syntax_error)}"
            }

    except HTTPException:
        raise
    except Exception as e:
        Logger.error(f"Error validating SQL query: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to validate query")