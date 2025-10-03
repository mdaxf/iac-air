"""
Rate Limiting and Cost Control Middleware for AI API endpoints
"""
import time
import json
from typing import Dict, Optional, Any
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import asyncio
from collections import defaultdict, deque
from datetime import datetime, timedelta

from app.core.logging_config import Logger
from app.core.config import settings


class RateLimitConfig:
    """Rate limiting configuration"""

    # General API limits (per minute)
    GENERAL_REQUESTS_PER_MINUTE = 100
    GENERAL_REQUESTS_PER_HOUR = 1000

    # AI API specific limits (per minute)
    AI_REQUESTS_PER_MINUTE = 10
    AI_REQUESTS_PER_HOUR = 100
    AI_REQUESTS_PER_DAY = 500

    # Cost control limits (in USD)
    DAILY_COST_LIMIT = 50.0
    HOURLY_COST_LIMIT = 10.0

    # Token usage limits
    DAILY_TOKEN_LIMIT = 100000
    HOURLY_TOKEN_LIMIT = 20000

    # AI endpoints that should be rate limited
    AI_ENDPOINTS = [
        "/api/v1/text2sql/generate",
        "/api/v1/chat/message",
        "/api/v1/vector/search",
        "/api/v1/admin/databases/*/generate-vectors"
    ]


