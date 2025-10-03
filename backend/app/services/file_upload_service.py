"""
File Upload Service

Handles file uploads, storage, and processing for database context enhancement.
"""
from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select
import os
import hashlib
from datetime import datetime
from pathlib import Path

from app.models.uploaded_file import UploadedFile
from app.schemas.uploaded_file import (
    UploadedFileCreate,
    UploadedFileUpdate,
    UploadedFileSearch
)


class FileUploadService:
    """Service for managing file uploads"""

    UPLOAD_DIR = "uploads/database_files"
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'xlsx', 'csv', 'txt', 'md'}
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

    @staticmethod
    def get_upload_directory() -> str:
        """Get or create upload directory"""
        upload_dir = Path(FileUploadService.UPLOAD_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)
        return str(upload_dir)

    @staticmethod
    def is_allowed_file(filename: str) -> bool:
        """Check if file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in FileUploadService.ALLOWED_EXTENSIONS

    @staticmethod
    def get_file_hash(file_content: bytes) -> str:
        """Generate hash for file content"""
        return hashlib.sha256(file_content).hexdigest()

    @staticmethod
    async def create_file_record(
        db: AsyncSession,
        file_data: UploadedFileCreate
    ) -> UploadedFile:
        """Create uploaded file record"""
        db_file = UploadedFile(
            db_alias=file_data.db_alias,
            file_name=file_data.file_name,
            file_type=file_data.file_type,
            file_size_bytes=file_data.file_size_bytes,
            file_path=file_data.file_path,
            mime_type=file_data.mime_type,
            content_metadata=file_data.content_metadata,
            uploaded_by=file_data.uploaded_by
        )
        db.add(db_file)
        await db.commit()
        await db.refresh(db_file)
        return db_file

    @staticmethod
    async def get_file(db: AsyncSession, file_id: UUID) -> Optional[UploadedFile]:
        """Get uploaded file by ID"""
        query = select(UploadedFile).where(UploadedFile.id == file_id)
        result = await db.execute(query)
        return result.scalars().first()

    @staticmethod
    async def list_files(
        db: AsyncSession,
        db_alias: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[UploadedFile]:
        """List uploaded files with optional filters"""
        query = select(UploadedFile)

        if db_alias:
            query = query.where(UploadedFile.db_alias == db_alias)
        if status:
            query = query.where(UploadedFile.status == status)

        query = query.order_by(UploadedFile.uploaded_at.desc()).limit(limit).offset(offset)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def search_files(
        db: AsyncSession,
        search: UploadedFileSearch
    ) -> List[UploadedFile]:
        """Search uploaded files"""
        query = select(UploadedFile)

        if search.db_alias:
            query = query.where(UploadedFile.db_alias == search.db_alias)
        if search.file_type:
            query = query.where(UploadedFile.file_type == search.file_type)
        if search.status:
            query = query.where(UploadedFile.status == search.status)
        if search.uploaded_by:
            query = query.where(UploadedFile.uploaded_by == search.uploaded_by)

        query = query.order_by(UploadedFile.uploaded_at.desc()).limit(search.limit).offset(search.offset)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def update_file(
        db: AsyncSession,
        file_id: UUID,
        file_update: UploadedFileUpdate
    ) -> Optional[UploadedFile]:
        """Update uploaded file"""
        query = select(UploadedFile).where(UploadedFile.id == file_id)
        result = await db.execute(query)
        db_file = result.scalars().first()
        if not db_file:
            return None

        update_data = file_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_file, field, value)

        await db.commit()
        await db.refresh(db_file)
        return db_file

    @staticmethod
    async def delete_file(db: AsyncSession, file_id: UUID) -> bool:
        """Delete uploaded file and remove from storage"""
        query = select(UploadedFile).where(UploadedFile.id == file_id)
        result = await db.execute(query)
        db_file = result.scalars().first()
        if not db_file:
            return False

        # Delete physical file
        try:
            if os.path.exists(db_file.file_path):
                os.remove(db_file.file_path)
        except Exception:
            pass  # Continue with database deletion even if file removal fails

        db.delete(db_file)
        await db.commit()
        return True

    @staticmethod
    async def update_processing_status(
        db: AsyncSession,
        file_id: UUID,
        status: str,
        progress: float = 0.0,
        error_message: Optional[str] = None
    ) -> Optional[UploadedFile]:
        """Update file processing status"""
        query = select(UploadedFile).where(UploadedFile.id == file_id)
        result = await db.execute(query)
        db_file = result.scalars().first()
        if not db_file:
            return None

        db_file.status = status
        db_file.processing_progress = progress

        if error_message:
            db_file.error_message = error_message

        if status == 'completed':
            db_file.processed_at = datetime.utcnow()
            db_file.processing_progress = 1.0

        await db.commit()
        await db.refresh(db_file)
        return db_file

    @staticmethod
    async def update_processing_results(
        db: AsyncSession,
        file_id: UUID,
        results: dict
    ) -> Optional[UploadedFile]:
        """Update file processing results"""
        query = select(UploadedFile).where(UploadedFile.id == file_id)
        result = await db.execute(query)
        db_file = result.scalars().first()
        if not db_file:
            return None

        db_file.processing_results = results
        await db.commit()
        await db.refresh(db_file)
        return db_file


class FileProcessingService:
    """Service for processing uploaded files into vector documents"""

    @staticmethod
    async def extract_text_from_pdf(file_path: str) -> str:
        """Extract text from PDF file"""
        # TODO: Implement PDF text extraction using PyPDF2 or pdfplumber
        # For now, return placeholder
        return "PDF text extraction not yet implemented"

    @staticmethod
    async def extract_text_from_docx(file_path: str) -> str:
        """Extract text from DOCX file"""
        # TODO: Implement DOCX text extraction using python-docx
        return "DOCX text extraction not yet implemented"

    @staticmethod
    async def extract_text_from_xlsx(file_path: str) -> str:
        """Extract text from XLSX file"""
        # TODO: Implement XLSX text extraction using openpyxl or pandas
        return "XLSX text extraction not yet implemented"

    @staticmethod
    async def extract_text_from_csv(file_path: str) -> str:
        """Extract text from CSV file"""
        # TODO: Implement CSV text extraction using pandas
        return "CSV text extraction not yet implemented"

    @staticmethod
    async def extract_text_from_txt(file_path: str) -> str:
        """Extract text from TXT file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            raise ValueError(f"Failed to read text file: {str(e)}")

    @staticmethod
    async def extract_text_from_md(file_path: str) -> str:
        """Extract text from Markdown file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            raise ValueError(f"Failed to read markdown file: {str(e)}")

    @staticmethod
    async def extract_text(file_path: str, file_type: str) -> str:
        """Extract text from file based on type"""
        extractors = {
            'pdf': FileProcessingService.extract_text_from_pdf,
            'docx': FileProcessingService.extract_text_from_docx,
            'xlsx': FileProcessingService.extract_text_from_xlsx,
            'csv': FileProcessingService.extract_text_from_csv,
            'txt': FileProcessingService.extract_text_from_txt,
            'md': FileProcessingService.extract_text_from_md
        }

        extractor = extractors.get(file_type)
        if not extractor:
            raise ValueError(f"Unsupported file type: {file_type}")

        return await extractor(file_path)

    @staticmethod
    def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks"""
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)

            # Move start forward by (chunk_size - overlap)
            start += (chunk_size - overlap)

        return chunks

    @staticmethod
    async def process_file(
        db: AsyncSession,
        file_id: UUID,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> dict:
        """
        Process uploaded file: extract text, chunk, and prepare for embedding.
        Returns processing results.
        """
        # This is a placeholder implementation
        # The actual implementation will be in Phase 3 & 4
        return {
            'chunks_created': 0,
            'embeddings_generated': 0,
            'tables_mentioned': [],
            'processing_time_ms': 0,
            'status': 'pending_full_implementation'
        }
