"""Simple tests for MVP endpoints."""
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint returns expected response."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "Awareness Platform API"
    assert response.json()["version"] == "1.0.0"


def test_health_endpoint():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_login_requires_credentials():
    """Test login endpoint requires credentials."""
    response = client.post("/api/v1/auth/login")
    assert response.status_code == 422  # Unprocessable Entity


def test_courses_requires_auth():
    """Test courses endpoint requires authentication."""
    response = client.get("/api/v1/courses")
    assert response.status_code == 401  # Unauthorized


def test_analytics_requires_auth():
    """Test analytics endpoint requires authentication."""
    response = client.get("/api/v1/analytics/dashboard")
    assert response.status_code == 401  # Unauthorized