class UserLimitTracker:
    """Track rate limits and costs per user"""

    def __init__(self):
        self.request_history: Dict[str, Dict[str, deque]] = defaultdict(
            lambda: {
                'general_minute': deque(),
                'general_hour': deque(),
                'ai_minute': deque(),
                'ai_hour': deque(),
                'ai_day': deque(),
            }
        )
        self.cost_tracking: Dict[str, Dict[str, float]] = defaultdict(
            lambda: {
                'hourly_cost': 0.0,
                'daily_cost': 0.0,
                'hourly_tokens': 0,
                'daily_tokens': 0,
                'last_hourly_reset': time.time(),
                'last_daily_reset': time.time(),
            }
        )
        self.cleanup_interval = 3600  # Clean up every hour
        self.last_cleanup = time.time()

    def cleanup_old_records(self):
        """Clean up old tracking records"""
        current_time = time.time()
        if current_time - self.last_cleanup < self.cleanup_interval:
            return

        cutoff_time = current_time - 86400  # 24 hours ago

        for user_id in list(self.request_history.keys()):
            user_history = self.request_history[user_id]

            # Clean up request history
            for period_type in user_history:
                while (user_history[period_type] and
                       user_history[period_type][0] < cutoff_time):
                    user_history[period_type].popleft()

        self.last_cleanup = current_time

    def reset_cost_counters(self, user_id: str):
        """Reset cost counters based on time periods"""
        current_time = time.time()
        user_costs = self.cost_tracking[user_id]

        # Reset hourly counters
        if current_time - user_costs['last_hourly_reset'] > 3600:
            user_costs['hourly_cost'] = 0.0
            user_costs['hourly_tokens'] = 0
            user_costs['last_hourly_reset'] = current_time

        # Reset daily counters
        if current_time - user_costs['last_daily_reset'] > 86400:
            user_costs['daily_cost'] = 0.0
            user_costs['daily_tokens'] = 0
            user_costs['last_daily_reset'] = current_time

    def check_rate_limit(self, user_id: str, endpoint: str, is_ai_endpoint: bool) -> Optional[Dict[str, Any]]:
        """Check if request should be rate limited"""
        current_time = time.time()
        user_history = self.request_history[user_id]

        # Clean up old records
        self.cleanup_old_records()

        # Check general API limits
        minute_requests = [t for t in user_history['general_minute'] if current_time - t < 60]
        hour_requests = [t for t in user_history['general_hour'] if current_time - t < 3600]

        if len(minute_requests) >= RateLimitConfig.GENERAL_REQUESTS_PER_MINUTE:
            return {
                "error": "Rate limit exceeded",
                "message": f"Too many requests. Limit: {RateLimitConfig.GENERAL_REQUESTS_PER_MINUTE} per minute",
                "retry_after": 60 - (current_time - minute_requests[0]),
                "limit_type": "general_minute"
            }

        if len(hour_requests) >= RateLimitConfig.GENERAL_REQUESTS_PER_HOUR:
            return {
                "error": "Rate limit exceeded",
                "message": f"Too many requests. Limit: {RateLimitConfig.GENERAL_REQUESTS_PER_HOUR} per hour",
                "retry_after": 3600 - (current_time - hour_requests[0]),
                "limit_type": "general_hour"
            }

        # Check AI-specific limits
        if is_ai_endpoint:
            ai_minute_requests = [t for t in user_history['ai_minute'] if current_time - t < 60]
            ai_hour_requests = [t for t in user_history['ai_hour'] if current_time - t < 3600]
            ai_day_requests = [t for t in user_history['ai_day'] if current_time - t < 86400]

            if len(ai_minute_requests) >= RateLimitConfig.AI_REQUESTS_PER_MINUTE:
                return {
                    "error": "AI rate limit exceeded",
                    "message": f"Too many AI requests. Limit: {RateLimitConfig.AI_REQUESTS_PER_MINUTE} per minute",
                    "retry_after": 60 - (current_time - ai_minute_requests[0]),
                    "limit_type": "ai_minute"
                }

            if len(ai_hour_requests) >= RateLimitConfig.AI_REQUESTS_PER_HOUR:
                return {
                    "error": "AI rate limit exceeded",
                    "message": f"Too many AI requests. Limit: {RateLimitConfig.AI_REQUESTS_PER_HOUR} per hour",
                    "retry_after": 3600 - (current_time - ai_hour_requests[0]),
                    "limit_type": "ai_hour"
                }

            if len(ai_day_requests) >= RateLimitConfig.AI_REQUESTS_PER_DAY:
                return {
                    "error": "AI rate limit exceeded",
                    "message": f"Too many AI requests. Limit: {RateLimitConfig.AI_REQUESTS_PER_DAY} per day",
                    "retry_after": 86400 - (current_time - ai_day_requests[0]),
                    "limit_type": "ai_day"
                }

        return None

    def check_cost_limits(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Check if cost limits are exceeded"""
        self.reset_cost_counters(user_id)
        user_costs = self.cost_tracking[user_id]

        if user_costs['daily_cost'] >= RateLimitConfig.DAILY_COST_LIMIT:
            return {
                "error": "Cost limit exceeded",
                "message": f"Daily cost limit of ${RateLimitConfig.DAILY_COST_LIMIT} exceeded",
                "current_cost": user_costs['daily_cost'],
                "limit_type": "daily_cost"
            }

        if user_costs['hourly_cost'] >= RateLimitConfig.HOURLY_COST_LIMIT:
            return {
                "error": "Cost limit exceeded",
                "message": f"Hourly cost limit of ${RateLimitConfig.HOURLY_COST_LIMIT} exceeded",
                "current_cost": user_costs['hourly_cost'],
                "limit_type": "hourly_cost"
            }

        if user_costs['daily_tokens'] >= RateLimitConfig.DAILY_TOKEN_LIMIT:
            return {
                "error": "Token limit exceeded",
                "message": f"Daily token limit of {RateLimitConfig.DAILY_TOKEN_LIMIT} exceeded",
                "current_tokens": user_costs['daily_tokens'],
                "limit_type": "daily_tokens"
            }

        if user_costs['hourly_tokens'] >= RateLimitConfig.HOURLY_TOKEN_LIMIT:
            return {
                "error": "Token limit exceeded",
                "message": f"Hourly token limit of {RateLimitConfig.HOURLY_TOKEN_LIMIT} exceeded",
                "current_tokens": user_costs['hourly_tokens'],
                "limit_type": "hourly_tokens"
            }

        return None

    def record_request(self, user_id: str, endpoint: str, is_ai_endpoint: bool):
        """Record a request for rate limiting"""
        current_time = time.time()
        user_history = self.request_history[user_id]

        # Record general request
        user_history['general_minute'].append(current_time)
        user_history['general_hour'].append(current_time)

        # Record AI request
        if is_ai_endpoint:
            user_history['ai_minute'].append(current_time)
            user_history['ai_hour'].append(current_time)
            user_history['ai_day'].append(current_time)

    def record_cost(self, user_id: str, cost: float, tokens: int):
        """Record cost and token usage"""
        self.reset_cost_counters(user_id)
        user_costs = self.cost_tracking[user_id]

        user_costs['hourly_cost'] += cost
        user_costs['daily_cost'] += cost
        user_costs['hourly_tokens'] += tokens
        user_costs['daily_tokens'] += tokens


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting and cost control"""

    def __init__(self, app):
        super().__init__(app)
        self.tracker = UserLimitTracker()

    def _get_user_id(self, request: Request) -> str:
        """Extract user ID from request"""
        # Try to get user ID from various sources
        user_id = None

        # From JWT token in Authorization header
        if hasattr(request.state, 'user') and request.state.user:
            user_id = str(request.state.user.id)

        # From query parameter (fallback for testing)
        if not user_id:
            user_id = request.query_params.get('user_id')

        # From client IP as last resort
        if not user_id:
            user_id = f"ip_{request.client.host}" if request.client else "unknown"

        return user_id

    def _is_ai_endpoint(self, path: str) -> bool:
        """Check if endpoint is an AI endpoint"""
        for ai_path in RateLimitConfig.AI_ENDPOINTS:
            if ai_path.endswith("*"):
                if path.startswith(ai_path[:-1]):
                    return True
            elif path == ai_path:
                return True
        return False

    def _estimate_request_cost(self, request: Request, response: Response) -> tuple[float, int]:
        """Estimate the cost and token usage of a request"""
        # This is a simplified cost estimation
        # In a real implementation, you'd get actual costs from AI service responses

        path = request.url.path
        cost = 0.0
        tokens = 0

        if "/text2sql/generate" in path:
            # Estimated cost for Text2SQL generation
            cost = 0.01  # $0.01 per request
            tokens = 500  # Estimated tokens
        elif "/chat/message" in path:
            # Estimated cost for chat messages
            cost = 0.005  # $0.005 per message
            tokens = 250  # Estimated tokens
        elif "/vector/search" in path:
            # Estimated cost for vector search
            cost = 0.001  # $0.001 per search
            tokens = 100  # Estimated tokens
        elif "/generate-vectors" in path:
            # Higher cost for vector generation
            cost = 0.05  # $0.05 per generation job
            tokens = 1000  # Estimated tokens

        return cost, tokens

    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting"""
        start_time = time.time()
        user_id = self._get_user_id(request)
        endpoint = request.url.path
        is_ai_endpoint = self._is_ai_endpoint(endpoint)

        # Skip rate limiting for SSE endpoints (they maintain long-lived connections)
        if "/stream/" in endpoint or endpoint.endswith("/stream"):
            return await call_next(request)

        try:
            # Check rate limits
            rate_limit_error = self.tracker.check_rate_limit(user_id, endpoint, is_ai_endpoint)
            if rate_limit_error:
                Logger.warning(f"Rate limit exceeded for user {user_id} on {endpoint}", extra={
                    "user_id": user_id,
                    "endpoint": endpoint,
                    "limit_type": rate_limit_error.get("limit_type"),
                })

                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content=rate_limit_error,
                    headers={"Retry-After": str(int(rate_limit_error.get("retry_after", 60)))}
                )

            # Check cost limits for AI endpoints
            if is_ai_endpoint:
                cost_limit_error = self.tracker.check_cost_limits(user_id)
                if cost_limit_error:
                    Logger.warning(f"Cost limit exceeded for user {user_id}", extra={
                        "user_id": user_id,
                        "endpoint": endpoint,
                        "limit_type": cost_limit_error.get("limit_type"),
                    })

                    return JSONResponse(
                        status_code=status.HTTP_402_PAYMENT_REQUIRED,
                        content=cost_limit_error
                    )

            # Record the request
            self.tracker.record_request(user_id, endpoint, is_ai_endpoint)

            # Process the request
            response = await call_next(request)

            # Record cost for AI endpoints
            if is_ai_endpoint and response.status_code < 400:
                cost, tokens = self._estimate_request_cost(request, response)
                if cost > 0:
                    self.tracker.record_cost(user_id, cost, tokens)

                    Logger.info(f"AI request cost recorded", extra={
                        "user_id": user_id,
                        "endpoint": endpoint,
                        "cost": cost,
                        "tokens": tokens,
                        "processing_time": time.time() - start_time,
                    })

            return response

        except Exception as e:
            Logger.error(f"Error in rate limit middleware: {str(e)}", extra={
                "user_id": user_id,
                "endpoint": endpoint,
                "error": str(e),
            })

            # Don't block requests due to middleware errors
            return await call_next(request)


# Global instance
rate_limiter = RateLimitMiddleware