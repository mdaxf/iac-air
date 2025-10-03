from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import get_current_admin_user
from app.models.user import User
from app.schemas.database import (
    DatabaseConnectionCreate,
    DatabaseConnection,
    SchemaImportRequest,
    ImportJob
)
from app.services.database_service import DatabaseService
from app.services.import_service import ImportService
from app.core.logging_config import log_method_calls, Logger, log_performance

router = APIRouter()


@router.post("/databases", response_model=DatabaseConnection)
async def create_database_connection(
    connection_data: DatabaseConnectionCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new database connection (admin only)"""
    database_service = DatabaseService()
    try:
        return await database_service.create_database_connection(db, connection_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/databases", response_model=List[DatabaseConnection])
async def list_database_connections(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """List all database connections (admin only)"""
    database_service = DatabaseService()
    return await database_service.list_database_connections(db)


@router.get("/databases/{alias}", response_model=DatabaseConnection)
async def get_database_connection(
    alias: str,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a database connection by alias (admin only)"""
    database_service = DatabaseService()
    db_conn = await database_service.get_database_connection(db, alias)
    if not db_conn:
        raise HTTPException(status_code=404, detail="Database connection not found")
    return db_conn


@router.post("/databases/{alias}/import")
async def start_schema_import(
    alias: str,
    import_request: SchemaImportRequest,
    background_tasks: BackgroundTasks,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Start schema import for a database (admin only)"""
    database_service = DatabaseService()
    db_conn = await database_service.get_database_connection(db, alias)
    if not db_conn:
        raise HTTPException(status_code=404, detail="Database connection not found")

    import_service = ImportService()
    job_id = await import_service.start_import_job(
        db, db_conn, import_request, background_tasks
    )

    return {"job_id": job_id, "status": "started"}


@router.get("/jobs/{job_id}")
async def get_import_job_status(
    job_id: str,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get the status of an import job (admin only)"""
    import_service = ImportService()
    job = await import_service.get_job_status(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/databases/{alias}/schema")
async def get_database_schema(
    alias: str,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get the schema information for a database (admin only)"""
    database_service = DatabaseService()
    db_conn = await database_service.get_database_connection(db, alias)
    if not db_conn:
        raise HTTPException(status_code=404, detail="Database connection not found")

    try:
        schema_info = await database_service.introspect_database(db_conn)
        return schema_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to introspect database: {str(e)}")


@router.put("/databases/{alias}", response_model=DatabaseConnection)
async def update_database_connection(
    alias: str,
    update_data: DatabaseConnectionCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a database connection (admin only)"""
    database_service = DatabaseService()
    db_conn = await database_service.get_database_connection(db, alias)
    if not db_conn:
        raise HTTPException(status_code=404, detail="Database connection not found")

    try:
        return await database_service.update_database_connection(db, alias, update_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/databases/{alias}")
async def delete_database_connection(
    alias: str,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a database connection (admin only)"""
    database_service = DatabaseService()
    db_conn = await database_service.get_database_connection(db, alias)
    if not db_conn:
        raise HTTPException(status_code=404, detail="Database connection not found")

    try:
        await database_service.delete_database_connection(db, alias)
        return {"message": f"Database connection '{alias}' deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/databases/{alias}/generate-vectors")
async def generate_vector_documents(
    alias: str,
    background_tasks: BackgroundTasks,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate vector documents for database schema (admin only)"""
    database_service = DatabaseService()
    db_conn = await database_service.get_database_connection(db, alias)
    if not db_conn:
        raise HTTPException(status_code=404, detail="Database connection not found")

    try:
        # Start vector document generation in background
        from app.services.vector_generation_service import VectorGenerationService
        vector_service = VectorGenerationService()

        job_id = await vector_service.generate_database_vectors(
            db, db_conn, background_tasks
        )

        return {
            "job_id": job_id,
            "status": "started",
            "message": f"Vector document generation started for database '{alias}'"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start vector generation: {str(e)}")