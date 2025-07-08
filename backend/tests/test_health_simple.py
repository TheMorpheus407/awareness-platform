"""Simple health endpoint tests without database dependencies."""

import pytest
from fastapi.testclient import TestClient
from main import app


def test_root_endpoint():
    """Test root endpoint without any fixtures."""
    client = TestClient(app)
    response = client.get("/")
    print(f"Status: {response.status_code}")
    print(f"Body: {response.text}")
    print(f"Headers: {dict(response.headers)}")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "Welcome to" in data["message"]


def test_health_check_basic():
    """Test basic health check endpoint without database."""
    client = TestClient(app)
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert "version" in data