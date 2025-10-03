"""
Global Exception Handlers and Custom Exceptions
"""
from typing import Any, Dict, Optional
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
import traceback
import uuid

from app.core.logging_config import Logger


class AIDataAnalyticsException(Exception):
    """Base exception for AI Data Analytics Platform"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class DatabaseConnectionError(AIDataAnalyticsException):
    """Raised when database connection fails"""
    pass


class VectorSearchError(AIDataAnalyticsException):
    """Raised when vector search operations fail"""
    pass


class Text2SQLError(AIDataAnalyticsException):
    """Raised when Text2SQL operations fail"""
    pass


class ChatServiceError(AIDataAnalyticsException):
    """Raised when chat service operations fail"""
    pass


class AuthenticationError(AIDataAnalyticsException):
    """Raised when authentication fails"""
    pass


class AuthorizationError(AIDataAnalyticsException):
    """Raised when authorization fails"""
    pass


class ValidationError(AIDataAnalyticsException):
    """Raised when data validation fails"""
    pass


async def database_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Handle SQLAlchemy database exceptions"""
    error_id = str(uuid.uuid4())

    Logger.error(f"Database error [{error_id}]: {str(exc)}", extra={
        "error_id": error_id,
        "exception_type": type(exc).__name__,
        "traceback": traceback.format_exc(),
        "request_url": str(request.url),
        "request_method": request.method,
    })

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Database Error",
            "message": "A database error occurred. Please try again later.",
            "error_id": error_id,
            "type": "database_error"
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle Pydantic validation exceptions"""
    error_id = str(uuid.uuid4())

    Logger.warning(f"Validation error [{error_id}]: {str(exc)}", extra={
        "error_id": error_id,
        "validation_errors": exc.errors(),
        "request_url": str(request.url),
        "request_method": request.method,
    })

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "message": "Invalid request data",
            "details": exc.errors(),
            "error_id": error_id,
            "type": "validation_error"
        }
    )


async def response_validation_exception_handler(request: Request, exc: ResponseValidationError) -> JSONResponse:
    """Handle Pydantic response validation exceptions"""
    error_id = str(uuid.uuid4())

    Logger.error(f"Response validation error [{error_id}]: {str(exc)}", extra={
        "error_id": error_id,
        "validation_errors": exc.errors() if hasattr(exc, 'errors') else str(exc),
        "request_url": str(request.url),
        "request_method": request.method,
        "traceback": traceback.format_exc(),
    })

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "An internal error occurred while processing the response",
            "error_id": error_id,
            "type": "response_validation_error"
        }
    )


async def ai_data_analytics_exception_handler(request: Request, exc: AIDataAnalyticsException) -> JSONResponse:
    """Handle custom AI Data Analytics exceptions"""
    error_id = str(uuid.uuid4())

    # Determine status code based on exception type
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    if isinstance(exc, AuthenticationError):
        status_code = status.HTTP_401_UNAUTHORIZED
    elif isinstance(exc, AuthorizationError):
        status_code = status.HTTP_403_FORBIDDEN
    elif isinstance(exc, ValidationError):
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    elif isinstance(exc, DatabaseConnectionError):
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    Logger.error(f"Platform error [{error_id}]: {exc.message}", extra={
        "error_id": error_id,
        "exception_type": type(exc).__name__,
        "details": exc.details,
        "request_url": str(request.url),
        "request_method": request.method,
    })

    return JSONResponse(
        status_code=status_code,
        content={
            "error": type(exc).__name__,
            "message": exc.message,
            "details": exc.details,
            "error_id": error_id,
            "type": "platform_error"
        }
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions"""
    error_id = str(uuid.uuid4())

    Logger.error(f"Unexpected error [{error_id}]: {str(exc)}", extra={
        "error_id": error_id,
        "exception_type": type(exc).__name__,
        "traceback": traceback.format_exc(),
        "request_url": str(request.url),
        "request_method": request.method,
    })

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred. Please try again later.",
            "error_id": error_id,
            "type": "general_error"
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTP exceptions with enhanced logging"""
    error_id = str(uuid.uuid4())

    # Log the exception based on its severity
    if exc.status_code >= 500:
        Logger.error(f"HTTP error [{error_id}]: {exc.detail}", extra={
            "error_id": error_id,
            "status_code": exc.status_code,
            "request_url": str(request.url),
            "request_method": request.method,
        })
    else:
        Logger.warning(f"HTTP error [{error_id}]: {exc.detail}", extra={
            "error_id": error_id,
            "status_code": exc.status_code,
            "request_url": str(request.url),
            "request_method": request.method,
        })

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP Error",
            "message": exc.detail,
            "error_id": error_id,
            "type": "http_error"
        }
    )