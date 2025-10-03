from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.vector_document import (
    VectorDocumentCreate,
    VectorDocument,
    VectorSearchRequest,
    VectorSearchResult,
    VectorDatabaseStats,
    DatabaseDocumentCreate
)
from app.services.vector_service import VectorService
from app.services.embedding_service import EmbeddingService
from app.core.logging_config import log_method_calls, Logger, log_performance

router = APIRouter()


def get_vector_service():
    embedding_service = EmbeddingService()
    return VectorService(embedding_service)


@router.post("/documents", response_model=VectorDocument)
async def create_vector_document(
    document_data: VectorDocumentCreate,
    db: AsyncSession = Depends(get_db),
    vector_service: VectorService = Depends(get_vector_service)
):
    """Create a new vector document"""
    try:
        return await vector_service.create_document(db, document_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create document: {str(e)}")


@router.post("/search", response_model=List[VectorSearchResult])
async def search_vector_documents(
    search_request: VectorSearchRequest,
    db: AsyncSession = Depends(get_db),
    vector_service: VectorService = Depends(get_vector_service)
):
    """Search for similar vector documents"""
    try:
        return await vector_service.search_similar(db, search_request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/documents/{resource_id}", response_model=VectorDocument)
async def get_vector_document(
    resource_id: str,
    db_alias: str = None,
    db: AsyncSession = Depends(get_db),
    vector_service: VectorService = Depends(get_vector_service)
):
    """Get a vector document by resource ID"""
    document = await vector_service.get_document_by_resource_id(db, resource_id, db_alias)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.put("/documents/{document_id}", response_model=VectorDocument)
async def update_vector_document(
    document_id: str,
    content: str,
    metadata: dict = None,
    db: AsyncSession = Depends(get_db),
    vector_service: VectorService = Depends(get_vector_service)
):
    """Update a vector document"""
    try:
        document = await vector_service.update_document(db, document_id, content, metadata)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return document
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update document: {str(e)}")


@router.delete("/documents/database/{db_alias}")
async def delete_documents_by_database(
    db_alias: str,
    db: AsyncSession = Depends(get_db),
    vector_service: VectorService = Depends(get_vector_service)
):
    """Delete all vector documents for a database"""
    try:
        count = await vector_service.delete_documents_by_db_alias(db, db_alias)
        return {"deleted_count": count, "message": f"Deleted {count} documents for database {db_alias}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete documents: {str(e)}")


@router.get("/stats/{db_alias}", response_model=VectorDatabaseStats)
async def get_database_vector_stats(
    db_alias: str,
    db: AsyncSession = Depends(get_db),
    vector_service: VectorService = Depends(get_vector_service)
):
    """Get vector database statistics for a specific database"""
    try:
        return await vector_service.get_database_stats(db, db_alias)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get database stats: {str(e)}")


@router.post("/database-documents/{db_alias}", response_model=VectorDocument)
async def create_database_document(
    db_alias: str,
    document_data: DatabaseDocumentCreate,
    db: AsyncSession = Depends(get_db),
    vector_service: VectorService = Depends(get_vector_service)
):
    """Create a database documentation document with vector embedding"""
    try:
        return await vector_service.create_database_document(
            db=db,
            db_alias=db_alias,
            title=document_data.title,
            content=document_data.content,
            document_type=document_data.document_type,
            metadata=document_data.metadata
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create database document: {str(e)}")