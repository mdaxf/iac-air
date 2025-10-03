import time
import json
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging_config import Logger


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log API requests and responses"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        # Extract request info
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        method = request.method
        url = str(request.url)

        # Get user info if available
        user_id = getattr(request.state, 'user_id', 'anonymous')

        # Log request
        request_log = {
            "method": method,
            "url": url,
            "client_ip": client_ip,
            "user_agent": user_agent,
            "user_id": user_id
        }

        Logger.access(f"REQUEST: {method} {url} from {client_ip} (User: {user_id})")

        try:
            # Process request
            response = await call_next(request)

            # Calculate response time
            process_time = time.time() - start_time

            # Log response
            response_log = {
                **request_log,
                "status_code": response.status_code,
                "response_time": round(process_time, 3)
            }

            Logger.access(
                f"RESPONSE: {method} {url} - {response.status_code} - {process_time:.3f}s"
            )

            # Log slow requests
            if process_time > 1.0:  # Log requests taking more than 1 second
                Logger.warning(
                    f"SLOW REQUEST: {method} {url} took {process_time:.3f}s",
                    **response_log
                )

            # Add timing header
            response.headers["X-Process-Time"] = str(process_time)

            return response

        except Exception as e:
            process_time = time.time() - start_time

            # Log error
            Logger.error(
                f"REQUEST ERROR: {method} {url} - {str(e)} - {process_time:.3f}s",
                error=str(e),
                **request_log
            )
            raise


class SecurityLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log security-related events"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check for suspicious patterns
        url = str(request.url)
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "")

        # Log suspicious activity
        suspicious_patterns = [
            "sql", "union", "select", "drop", "delete", "insert", "update",
            "script", "javascript", "eval", "exec", "../", "passwd", "etc"
        ]

        for pattern in suspicious_patterns:
            if pattern in url.lower() or pattern in user_agent.lower():
                Logger.security(
                    f"SUSPICIOUS REQUEST: {request.method} {url} from {client_ip}",
                    pattern=pattern,
                    user_agent=user_agent
                )
                break

        response = await call_next(request)

        # Log authentication failures
        if response.status_code == 401:
            Logger.security(
                f"AUTH FAILURE: {request.method} {url} from {client_ip}",
                status_code=response.status_code
            )

        # Log authorization failures
        elif response.status_code == 403:
            Logger.security(
                f"AUTHZ FAILURE: {request.method} {url} from {client_ip}",
                status_code=response.status_code
            )

        return response