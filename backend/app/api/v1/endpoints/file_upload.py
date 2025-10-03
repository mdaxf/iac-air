"""
File Upload API Endpoints

Provides REST API for uploading and managing files for database context enhancement.
"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession
import os
from pathlib import Path

from app.core.database import get_db
from app.schemas.uploaded_file import (
    UploadedFile,
    UploadedFileUpdate,
    UploadedFileSearch,
    FileUploadResponse,
    FileProcessRequest,
    FileProcessResult
)
from app.services.file_upload_service import FileUploadService, FileProcessingService
from app.schemas.uploaded_file import UploadedFileCreate
from app.core.logging_config import log_method_calls, Logger
import logging

router = APIRouter()
logger = logging.getLogger("file_upload_api")


@router.post("/upload", response_model=FileUploadResponse)
@log_method_calls
async def upload_file(
    file: UploadFile = File(...),
    db_alias: str = Form(...),
    uploaded_by: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """Upload a file for database context enhancement"""
    try:
        # Validate file
        if not FileUploadService.is_allowed_file(file.filename):
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed types: {', '.join(FileUploadService.ALLOWED_EXTENSIONS)}"
            )

        # Read file content
        file_content = await file.read()
        file_size = len(file_content)

        if file_size > FileUploadService.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum allowed size of {FileUploadService.MAX_FILE_SIZE / 1024 / 1024}MB"
            )

        # Get file extension
        file_ext = file.filename.rsplit('.', 1)[1].lower()

        # Create upload directory
        upload_dir = FileUploadService.get_upload_directory()

        # Generate unique filename
        file_hash = FileUploadService.get_file_hash(file_content)
        safe_filename = f"{file_hash}_{file.filename}"
        file_path = os.path.join(upload_dir, safe_filename)

        # Save file
        with open(file_path, 'wb') as f:
            f.write(file_content)

        # Create database record
        file_data = UploadedFileCreate(
            db_alias=db_alias,
            file_name=file.filename,
            file_type=file_ext,
            file_size_bytes=file_size,
            file_path=file_path,
            mime_type=file.content_type,
            uploaded_by=uploaded_by
        )

        db_file = await FileUploadService.create_file_record(db, file_data)

        return FileUploadResponse(
            success=True,
            file_id=db_file.id,
            file_name=db_file.file_name,
            file_size_bytes=db_file.file_size_bytes,
            status=db_file.status,
            message="File uploaded successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/files/{file_id}", response_model=UploadedFile)
@log_method_calls
async def get_uploaded_file(
    file_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get uploaded file by ID"""
    file = await FileUploadService.get_file(db, file_id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    return file


@router.get("/files", response_model=List[UploadedFile])
@log_method_calls
async def list_uploaded_files(
    db_alias: str = Query(None),
    status: str = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """List uploaded files with optional filters"""
    files = await FileUploadService.list_files(
        db, db_alias=db_alias, status=status, limit=limit, offset=offset
    )
    return files


@router.post("/files/search", response_model=List[UploadedFile])
@log_method_calls
async def search_uploaded_files(
    search: UploadedFileSearch,
    db: AsyncSession = Depends(get_db)
):
    """Search uploaded files"""
    files = await FileUploadService.search_files(db, search)
    return files


@router.put("/files/{file_id}", response_model=UploadedFile)
@log_method_calls
async def update_uploaded_file(
    file_id: UUID,
    file_update: UploadedFileUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update uploaded file metadata"""
    file = await FileUploadService.update_file(db, file_id, file_update)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    return file


@router.delete("/files/{file_id}", status_code=204)
@log_method_calls
async def delete_uploaded_file(
    file_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete uploaded file"""
    success = await FileUploadService.delete_file(db, file_id)
    if not success:
        raise HTTPException(status_code=404, detail="File not found")
    return None


@router.post("/files/{file_id}/process", response_model=FileProcessResult)
@log_method_calls
async def process_uploaded_file(
    file_id: UUID,
    process_request: FileProcessRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Process uploaded file: extract text, chunk, and generate embeddings.
    This is a placeholder - full implementation will be in Phase 3 & 4.
    """
    try:
        # Get file
        file = await FileUploadService.get_file(db, file_id)
        if not file:
            raise HTTPException(status_code=404, detail="File not found")

        if file.status == 'processing':
            raise HTTPException(status_code=400, detail="File is already being processed")

        # Update status to processing
        await FileUploadService.update_processing_status(db, file_id, 'processing', 0.0)

        # Process file (placeholder)
        import time
        start_time = time.time()

        try:
            # Extract text
            text = await FileProcessingService.extract_text(file.file_path, file.file_type)

            # Chunk text
            chunks = FileProcessingService.chunk_text(
                text,
                chunk_size=process_request.chunk_size,
                chunk_overlap=process_request.chunk_overlap
            )

            # TODO: Create vector documents and generate embeddings (Phase 3 & 4)
            processing_time = (time.time() - start_time) * 1000

            # Update status to completed
            await FileUploadService.update_processing_status(db, file_id, 'completed', 1.0)

            # Update results
            results = {
                'chunks_created': len(chunks),
                'embeddings_generated': 0,  # TODO: Implement in Phase 4
                'tables_mentioned': [],  # TODO: Extract table mentions
                'processing_time_ms': processing_time
            }
            await FileUploadService.update_processing_results(db, file_id, results)

            return FileProcessResult(
                success=True,
                file_id=file_id,
                chunks_created=len(chunks),
                embeddings_generated=0,
                tables_mentioned=[],
                processing_time_ms=processing_time
            )

        except Exception as e:
            # Update status to failed
            await FileUploadService.update_processing_status(
                db, file_id, 'failed', 0.0, str(e)
            )
            raise

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        return FileProcessResult(
            success=False,
            file_id=file_id,
            chunks_created=0,
            embeddings_generated=0,
            processing_time_ms=0,
            error=str(e)
        )


@router.post("/files/{file_id}/retry", response_model=FileProcessResult)
@log_method_calls
async def retry_file_processing(
    file_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Retry processing a failed file"""
    file = await FileUploadService.get_file(db, file_id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    if file.status != 'failed':
        raise HTTPException(
            status_code=400,
            detail=f"File is not in failed status (current status: {file.status})"
        )

    # Reset status and retry
    await FileUploadService.update_processing_status(db, file_id, 'uploaded', 0.0, None)

    # Process with default parameters
    process_request = FileProcessRequest(
        file_id=file_id,
        chunk_size=1000,
        chunk_overlap=200,
        generate_embeddings=True
    )

    return await process_uploaded_file(file_id, process_request, db)
