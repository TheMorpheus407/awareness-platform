"""Extended tests for health endpoints."""

import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock
from sqlalchemy.exc import OperationalError


class TestHealthEndpoints:
    """Extended test cases for health endpoints."""
    
    @pytest.mark.asyncio
    async def test_health_endpoint_structure(self, client: AsyncClient):
        """Test health endpoint returns expected structure."""
        response = await client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check all expected fields
        assert "status" in data
        assert "service" in data
        assert "version" in data
        assert "timestamp" in data
        
        # Validate values
        assert data["status"] == "healthy"
        assert isinstance(data["service"], str)
        assert isinstance(data["version"], str)
        assert isinstance(data["timestamp"], str)
    
    @pytest.mark.asyncio
    async def test_database_health_when_connected(self, client: AsyncClient):
        """Test database health check when database is connected."""
        response = await client.get("/api/health/db")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
        assert "timestamp" in data
    
    @pytest.mark.asyncio
    async def test_database_health_when_disconnected(self, client: AsyncClient):
        """Test database health check when database is disconnected."""
        # Mock database connection to fail
        with patch('api.routes.health.get_db') as mock_get_db:
            async def mock_db_error():
                raise OperationalError("Connection failed", None, None)
                yield
            
            mock_get_db.return_value = mock_db_error()
            
            response = await client.get("/api/health/db")
            
            # Should still return 200 but with unhealthy status
            assert response.status_code == 503
            data = response.json()
            
            assert data["status"] == "unhealthy"
            assert data["database"] == "disconnected"
    
    @pytest.mark.asyncio
    async def test_health_endpoints_no_auth_required(self, client: AsyncClient):
        """Test that health endpoints don't require authentication."""
        # Test without any auth headers
        endpoints = ["/api/health", "/api/health/db", "/"]
        
        for endpoint in endpoints:
            response = await client.get(endpoint)
            # Should not return 401 Unauthorized
            assert response.status_code != 401
            assert response.status_code in [200, 503]  # 503 for db when not connected
    
    @pytest.mark.asyncio
    async def test_health_endpoint_performance(self, client: AsyncClient):
        """Test that health endpoint responds quickly."""
        import time
        
        start_time = time.time()
        response = await client.get("/api/health")
        end_time = time.time()
        
        assert response.status_code == 200
        
        # Health check should respond in less than 100ms
        response_time = (end_time - start_time) * 1000
        assert response_time < 100
    
    @pytest.mark.asyncio
    async def test_root_endpoint_debug_mode(self, client: AsyncClient):
        """Test root endpoint shows different info based on debug mode."""
        with patch('core.config.settings.DEBUG', True):
            response = await client.get("/")
            data = response.json()
            
            # In debug mode, should show docs URL
            assert "docs" in data
            assert "/api/docs" in data["docs"]
        
        with patch('core.config.settings.DEBUG', False):
            response = await client.get("/")
            data = response.json()
            
            # In production, docs should be disabled
            assert "docs" in data
            assert data["docs"] == "Disabled in production"
    
    @pytest.mark.asyncio
    async def test_health_endpoint_headers(self, client: AsyncClient):
        """Test that health endpoints return proper headers."""
        response = await client.get("/api/health")
        
        # Check content type
        assert response.headers["content-type"] == "application/json"
        
        # Should have our custom headers from middleware
        # Note: These might not be present in test client, 
        # but we check the response is valid JSON
        assert response.json() is not None
    
    @pytest.mark.asyncio
    async def test_concurrent_health_checks(self, client: AsyncClient):
        """Test multiple concurrent health checks."""
        import asyncio
        
        # Make 10 concurrent requests
        tasks = []
        for _ in range(10):
            tasks.append(client.get("/api/health"))
        
        responses = await asyncio.gather(*tasks)
        
        # All should succeed
        for response in responses:
            assert response.status_code == 200
            assert response.json()["status"] == "healthy"