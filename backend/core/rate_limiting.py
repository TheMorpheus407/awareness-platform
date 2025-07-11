"""Enhanced rate limiting with user-based and role-based limits."""

import asyncio
import time
from typing import Callable, Dict, Optional, Tuple
from collections import defaultdict
from datetime import datetime, timedelta

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from core.config import settings
from core.logging import logger
from core.cache import cache


class RateLimitConfig:
    """Rate limit configuration for different user types and endpoints."""
    
    # Default limits by user role
    ROLE_LIMITS = {
        "anonymous": "10/minute;100/hour;1000/day",
        "employee": "30/minute;500/hour;5000/day",
        "manager": "60/minute;1000/hour;10000/day",
        "admin": "120/minute;2000/hour;20000/day",
        "api_key": "100/minute;2000/hour;20000/day"
    }
    
    # Endpoint-specific limits
    ENDPOINT_LIMITS = {
        # Auth endpoints - stricter limits
        "/api/v1/auth/login": "5/minute;20/hour",
        "/api/v1/auth/register": "3/minute;10/hour",
        "/api/v1/auth/password-reset": "3/minute;10/hour",
        "/api/v1/auth/verify-email": "5/minute;20/hour",
        
        # API endpoints
        "/api/v1/users": "30/minute;300/hour",
        "/api/v1/companies": "20/minute;200/hour",
        "/api/v1/courses": "50/minute;500/hour",
        "/api/v1/phishing": "10/minute;100/hour",
        
        # File uploads
        "/api/v1/upload": "5/minute;20/hour",
        
        # Health checks - no limit
        "/api/health": None,
        "/health": None
    }
    
    # Burst allowance configuration
    BURST_MULTIPLIER = 1.5  # Allow 50% burst over limit
    
    # Sliding window configuration
    WINDOW_SIZES = {
        "second": 1,
        "minute": 60,
        "hour": 3600,
        "day": 86400
    }


