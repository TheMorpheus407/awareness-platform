"""Custom middleware for the application."""

import hashlib
import hmac
import secrets
import time
import uuid
from typing import Callable, Optional

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from core.config import settings
from core.logging import logger


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to the response."""
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Only add HSTS in production
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Content Security Policy
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net",
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
            "font-src 'self' https://fonts.gstatic.com",
            "img-src 'self' data: https:",
            "connect-src 'self' https://api.stripe.com",
            "frame-src 'self' https://js.stripe.com https://hooks.stripe.com",
            "object-src 'none'",
            "base-uri 'self'",
            "form-action 'self'",
        ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)
        
        # Permissions Policy
        permissions = [
            "camera=()",
            "microphone=()",
            "geolocation=()",
            "payment=(self)",
            "usb=()",
        ]
        response.headers["Permissions-Policy"] = ", ".join(permissions)
        
        return response


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Add a unique request ID to each request and response."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add request ID to request state and response headers."""
        # Generate or get request ID
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())
        
        # Store request ID in request state
        request.state.request_id = request_id
        
        # Process request
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response


class TimingMiddleware(BaseHTTPMiddleware):
    """Add request timing information to responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Measure request processing time."""
        start_time = time.time()
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = f"{process_time:.3f}"
        
        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Global error handling middleware."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Handle errors globally."""
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            # Log the error with request context
            request_id = getattr(request.state, "request_id", "unknown")
            logger.error(
                f"Unhandled exception in request {request_id}: {exc}",
                exc_info=True,
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "url": str(request.url),
                    "client": request.client.host if request.client else None,
                }
            )
            
            # Return generic error response
            if settings.DEBUG:
                return JSONResponse(
                    status_code=500,
                    content={
                        "detail": str(exc),
                        "type": type(exc).__name__,
                        "request_id": request_id,
                    }
                )
            else:
                return JSONResponse(
                    status_code=500,
                    content={
                        "detail": "Internal server error",
                        "request_id": request_id,
                    }
                )


class RateLimitMiddleware:
    """Rate limiting middleware configuration."""
    
    def __init__(self, app: ASGIApp):
        """Initialize rate limiter."""
        self.app = app
        self.limiter = Limiter(
            key_func=get_remote_address,
            default_limits=[f"{settings.RATE_LIMIT_REQUESTS}/{settings.RATE_LIMIT_PERIOD}seconds"],
            enabled=settings.RATE_LIMIT_ENABLED,
            storage_uri=settings.RATE_LIMIT_STORAGE_URL,
        )
    
    async def __call__(self, scope, receive, send):
        """Apply rate limiting."""
        if scope["type"] == "http":
            # Skip rate limiting for health checks
            if scope["path"] in ["/health", "/api/health", "/api/health/db"]:
                await self.app(scope, receive, send)
                return
        
        await self.app(scope, receive, send)


# Create rate limiter instance
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.RATE_LIMIT_REQUESTS}/{settings.RATE_LIMIT_PERIOD}seconds"],
    enabled=settings.RATE_LIMIT_ENABLED,
    storage_uri=settings.RATE_LIMIT_STORAGE_URL,
)


