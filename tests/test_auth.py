"""Test authentication endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    """Test user registration."""
    user_data = {
        "email": "test@example.com",
        "password": "TestPassword123!",
        "first_name": "Test",
        "last_name": "User"
    }
    response = await client.post("/api/auth/register", json=user_data)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == user_data["email"]
    assert "id" in data
    assert "password" not in data

@pytest.mark.asyncio
async def test_login_user(client: AsyncClient):
    """Test user login."""
    # First register a user
    user_data = {
        "email": "login@example.com",
        "password": "LoginPassword123!",
        "first_name": "Login",
        "last_name": "User"
    }
    await client.post("/api/auth/register", json=user_data)
    
    # Then try to login
    login_data = {
        "username": user_data["email"],
        "password": user_data["password"]
    }
    response = await client.post("/api/auth/login", data=login_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient):
    """Test login with invalid credentials."""
    login_data = {
        "username": "nonexistent@example.com",
        "password": "WrongPassword123!"
    }
    response = await client.post("/api/auth/login", data=login_data)
    assert response.status_code == 401