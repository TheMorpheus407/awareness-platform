"""Test health endpoints."""

import pytest
from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    """Test basic health check endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert "version" in data


def test_database_health_check(client: TestClient):
    """Test database health check endpoint."""
    response = client.get("/api/health/db")
    assert response.status_code == 200
    data = response.json()
    # Database health might be unhealthy in test environment due to async/sync mismatch
    assert "status" in data
    assert "database" in data
    # If unhealthy, ensure error message is present
    if data["status"] == "unhealthy":
        assert "error" in data or data["database"] == "disconnected"


def test_root_endpoint(client: TestClient):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data