#!/usr/bin/env python3
"""Fix the middleware issue"""

content = '''from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
import uuid
from loguru import logger

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID
        request_id = str(uuid.uuid4())
        
        # Log request
        start_time = time.time()
        logger.info(f"Request {request_id}: {request.method} {request.url.path}")
        
        # Process request
        try:
            response = await call_next(request)
            
            # Add security headers
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            response.headers["X-Request-ID"] = request_id
            
            # Remove server header (correct way)
            if "server" in response.headers:
                del response.headers["server"]
            
            # Log response
            process_time = time.time() - start_time
            logger.info(
                f"Request {request_id} completed: "
                f"status={response.status_code} "
                f"duration={process_time:.3f}s"
            )
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"Request {request_id} failed: "
                f"error={str(e)} "
                f"duration={process_time:.3f}s"
            )
            raise


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Basic rate limiting middleware"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.request_counts = {}
        self.window_size = 60  # 1 minute
        self.max_requests = 100
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Skip rate limiting for health checks
        if request.url.path == "/api/health":
            return await call_next(request)
        
        # Check rate limit
        current_time = time.time()
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = []
        
        # Remove old requests
        self.request_counts[client_ip] = [
            timestamp for timestamp in self.request_counts[client_ip]
            if current_time - timestamp < self.window_size
        ]
        
        # Check if rate limit exceeded
        if len(self.request_counts[client_ip]) >= self.max_requests:
            logger.warning(f"Rate limit exceeded for {client_ip}")
            return Response(
                content="Rate limit exceeded",
                status_code=429,
                headers={"Retry-After": str(self.window_size)}
            )
        
        # Add current request
        self.request_counts[client_ip].append(current_time)
        
        # Process request
        return await call_next(request)
'''

with open('/tmp/middleware.py', 'w') as f:
    f.write(content)

print("Middleware file created")