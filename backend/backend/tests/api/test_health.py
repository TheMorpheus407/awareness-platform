"""Test health check endpoint."""

import pytest
from fastapi import status


def test_health_check(client):
    """Test the health check endpoint returns correct status."""
    response = client.get("/api/v1/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "version" in data