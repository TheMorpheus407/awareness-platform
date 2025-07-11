"""Tests for CSRF middleware."""

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from core.middleware import CSRFMiddleware
from core.config import settings


@pytest.fixture
def app_with_csrf():
    """Create a test app with CSRF middleware."""
    app = FastAPI()
    
    # Add CSRF middleware
    app.add_middleware(
        CSRFMiddleware,
        secret_key="test-secret-key",
        cookie_secure=False,  # For testing
        exclude_paths={"/auth/login", "/health"}
    )
    
    @app.get("/test")
    async def test_get():
        return {"message": "GET request"}
    
    @app.post("/test")
    async def test_post():
        return {"message": "POST request"}
    
    @app.get("/auth/csrf-token")
    async def get_csrf_token(request: Request):
        csrf_token = getattr(request.state, "csrf_token", None)
        return {"csrf_token": csrf_token}
    
    @app.post("/auth/login")
    async def login():
        return {"message": "Login endpoint"}
    
    return app


class TestCSRFMiddleware:
    """Test CSRF middleware functionality."""
    
    def test_get_request_no_csrf_required(self, app_with_csrf):
        """Test that GET requests don't require CSRF token."""
        client = TestClient(app_with_csrf)
        response = client.get("/test")
        assert response.status_code == 200
        assert response.json() == {"message": "GET request"}
    
    def test_post_request_without_csrf_token_fails(self, app_with_csrf):
        """Test that POST requests without CSRF token are rejected."""
        client = TestClient(app_with_csrf)
        response = client.post("/test", json={"data": "test"})
        assert response.status_code == 403
        assert "CSRF token missing" in response.json()["detail"]
    
    def test_post_request_with_valid_csrf_token_succeeds(self, app_with_csrf):
        """Test that POST requests with valid CSRF token succeed."""
        client = TestClient(app_with_csrf)
        
        # First get CSRF token
        token_response = client.get("/auth/csrf-token")
        csrf_token = token_response.json()["csrf_token"]
        
        # Make POST request with CSRF token
        response = client.post(
            "/test",
            json={"data": "test"},
            headers={"X-CSRF-Token": csrf_token}
        )
        assert response.status_code == 200
        assert response.json() == {"message": "POST request"}
    
    def test_excluded_path_no_csrf_required(self, app_with_csrf):
        """Test that excluded paths don't require CSRF token."""
        client = TestClient(app_with_csrf)
        response = client.post("/auth/login", json={"username": "test", "password": "test"})
        assert response.status_code == 200
        assert response.json() == {"message": "Login endpoint"}
    
    def test_csrf_token_in_cookie(self, app_with_csrf):
        """Test that CSRF token is set in cookie."""
        client = TestClient(app_with_csrf)
        response = client.get("/auth/csrf-token")
        
        # Check that csrf_token cookie is set
        assert "csrf_token" in response.cookies
        csrf_cookie = response.cookies["csrf_token"]
        assert len(csrf_cookie) > 0
    
    def test_csrf_token_rotation(self, app_with_csrf):
        """Test that new sessions get new CSRF tokens."""
        client1 = TestClient(app_with_csrf)
        client2 = TestClient(app_with_csrf)
        
        # Get tokens for two different clients
        response1 = client1.get("/auth/csrf-token")
        response2 = client2.get("/auth/csrf-token")
        
        token1 = response1.json()["csrf_token"]
        token2 = response2.json()["csrf_token"]
        
        # Tokens should be different
        assert token1 != token2
    
    def test_invalid_csrf_token_rejected(self, app_with_csrf):
        """Test that invalid CSRF tokens are rejected."""
        client = TestClient(app_with_csrf)
        
        # Make POST request with invalid CSRF token
        response = client.post(
            "/test",
            json={"data": "test"},
            headers={"X-CSRF-Token": "invalid-token"}
        )
        assert response.status_code == 403
        assert "CSRF token invalid" in response.json()["detail"]
    
    def test_csrf_token_mismatch_rejected(self, app_with_csrf):
        """Test that mismatched CSRF tokens are rejected."""
        client1 = TestClient(app_with_csrf)
        client2 = TestClient(app_with_csrf)
        
        # Get token from client1
        token_response = client1.get("/auth/csrf-token")
        csrf_token = token_response.json()["csrf_token"]
        
        # Try to use client1's token with client2
        response = client2.post(
            "/test",
            json={"data": "test"},
            headers={"X-CSRF-Token": csrf_token}
        )
        assert response.status_code == 403


@pytest.mark.asyncio
async def test_csrf_middleware_initialization():
    """Test CSRF middleware initialization with different configurations."""
    app = FastAPI()
    
    # Test with default configuration
    middleware = CSRFMiddleware(
        app,
        secret_key="test-key"
    )
    assert middleware.cookie_name == "csrf_token"
    assert middleware.header_name == "X-CSRF-Token"
    assert middleware.token_length == 32
    
    # Test with custom configuration
    middleware = CSRFMiddleware(
        app,
        secret_key="test-key",
        cookie_name="custom_csrf",
        header_name="X-Custom-CSRF",
        token_length=64
    )
    assert middleware.cookie_name == "custom_csrf"
    assert middleware.header_name == "X-Custom-CSRF"
    assert middleware.token_length == 64