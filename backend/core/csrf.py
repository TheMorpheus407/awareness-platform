"""CSRF Protection for the application."""

import secrets
import hashlib
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class CSRFProtection:
    """CSRF Protection implementation."""
    
    def __init__(
        self,
        secret_key: str,
        token_lifetime: int = 3600,  # 1 hour
        cookie_name: str = "csrf_token",
        header_name: str = "X-CSRF-Token",
        safe_methods: set = None,
        exclude_paths: set = None,
    ):
        self.secret_key = secret_key
        self.token_lifetime = token_lifetime
        self.cookie_name = cookie_name
        self.header_name = header_name
        self.safe_methods = safe_methods or {"GET", "HEAD", "OPTIONS", "TRACE"}
        self.exclude_paths = exclude_paths or {"/api/health", "/api/docs", "/api/openapi.json"}
        
    def generate_token(self) -> str:
        """Generate a new CSRF token."""
        token = secrets.token_urlsafe(32)
        timestamp = str(int(datetime.utcnow().timestamp()))
        
        # Create a signed token with timestamp
        message = f"{token}:{timestamp}"
        signature = hashlib.sha256(
            f"{message}:{self.secret_key}".encode()
        ).hexdigest()
        
        return f"{message}:{signature}"
    
    def validate_token(self, token: str) -> bool:
        """Validate a CSRF token."""
        try:
            parts = token.split(":")
            if len(parts) != 3:
                return False
            
            token_value, timestamp, signature = parts
            
            # Check timestamp
            token_time = int(timestamp)
            current_time = int(datetime.utcnow().timestamp())
            
            if current_time - token_time > self.token_lifetime:
                return False
            
            # Verify signature
            message = f"{token_value}:{timestamp}"
            expected_signature = hashlib.sha256(
                f"{message}:{self.secret_key}".encode()
            ).hexdigest()
            
            return secrets.compare_digest(signature, expected_signature)
            
        except (ValueError, AttributeError):
            return False
    
    def get_token_from_request(self, request: Request) -> Optional[str]:
        """Extract CSRF token from request headers or form data."""
        # Check header first
        token = request.headers.get(self.header_name)
        if token:
            return token
        
        # Check form data for traditional form submissions
        if request.headers.get("content-type", "").startswith("application/x-www-form-urlencoded"):
            # This would need to be parsed from the body
            # For now, we'll just use header-based CSRF
            pass
        
        return None


class CSRFMiddleware(BaseHTTPMiddleware):
    """CSRF Protection Middleware."""
    
    def __init__(self, app, csrf_protection: CSRFProtection):
        super().__init__(app)
        self.csrf = csrf_protection
    
    async def dispatch(self, request: Request, call_next):
        # Skip CSRF check for safe methods
        if request.method in self.csrf.safe_methods:
            response = await call_next(request)
            # Add CSRF token to response for GET requests
            if request.method == "GET":
                csrf_token = self.csrf.generate_token()
                response.set_cookie(
                    key=self.csrf.cookie_name,
                    value=csrf_token,
                    httponly=False,  # JavaScript needs to read it
                    secure=True,  # HTTPS only in production
                    samesite="strict",
                    max_age=self.csrf.token_lifetime,
                )
            return response
        
        # Skip excluded paths
        if request.url.path in self.csrf.exclude_paths:
            return await call_next(request)
        
        # Get token from cookie
        cookie_token = request.cookies.get(self.csrf.cookie_name)
        if not cookie_token:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "CSRF cookie not found"},
            )
        
        # Get token from request
        request_token = self.csrf.get_token_from_request(request)
        if not request_token:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "CSRF token not provided"},
            )
        
        # Validate tokens match and are valid
        if not secrets.compare_digest(cookie_token, request_token):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "CSRF token mismatch"},
            )
        
        if not self.csrf.validate_token(cookie_token):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Invalid CSRF token"},
            )
        
        # Token is valid, proceed with request
        response = await call_next(request)
        
        # Rotate token on state-changing requests
        new_token = self.csrf.generate_token()
        response.set_cookie(
            key=self.csrf.cookie_name,
            value=new_token,
            httponly=False,
            secure=True,
            samesite="strict",
            max_age=self.csrf.token_lifetime,
        )
        
        return response


def get_csrf_token(request: Request) -> str:
    """Get or generate CSRF token for templates/API responses."""
    csrf_protection = getattr(request.app.state, "csrf_protection", None)
    if not csrf_protection:
        raise RuntimeError("CSRF protection not configured")
    
    # Check if token exists in cookies
    token = request.cookies.get(csrf_protection.cookie_name)
    if token and csrf_protection.validate_token(token):
        return token
    
    # Generate new token
    return csrf_protection.generate_token()


# Usage example in comments
"""
# In main.py, add CSRF protection:

from core.csrf import CSRFProtection, CSRFMiddleware

# Initialize CSRF protection
csrf_protection = CSRFProtection(
    secret_key=settings.SECRET_KEY,
    exclude_paths={
        "/api/health",
        "/api/docs",
        "/api/openapi.json",
        "/api/v1/auth/login",  # Login endpoint needs special handling
        "/api/v1/auth/register",
    }
)

# Store in app state
app.state.csrf_protection = csrf_protection

# Add middleware
app.add_middleware(CSRFMiddleware, csrf_protection=csrf_protection)

# In frontend, include CSRF token in requests:

const getCsrfToken = () => {
    return document.cookie
        .split('; ')
        .find(row => row.startsWith('csrf_token='))
        ?.split('=')[1];
};

fetch('/api/endpoint', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': getCsrfToken(),
    },
    body: JSON.stringify(data),
});
"""