class EnhancedRateLimiter:
    """Enhanced rate limiter with user-based and sliding window support."""
    
    def __init__(self):
        """Initialize the rate limiter."""
        self.cache = cache
        self.config = RateLimitConfig()
        self.request_history = defaultdict(list)
        self._cleanup_task = None
    
    async def start(self):
        """Start the cleanup task."""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def stop(self):
        """Stop the cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
    
    async def _cleanup_loop(self):
        """Periodically clean up old request history."""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                await self._cleanup_old_requests()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in rate limiter cleanup: {e}")
    
    async def _cleanup_old_requests(self):
        """Remove old requests from history."""
        now = time.time()
        cutoff = now - 86400  # Keep 24 hours of history
        
        for key in list(self.request_history.keys()):
            self.request_history[key] = [
                req_time for req_time in self.request_history[key]
                if req_time > cutoff
            ]
            
            if not self.request_history[key]:
                del self.request_history[key]
    
    def _get_user_info(self, request: Request) -> Tuple[str, str]:
        """Get user identification and role from request."""
        # Check for authenticated user
        if hasattr(request.state, "user") and request.state.user:
            user_id = str(request.state.user.id)
            user_role = request.state.user.role
            return f"user:{user_id}", user_role
        
        # Check for API key
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"api_key:{api_key[:8]}", "api_key"
        
        # Fall back to IP address
        client_ip = get_remote_address(request)
        return f"ip:{client_ip}", "anonymous"
    
    def _parse_limit_string(self, limit_string: str) -> Dict[str, int]:
        """Parse limit string like '10/minute;100/hour' into dict."""
        limits = {}
        
        if not limit_string:
            return limits
        
        for limit_part in limit_string.split(";"):
            count, period = limit_part.strip().split("/")
            limits[period] = int(count)
        
        return limits
    
    def _get_applicable_limit(self, request: Request, user_role: str) -> Optional[str]:
        """Get the most restrictive applicable limit for the request."""
        path = request.url.path
        
        # Check endpoint-specific limits first
        for endpoint_pattern, limit in self.config.ENDPOINT_LIMITS.items():
            if path.startswith(endpoint_pattern):
                if limit is None:
                    return None  # No rate limit for this endpoint
                return limit
        
        # Fall back to role-based limits
        return self.config.ROLE_LIMITS.get(user_role, self.config.ROLE_LIMITS["anonymous"])
    
    async def check_rate_limit(self, request: Request) -> Tuple[bool, Optional[int]]:
        """
        Check if request exceeds rate limit.
        
        Returns:
            Tuple of (is_allowed, retry_after_seconds)
        """
        user_key, user_role = self._get_user_info(request)
        limit_string = self._get_applicable_limit(request, user_role)
        
        if not limit_string:
            return True, None  # No limit applies
        
        limits = self._parse_limit_string(limit_string)
        now = time.time()
        
        # Track request in history
        self.request_history[user_key].append(now)
        
        # Check each limit
        for period, max_requests in limits.items():
            window_size = self.config.WINDOW_SIZES.get(period, 60)
            cutoff_time = now - window_size
            
            # Count requests in window
            recent_requests = [
                req_time for req_time in self.request_history[user_key]
                if req_time > cutoff_time
            ]
            
            # Apply burst allowance
            effective_limit = int(max_requests * self.config.BURST_MULTIPLIER)
            
            if len(recent_requests) > effective_limit:
                # Calculate retry after
                oldest_request_in_window = min(recent_requests)
                retry_after = int(window_size - (now - oldest_request_in_window)) + 1
                
                logger.warning(
                    f"Rate limit exceeded for {user_key} on {request.url.path}: "
                    f"{len(recent_requests)}/{max_requests} requests in {period}"
                )
                
                return False, retry_after
        
        return True, None
    
    async def get_rate_limit_info(self, request: Request) -> Dict[str, any]:
        """Get current rate limit information for the request."""
        user_key, user_role = self._get_user_info(request)
        limit_string = self._get_applicable_limit(request, user_role)
        
        if not limit_string:
            return {"limited": False}
        
        limits = self._parse_limit_string(limit_string)
        now = time.time()
        info = {
            "limited": True,
            "limits": {},
            "current_usage": {}
        }
        
        for period, max_requests in limits.items():
            window_size = self.config.WINDOW_SIZES.get(period, 60)
            cutoff_time = now - window_size
            
            recent_requests = [
                req_time for req_time in self.request_history.get(user_key, [])
                if req_time > cutoff_time
            ]
            
            info["limits"][period] = max_requests
            info["current_usage"][period] = len(recent_requests)
        
        return info


class EnhancedRateLimitMiddleware(BaseHTTPMiddleware):
    """Enhanced rate limiting middleware with user-based limits."""
    
    def __init__(self, app):
        """Initialize the middleware."""
        super().__init__(app)
        self.limiter = EnhancedRateLimiter()
        
        # Start cleanup task
        asyncio.create_task(self.limiter.start())
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply rate limiting to requests."""
        # Check rate limit
        is_allowed, retry_after = await self.limiter.check_rate_limit(request)
        
        if not is_allowed:
            # Get rate limit info for response
            limit_info = await self.limiter.get_rate_limit_info(request)
            
            response = JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded",
                    "retry_after": retry_after,
                    "limits": limit_info
                }
            )
            
            # Add rate limit headers
            response.headers["Retry-After"] = str(retry_after)
            response.headers["X-RateLimit-Limit"] = str(limit_info["limits"])
            response.headers["X-RateLimit-Remaining"] = "0"
            response.headers["X-RateLimit-Reset"] = str(int(time.time()) + retry_after)
            
            return response
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to successful responses
        limit_info = await self.limiter.get_rate_limit_info(request)
        if limit_info.get("limited"):
            # Find the most restrictive limit
            min_remaining = float('inf')
            for period, limit in limit_info["limits"].items():
                used = limit_info["current_usage"][period]
                remaining = limit - used
                if remaining < min_remaining:
                    min_remaining = remaining
            
            response.headers["X-RateLimit-Limit"] = str(limit_info["limits"])
            response.headers["X-RateLimit-Remaining"] = str(max(0, min_remaining))
        
        return response


# Backwards compatibility - create standard limiter for use with decorators
def get_limiter_key_func(request: Request) -> str:
    """Get rate limit key for request."""
    # Check for authenticated user
    if hasattr(request.state, "user") and request.state.user:
        return f"user:{request.state.user.id}"
    
    # Check for API key
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return f"api_key:{api_key[:8]}"
    
    # Fall back to IP address
    return get_remote_address(request)


# Create standard limiter instance for decorator usage
standard_limiter = Limiter(
    key_func=get_limiter_key_func,
    default_limits=["100/hour"],
    enabled=settings.RATE_LIMIT_ENABLED,
    storage_uri=settings.RATE_LIMIT_STORAGE_URL
)