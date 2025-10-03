from fastapi import APIRouter
from app.api.v1.endpoints import admin, chat, vector, auth, admin_users, admin_logs, admin_api_history, reports, database_metadata, text2sql, dashboard, business_semantic, file_upload, vector_metadata

api_router = APIRouter()

# Authentication endpoints
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])

# Admin endpoints
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(admin_users.router, prefix="/admin", tags=["user-management"])
api_router.include_router(admin_logs.router, prefix="/admin", tags=["logging"])
api_router.include_router(admin_api_history.router, prefix="/admin", tags=["api-history"])

# Core functionality endpoints
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(vector.router, prefix="/vector", tags=["vector"])

# Business Semantic Layer endpoints
api_router.include_router(business_semantic.router, prefix="/business-semantic", tags=["business-semantic"])

# File Upload endpoints
api_router.include_router(file_upload.router, prefix="/file-upload", tags=["file-upload"])

# Vector Metadata endpoints
api_router.include_router(vector_metadata.router, prefix="/vector-metadata", tags=["vector-metadata"])

# Report system endpoints
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(database_metadata.router, prefix="/database-metadata", tags=["database-metadata"])

# Include Text2SQL router for AI-powered features
api_router.include_router(text2sql.router, prefix="/text2sql", tags=["text2sql"])

# Dashboard endpoints
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])