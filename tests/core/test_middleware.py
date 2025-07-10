"""Tests for middleware."""

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import uuid

from core.middleware import SecurityHeadersMiddleware, RequestIdMiddleware


class TestSecurityHeadersMiddleware:
    """Test security headers middleware."""
    
    def test_security_headers_added(self):
        """Test that security headers are added to responses."""
        app = FastAPI()
        app.add_middleware(SecurityHeadersMiddleware)
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        client = TestClient(app)
        response = client.get("/test")
        
        # Check security headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["X-XSS-Protection"] == "1; mode=block"
        assert response.headers["Strict-Transport-Security"] == "max-age=31536000; includeSubDomains"
        assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
        assert response.headers["Permissions-Policy"] == "geolocation=(), microphone=(), camera=()"
        assert "Content-Security-Policy" in response.headers
        
        # Server header should be removed
        assert "server" not in response.headers
    
    def test_csp_header_content(self):
        """Test Content Security Policy header content."""
        app = FastAPI()
        app.add_middleware(SecurityHeadersMiddleware)
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        client = TestClient(app)
        response = client.get("/test")
        
        csp = response.headers["Content-Security-Policy"]
        
        # Check CSP directives
        assert "default-src 'self'" in csp
        assert "script-src 'self'" in csp
        assert "style-src 'self'" in csp
        assert "font-src 'self'" in csp
        assert "img-src 'self'" in csp
        assert "connect-src 'self'" in csp
        assert "frame-ancestors 'none'" in csp
        assert "base-uri 'self'" in csp
        assert "form-action 'self'" in csp
    
    def test_middleware_preserves_response(self):
        """Test that middleware doesn't alter response body."""
        app = FastAPI()
        app.add_middleware(SecurityHeadersMiddleware)
        
        test_data = {"key": "value", "number": 42}
        
        @app.get("/test")
        async def test_endpoint():
            return test_data
        
        client = TestClient(app)
        response = client.get("/test")
        
        assert response.status_code == 200
        assert response.json() == test_data


class TestRequestIdMiddleware:
    """Test request ID middleware."""
    
    def test_request_id_added_to_response(self):
        """Test that request ID is added to response headers."""
        app = FastAPI()
        app.add_middleware(RequestIdMiddleware)
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        client = TestClient(app)
        response = client.get("/test")
        
        assert "X-Request-ID" in response.headers
        
        # Validate UUID format
        request_id = response.headers["X-Request-ID"]
        uuid.UUID(request_id)  # Should not raise exception
    
    def test_request_id_unique_per_request(self):
        """Test that each request gets a unique ID."""
        app = FastAPI()
        app.add_middleware(RequestIdMiddleware)
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        client = TestClient(app)
        
        # Make multiple requests
        response1 = client.get("/test")
        response2 = client.get("/test")
        response3 = client.get("/test")
        
        id1 = response1.headers["X-Request-ID"]
        id2 = response2.headers["X-Request-ID"]
        id3 = response3.headers["X-Request-ID"]
        
        # All IDs should be different
        assert id1 != id2
        assert id2 != id3
        assert id1 != id3
    
    def test_request_id_available_in_request_state(self):
        """Test that request ID is available in request.state."""
        app = FastAPI()
        app.add_middleware(RequestIdMiddleware)
        
        captured_request_id = None
        
        @app.get("/test")
        async def test_endpoint(request: Request):
            nonlocal captured_request_id
            captured_request_id = request.state.request_id
            return {"message": "test"}
        
        client = TestClient(app)
        response = client.get("/test")
        
        # Request ID in state should match header
        assert captured_request_id == response.headers["X-Request-ID"]
    
    def test_middleware_error_handling(self):
        """Test middleware handles errors gracefully."""
        app = FastAPI()
        app.add_middleware(RequestIdMiddleware)
        
        @app.get("/test")
        async def test_endpoint():
            raise ValueError("Test error")
        
        client = TestClient(app)
        response = client.get("/test")
        
        # Even with error, request ID should be present
        assert "X-Request-ID" in response.headers
        assert response.status_code == 500


class TestMiddlewareIntegration:
    """Test multiple middleware working together."""
    
    def test_all_middleware_together(self):
        """Test that all middleware work together correctly."""
        app = FastAPI()
        app.add_middleware(SecurityHeadersMiddleware)
        app.add_middleware(RequestIdMiddleware)
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        client = TestClient(app)
        response = client.get("/test")
        
        # Check both middleware effects
        assert "X-Request-ID" in response.headers
        assert "X-Content-Type-Options" in response.headers
        assert response.status_code == 200
        assert response.json() == {"message": "test"}