class CSRFMiddleware(BaseHTTPMiddleware):
    """CSRF protection middleware for FastAPI."""
    
    def __init__(
        self,
        app,
        secret_key: Optional[str] = None,
        cookie_name: str = "csrf_token",
        cookie_secure: bool = True,
        cookie_httponly: bool = True,
        cookie_samesite: str = "strict",
        header_name: str = "X-CSRF-Token",
        safe_methods: set = None,
        exclude_paths: set = None,
        token_length: int = 32,
    ):
        """
        Initialize CSRF middleware.
        
        Args:
            app: The FastAPI application
            secret_key: Secret key for signing tokens (defaults to settings.SECRET_KEY)
            cookie_name: Name of the CSRF cookie
            cookie_secure: Set secure flag on cookie (HTTPS only)
            cookie_httponly: Set httponly flag on cookie
            cookie_samesite: SameSite policy for cookie
            header_name: Name of the CSRF header
            safe_methods: HTTP methods that don't require CSRF protection
            exclude_paths: Paths to exclude from CSRF protection
            token_length: Length of the CSRF token
        """
        super().__init__(app)
        self.secret_key = secret_key or settings.SECRET_KEY
        self.cookie_name = cookie_name
        self.cookie_secure = cookie_secure and settings.is_production
        self.cookie_httponly = cookie_httponly
        self.cookie_samesite = cookie_samesite
        self.header_name = header_name
        self.safe_methods = safe_methods or {"GET", "HEAD", "OPTIONS", "TRACE"}
        self.exclude_paths = exclude_paths or {
            "/api/health",
            "/api/health/db",
            "/health",
            "/api/docs",
            "/api/redoc",
            "/api/openapi.json",
        }
        self.token_length = token_length
    
    def _generate_csrf_token(self) -> str:
        """Generate a new CSRF token."""
        token = secrets.token_urlsafe(self.token_length)
        return token
    
    def _sign_token(self, token: str) -> str:
        """Sign a CSRF token with the secret key."""
        signature = hmac.new(
            self.secret_key.encode(),
            token.encode(),
            hashlib.sha256
        ).hexdigest()
        return f"{token}.{signature}"
    
    def _verify_token(self, signed_token: str) -> bool:
        """Verify a signed CSRF token."""
        try:
            token, signature = signed_token.rsplit(".", 1)
            expected_signature = hmac.new(
                self.secret_key.encode(),
                token.encode(),
                hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(signature, expected_signature)
        except (ValueError, AttributeError):
            return False
    
    def _get_token_from_cookie(self, request: Request) -> Optional[str]:
        """Get CSRF token from cookie."""
        return request.cookies.get(self.cookie_name)
    
    def _get_token_from_header(self, request: Request) -> Optional[str]:
        """Get CSRF token from header."""
        return request.headers.get(self.header_name)
    
    def _should_check_csrf(self, request: Request) -> bool:
        """Check if CSRF protection should be applied to this request."""
        # Skip safe methods
        if request.method in self.safe_methods:
            return False
        
        # Skip excluded paths
        if request.url.path in self.exclude_paths:
            return False
        
        # Skip if path starts with excluded prefix
        for path in self.exclude_paths:
            if request.url.path.startswith(path):
                return False
        
        return True
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request and apply CSRF protection."""
        # Get or generate CSRF token
        csrf_token_cookie = self._get_token_from_cookie(request)
        
        if not csrf_token_cookie:
            # Generate new token for first-time visitors
            csrf_token = self._generate_csrf_token()
            signed_token = self._sign_token(csrf_token)
            request.state.csrf_token = csrf_token
            request.state.csrf_token_new = True
        else:
            # Verify existing token
            if not self._verify_token(csrf_token_cookie):
                logger.warning(
                    f"Invalid CSRF token cookie from {request.client.host}",
                    extra={
                        "method": request.method,
                        "path": request.url.path,
                        "client": request.client.host if request.client else None,
                    }
                )
                # Generate new token if invalid
                csrf_token = self._generate_csrf_token()
                signed_token = self._sign_token(csrf_token)
                request.state.csrf_token = csrf_token
                request.state.csrf_token_new = True
            else:
                # Extract the unsigned token
                csrf_token = csrf_token_cookie.split(".")[0]
                signed_token = csrf_token_cookie
                request.state.csrf_token = csrf_token
                request.state.csrf_token_new = False
        
        # Check CSRF token for state-changing requests
        if self._should_check_csrf(request):
            csrf_token_header = self._get_token_from_header(request)
            
            if not csrf_token_header:
                logger.warning(
                    f"Missing CSRF token header for {request.method} {request.url.path}",
                    extra={
                        "method": request.method,
                        "path": request.url.path,
                        "client": request.client.host if request.client else None,
                    }
                )
                raise HTTPException(
                    status_code=403,
                    detail="CSRF token missing",
                    headers={"X-CSRF-Token-Required": "true"}
                )
            
            # Compare tokens (unsigned versions)
            if not hmac.compare_digest(csrf_token, csrf_token_header):
                logger.warning(
                    f"CSRF token mismatch for {request.method} {request.url.path}",
                    extra={
                        "method": request.method,
                        "path": request.url.path,
                        "client": request.client.host if request.client else None,
                    }
                )
                raise HTTPException(
                    status_code=403,
                    detail="CSRF token invalid"
                )
        
        # Process the request
        response = await call_next(request)
        
        # Set CSRF cookie if new or updated
        if hasattr(request.state, "csrf_token_new") and request.state.csrf_token_new:
            response.set_cookie(
                key=self.cookie_name,
                value=signed_token,
                secure=self.cookie_secure,
                httponly=self.cookie_httponly,
                samesite=self.cookie_samesite,
                max_age=86400,  # 24 hours
                path="/",
            )
            # Also add the unsigned token to response headers for easy access
            response.headers["X-CSRF-Token"] = csrf_token
        
        return response