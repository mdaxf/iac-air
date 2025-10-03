import time
import json
import uuid
from typing import Callable, Optional
from datetime import datetime
from urllib.parse import parse_qs, urlparse
import asyncio

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db_session
from app.core.logging_config import Logger, debug_logger as app_logger
from app.models.api_history import APICallHistory
from app.core.auth import get_current_user

class APIHistoryMiddleware_1(BaseHTTPMiddleware):
    """Middleware to track API call history"""

    def __init__(self, app):
        super().__init__(app)
        self.sensitive_headers = {
            'authorization', 'cookie', 'x-api-key', 'x-auth-token',
            'set-cookie', 'www-authenticate'
        }
        self.sensitive_paths = {
            '/auth/login', '/auth/change-password', '/admin/users'
        }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:

        app_logger.debug(f"API History Middleare is called for {request.method} {request.url.path}!")

        if not settings.API_HISTORY_ENABLED:
            app_logger.debug(f"API History enabled is false")
            return await call_next(request)

        # Skip health checks and static files
        if self._should_skip_tracking(request):
            app_logger.debug(f"API History record is skipped for request {request}")
            return await call_next(request)

        # Generate correlation ID
        correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id

        # Start timing
        start_time = time.time()
        start_datetime = datetime.utcnow()

        # Extract request information
        app_logger.debug(f"API History middleware to extract request information from {request}")
        request_info = await self._extract_request_info(request)

        # Initialize history record
        app_logger.debug(f"Create an API History record object")
        history_record = APICallHistory(
            method=request.method,
            path=request.url.path,
            full_url=str(request.url),
            query_params=dict(request.query_params) if request.query_params else None,
            client_ip=self._get_client_ip(request),
            user_agent=request.headers.get("user-agent"),
            referer=request.headers.get("referer"),
            request_headers=self._filter_sensitive_headers(dict(request.headers)),
            request_body=request_info.get('body'),
            request_size=request_info.get('size'),
            start_time=start_datetime,
            endpoint_name=self._get_endpoint_name(request),
            api_version=self._extract_api_version(request),
            source=self._determine_source(request),
            correlation_id=correlation_id
        )

        response = None
        error_occurred = False

        try:
            # Process the request
            app_logger.debug(f"Wait for the API call response")

            try:
                response = await call_next(request)
            except Exception as e:
                app_logger.error(f"Error processing request {request.method} {request.url.path}: {e}")
                # Create error response if processing fails
                from starlette.responses import JSONResponse
                response = JSONResponse(
                    status_code=500,
                    content={"detail": "Internal server error"}
                )

            #response = await call_next(request)
            app_logger.debug(f"API call with response: {response}")
            # Calculate timing
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            app_logger.debug(f"APII call take {duration_ms} ms from {start_time} to {end_time}")

            # Extract user information if available
            app_logger.debug(f"Get user information")
            user_info = self._extract_user_info(request)
            if user_info:
                history_record.user_id = user_info.get('user_id')
                history_record.username = user_info.get('username')
                history_record.is_admin = str(user_info.get('is_admin', False)).lower()

            # Extract response information
            app_logger.debug(f"Extract response information {response}")
            response_info = await self._extract_response_info(response)

            # Update history record
            history_record.end_time = datetime.utcnow()
            history_record.duration_ms = duration_ms
            history_record.status_code = response.status_code
            history_record.response_headers = self._filter_sensitive_headers(dict(response.headers))
            history_record.response_body = response_info.get('body')
            history_record.response_size = response_info.get('size')

            # Set error_message for error status codes
            if response.status_code >= 400:
                error_message = f"HTTP {response.status_code}"
                # Try to extract error detail from response body if available
                if response_info.get('body'):
                    try:
                        if isinstance(response_info['body'], dict) and 'detail' in response_info['body']:
                            error_message = f"{error_message}: {response_info['body']['detail']}"
                        elif isinstance(response_info['body'], str):
                            error_message = f"{error_message}: {response_info['body'][:500]}"
                    except Exception:
                        pass
                history_record.error_message = error_message[:1000]  # Truncate long messages

            app_logger.debug(f"Updated api history record:{history_record}")
        except Exception as e:
            app_logger.debug(f"Exception: {str(e)}")
            error_occurred = True
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000

            # Update history record with error info
            history_record.end_time = datetime.utcnow()
            history_record.duration_ms = duration_ms
            history_record.status_code = 500
            history_record.error_message = str(e)[:1000]  # Truncate long error messages

            Logger.error(f"Error in API request {correlation_id}: {str(e)}")

        finally:
            # Save to database (async, non-blocking)
            app_logger.debug(f"Save history to db: {history_record}")
            try:
                await self._save_history_record(history_record)
            except Exception as e:
                app_logger.debug(f"Failed to save API history record: {str(e)}")
                Logger.error(f"Failed to save API history record: {str(e)}")

            # Re-raise the original exception if there was one
            if error_occurred and response is None:
                app_logger.debug(f"Failed to save API history record")
                raise

        return response

    def _should_skip_tracking(self, request: Request) -> bool:
        """Determine if this request should be skipped from tracking"""
        path = request.url.path

        # Skip health checks
        if path in ['/health', '/']:
            return True

        # Skip OpenAPI docs
        if path.startswith('/docs') or path.startswith('/redoc') or path.startswith('/openapi'):
            return True

        # Skip static files
        if any(path.endswith(ext) for ext in ['.js', '.css', '.ico', '.png', '.jpg', '.gif']):
            return True

        return False

    async def _extract_request_info(self, request: Request) -> dict:
        """Extract request body and size information"""
        try:
            # Read request body
            body = await request.body()
            body_size = len(body) if body else 0

            # Store body content if not too large and not sensitive
            body_content = None
            if body_size > 0 and body_size <= settings.API_HISTORY_MAX_REQUEST_SIZE:
                if not self._is_sensitive_path(request.url.path):
                    try:
                        # Try to decode as JSON for better storage
                        body_content = json.loads(body.decode('utf-8'))
                        # Remove sensitive fields
                        if isinstance(body_content, dict):
                            body_content = self._filter_sensitive_data(body_content)
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        # Store as string if not JSON
                        body_content = body.decode('utf-8', errors='ignore')[:1000]

            return {
                'body': body_content,
                'size': body_size
            }
        except Exception as e:
            Logger.warning(f"Failed to extract request info: {str(e)}")
            return {'body': None, 'size': 0}

    async def _extract_response_info(self, response: Response) -> dict:
        """Extract response body and size information"""
        try:
            # Get response size from headers or content
            content_length = response.headers.get('content-length')
            if content_length:
                response_size = int(content_length)
            else:
                response_size = 0

            # For error responses (4xx, 5xx), capture body for error_message
            response_body = None
            if hasattr(response, 'body'):
                try:
                    body_bytes = response.body
                    if body_bytes and len(body_bytes) > 0:
                        if len(body_bytes) <= settings.API_HISTORY_MAX_RESPONSE_SIZE:
                            try:
                                # Try to decode as JSON
                                response_body = json.loads(body_bytes.decode('utf-8'))
                            except (json.JSONDecodeError, UnicodeDecodeError):
                                # Store as string if not JSON
                                response_body = body_bytes.decode('utf-8', errors='ignore')[:1000]
                        response_size = len(body_bytes)
                except Exception:
                    pass

            return {
                'body': response_body,
                'size': response_size
            }
        except Exception as e:
            Logger.warning(f"Failed to extract response info: {str(e)}")
            return {'body': None, 'size': 0}

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address"""
        # Check for forwarded headers first
        forwarded_for = request.headers.get('x-forwarded-for')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()

        real_ip = request.headers.get('x-real-ip')
        if real_ip:
            return real_ip

        # Fallback to direct client IP
        if request.client:
            return request.client.host

        return 'unknown'

    def _extract_user_info(self, request: Request) -> Optional[dict]:
        """Extract user information from request state"""
        if hasattr(request.state, 'user'):
            user = request.state.user
            return {
                'user_id': str(user.id) if hasattr(user, 'id') else None,
                'username': getattr(user, 'username', None),
                'is_admin': getattr(user, 'is_admin', False)
            }
        return None

    def _get_endpoint_name(self, request: Request) -> Optional[str]:
        """Extract friendly endpoint name"""
        if hasattr(request, 'route') and request.route:
            return getattr(request.route, 'name', None)
        return None

    def _extract_api_version(self, request: Request) -> Optional[str]:
        """Extract API version from path"""
        path_parts = request.url.path.split('/')
        for part in path_parts:
            if part.startswith('v') and part[1:].isdigit():
                return part
        return None

    def _determine_source(self, request: Request) -> str:
        """Determine the source of the request"""
        user_agent = request.headers.get('user-agent', '').lower()

        if 'mobile' in user_agent or 'android' in user_agent or 'iphone' in user_agent:
            return 'mobile'
        elif 'postman' in user_agent:
            return 'postman'
        elif 'curl' in user_agent:
            return 'curl'
        elif 'python' in user_agent or 'requests' in user_agent:
            return 'script'
        elif any(browser in user_agent for browser in ['chrome', 'firefox', 'safari', 'edge']):
            return 'web'
        else:
            return 'api'

    def _filter_sensitive_headers(self, headers: dict) -> dict:
        """Remove sensitive headers from logging"""
        filtered = {}
        for key, value in headers.items():
            if key.lower() not in self.sensitive_headers:
                filtered[key] = value
            else:
                filtered[key] = '[REDACTED]'
        return filtered

    def _filter_sensitive_data(self, data: dict) -> dict:
        """Remove sensitive data from request/response bodies"""
        sensitive_fields = {
            'password', 'token', 'secret', 'key', 'auth', 'authorization',
            'current_password', 'new_password', 'confirm_password'
        }

        filtered = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in sensitive_fields):
                filtered[key] = '[REDACTED]'
            elif isinstance(value, dict):
                filtered[key] = self._filter_sensitive_data(value)
            else:
                filtered[key] = value
        return filtered

    def _is_sensitive_path(self, path: str) -> bool:
        """Check if path contains sensitive data"""
        return any(sensitive_path in path for sensitive_path in self.sensitive_paths)

    async def _save_history_record(self, record: APICallHistory):
        """Save history record to database"""
        try:
            async with get_db_session() as db:
                db.add(record)
                await db.commit()
        except Exception as e:
            Logger.error(f"Failed to save API history record: {str(e)}")
            # Don't raise the exception to avoid breaking the API response


sensitive_headers = {
            'authorization', 'cookie', 'x-api-key', 'x-auth-token',
            'set-cookie', 'www-authenticate'
        }
sensitive_paths = {
            '/auth/login', '/auth/change-password', '/admin/users'
        }

def filter_sensitive_data(data: dict) -> dict:
        """Remove sensitive data from request/response bodies"""

        sensitive_fields = {
            'password', 'token', 'secret', 'key', 'auth', 'authorization',
            'current_password', 'new_password', 'confirm_password'
        }

        filtered = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in sensitive_fields):
                filtered[key] = '[REDACTED]'
            elif isinstance(value, dict):
                filtered[key] = filter_sensitive_data(value)
            else:
                filtered[key] = value
        return filtered

def filter_sensitive_headers(headers: dict) -> dict:
        """Remove sensitive headers from logging"""
        filtered = {}
        for key, value in headers.items():
            if key.lower() not in sensitive_headers:
                filtered[key] = value
            else:
                filtered[key] = '[REDACTED]'
        return filtered

def extract_response_info( response: Response) -> dict:
        """Extract response body and size information"""
        try:
            # Get response size from headers or content
            content_length = response.headers.get('content-length')
            if content_length:
                response_size = int(content_length)
            else:
                response_size = 0

            # For small responses, try to capture body content
            response_body = None
            if response_size > 0 and response_size <= settings.API_HISTORY_MAX_RESPONSE_SIZE:
                # This is complex with streaming responses, so we'll skip body capture for now
                # In a production system, you might want to implement response body capture
                pass

            return {
                'body': response_body,
                'size': response_size
            }
        except Exception as e:
            Logger.warning(f"Failed to extract response info: {str(e)}")
            return {'body': None, 'size': 0}
        
def state_to_dict(state):
    return {k: v for k, v in vars(state).get("_state", {}).items()}

async def extract_user_info(request: Request) -> Optional[dict]:
        """Extract user information from request state"""
        app_logger.debug(f"Extract user information from request state: {state_to_dict(request.state)}")

        if hasattr(request.state, 'user'):
            user = request.state.user
            if user:
                return {
                    'user_id': str(user.id) if hasattr(user, 'id') else None,
                    'username': getattr(user, 'username', None),
                    'is_admin': getattr(user, 'is_admin', False)
                }

        app_logger.debug(f"There is no user object in the request.state")
        # Cannot extract user from middleware context - user should be set in request.state
        return None

async def log_api_call_async(endpoint: str, method: str, headers: dict, request_data: str,
                             response_status: int, response_size: int, processing_time: int,
                             user_agent: str = None, ip_address: str = None,start_time:datetime = datetime.utcnow, 
                             end_time:datetime = datetime.utcnow, request:Request ={}, response: Response = {}):
    """Log API call to database for tracking and analytics - async version"""
    try:
        app_logger.debug(f"Logging API call async: {method} {endpoint} - Status: {response_status}, Time: {processing_time}ms")
        app_logger.debug(f"API Call Details: endpoint={endpoint}, method={method}, headers={headers}, "
                              f"request_data={request_data}, response_status={response_status}, "
                              f"response_size={response_size}, processing_time={processing_time}, "
                              f"user_agent={user_agent}, ip_address={ip_address}")
        
        await log_api_call(endpoint, method, headers, request_data,
                                 response_status, response_size, processing_time,
                                 user_agent, ip_address,start_time, end_time,request,response)
    except Exception as e:
        app_logger.error(f"Failed to log API call async: {e}")

async def log_api_call(endpoint: str, method: str, headers: dict, request_data: str,
                      response_status: int, response_size: int, processing_time: int,
                      user_agent: str = None, ip_address: str = None,start_time:datetime = datetime.utcnow(), 
                      end_time:datetime = datetime.utcnow(), request:Request ={}, response: Response = {}):
    """Synchronous database logging function"""
    
    response_info = extract_response_info(response)

    try:
        history_record = APICallHistory(
            method= method,
            path=request.url.path,
            full_url=str(request.url),
            query_params= dict(request.query_params) if request.query_params else None,
            client_ip=ip_address,
            user_agent=user_agent,
            referer=request.headers.get("referer"),
            request_headers=headers, #str(headers),
            request_body=request_data,
            request_size=0,
            start_time=start_time,
            endpoint_name=endpoint,
            api_version="v1",
            source=ip_address,
            correlation_id=str(uuid.uuid4()),
             # Update history record
            end_time = end_time,
            duration_ms = processing_time,
            status_code = response_status,
            response_headers = str(filter_sensitive_headers(dict(response.headers))),
            response_body = response_info.get('body'),
            response_size = response_size
        )
        user_info = await extract_user_info(request)
        if user_info:
            history_record.user_id = user_info.get('user_id')
            history_record.username = user_info.get('username')
            history_record.is_admin = str(user_info.get('is_admin', False)).lower()


        await _save_history_record(history_record)

    except Exception as e:
        app_logger.error(f"Failed to log API call to database: {e}")

async def _save_history_record(record: APICallHistory):
        """Save history record to database"""
        try:
            async with get_db_session() as db:
                db.add(record)
                await db.commit()
        except Exception as e:
            Logger.error(f"Failed to save API history record: {str(e)}")
            # Don't raise the exception to avoid breaking the API response

class APIHistoryMiddleware(BaseHTTPMiddleware):
    """Middleware to track API usage and performance metrics"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        start_datetime = datetime.utcnow()
        # Get request metadata
        endpoint = str(request.url.path)
        method = request.method
        headers = dict(request.headers)
        user_agent = headers.get("user-agent", "")
        ip_address = request.client.host if request.client else ""

        app_logger.debug(f"API Request: {method} {endpoint} from {ip_address}")

        # For request body logging, we'll capture it without consuming the stream
        request_data = ""
        if method in ["POST", "PUT", "PATCH"]:
            try:
                # Get content type and length for logging metadata
                content_type = headers.get("content-type", "")
                content_length = headers.get("content-length", "0")

                if "multipart/form-data" in content_type:
                    request_data = f"<multipart form data {content_length} bytes>"
                elif "application/json" in content_type:
                    request_data = f"<json data {content_length} bytes>"
                elif "application/octet-stream" in content_type:
                    request_data = f"<binary data {content_length} bytes>"
                else:
                    request_data = f"<{content_type} data {content_length} bytes>"

                app_logger.debug(f"Request body info: {request_data}")
            except Exception as e:
                app_logger.debug(f"Failed to get request body info: {e}")
                request_data = "<error reading request metadata>"

        # Process the request without consuming body
        try:
            response = await call_next(request)
        except Exception as e:
            app_logger.error(f"Error processing request {method} {endpoint}: {e}")
            # Create error response if processing fails
            from starlette.responses import JSONResponse
            response = JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"}
            )

        # Calculate processing time
        end_datetime = datetime.utcnow()
        processing_time = int((time.time() - start_time) * 1000)
        app_logger.debug(f"API Response: {method} {endpoint} - Status: {response.status_code}, Time: {processing_time}ms")

        # Get response size
        response_size = 0
        app_logger.debug(f"Response headers: {response.headers}")
        if hasattr(response, 'headers') and 'content-length' in response.headers:
            try:
                app_logger.debug(f"Content-Length header: {response.headers['content-length']}")
                response_size = int(response.headers['content-length'])
            except (ValueError, TypeError):
                app_logger.debug("Invalid Content-Length header value")
                response_size = 0

        # Skip logging for static files, docs, and health checks
        skip_endpoints = ['/static', '/docs', '/openapi', '/redoc', '/favicon.ico', '/health','/api/v1/admin/api-history']
        should_log = not any(endpoint.startswith(skip) for skip in skip_endpoints)

        if should_log:
            # Log asynchronously without blocking the response
            asyncio.create_task(
                log_api_call_async(
                    endpoint=endpoint,
                    method=method,
                    headers=headers,
                    request_data=request_data,
                    response_status=response.status_code,
                    response_size=response_size,
                    processing_time=processing_time,
                    user_agent=user_agent,
                    ip_address=ip_address,
                    start_time= start_datetime,
                    end_time=end_datetime,
                    request=request,
                    response=response
                    )
            )

        return response