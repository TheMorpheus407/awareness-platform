"""Tests for authentication routes."""

import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from core.security import get_password_hash, create_access_token
from core.config import settings


@pytest.mark.asyncio
class TestAuthRoutes:
    """Test authentication routes."""

    async def test_register_success(
        self, async_client: AsyncClient, db: AsyncSession, async_test_company
    ) -> None:
        """Test successful user registration."""
        data = {
            "email": "newuser@example.com",
            "password": "ValidPassword123!",
            "first_name": "New",
            "last_name": "User",
            "company_id": str(async_test_company.id)
        }
        
        response = await async_client.post("/api/v1/auth/register", json=data)
        assert response.status_code == 201
        
        result = response.json()
        assert result["email"] == data["email"]
        assert result["first_name"] == data["first_name"]
        assert result["last_name"] == data["last_name"]
        assert "id" in result
        assert "password_hash" not in result

    async def test_register_duplicate_email(
        self, async_client: AsyncClient, db: AsyncSession, async_test_user: User
    ) -> None:
        """Test registration with duplicate email."""
        data = {
            "email": async_test_user.email,
            "password": "ValidPassword123!",
            "first_name": "Another",
            "last_name": "User",
            "company_id": str(async_test_user.company_id)
        }
        
        response = await async_client.post("/api/v1/auth/register", json=data)
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    async def test_register_invalid_email(
        self, async_client: AsyncClient
    ) -> None:
        """Test registration with invalid email."""
        data = {
            "email": "invalid-email",
            "password": "ValidPassword123!",
            "first_name": "Test",
            "last_name": "User"
        }
        
        response = await async_client.post("/api/v1/auth/register", json=data)
        assert response.status_code == 422

    async def test_register_weak_password(
        self, async_client: AsyncClient
    ) -> None:
        """Test registration with weak password."""
        data = {
            "email": "test@example.com",
            "password": "weak",
            "first_name": "Test",
            "last_name": "User"
        }
        
        response = await async_client.post("/api/v1/auth/register", json=data)
        assert response.status_code == 422

    async def test_login_success(
        self, async_client: AsyncClient, db: AsyncSession, async_test_user: User
    ) -> None:
        """Test successful login."""
        # OAuth2PasswordRequestForm expects 'email' field but we use email
        login_data = {
            "username": async_test_user.email,  # OAuth2 standard field name
            "password": "testpassword123"
        }
        
        response = await async_client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 200
        
        result = response.json()
        assert "access_token" in result
        assert "refresh_token" in result
        assert result["token_type"] == "bearer"

    async def test_login_invalid_credentials(
        self, async_client: AsyncClient, db: AsyncSession, async_test_user: User
    ) -> None:
        """Test login with invalid credentials."""
        login_data = {
            "username": async_test_user.email,  # OAuth2 standard field name
            "password": "wrongpassword"
        }
        
        response = await async_client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]

    async def test_login_nonexistent_user(
        self, async_client: AsyncClient
    ) -> None:
        """Test login with non-existent user."""
        login_data = {
            "email": "nonexistent@example.com",  # OAuth2 standard field name
            "password": "anypassword"
        }
        
        response = await async_client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]

    async def test_login_inactive_user(
        self, async_client: AsyncClient, db: AsyncSession
    ) -> None:
        """Test login with inactive user."""
        # Create inactive user
        user = User(
            email="inactive@example.com",
            password_hash=get_password_hash("testpassword123"),
            first_name="Inactive",
            last_name="User",
            is_active=False
        )
        db.add(user)
        await db.commit()
        
        login_data = {
            "email": user.email,  # OAuth2 standard field name
            "password": "testpassword123"
        }
        
        response = await async_client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 403
        assert "Inactive user" in response.json()["detail"]

    async def test_login_unverified_user(
        self, async_client: AsyncClient, db: AsyncSession
    ) -> None:
        """Test login with unverified user (should still work)."""
        # Create unverified user
        user = User(
            email="unverified@example.com",
            password_hash=get_password_hash("testpassword123"),
            first_name="Unverified",
            last_name="User",
            email_verified=False
        )
        db.add(user)
        await db.commit()
        
        login_data = {
            "email": user.email,  # OAuth2 standard field name
            "password": "testpassword123"
        }
        
        response = await async_client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 200
        
        result = response.json()
        assert "access_token" in result
        assert "refresh_token" in result

    async def test_refresh_token_success(
        self, async_client: AsyncClient, db: AsyncSession, async_test_user: User
    ) -> None:
        """Test refresh token endpoint."""
        # First login to get tokens
        login_data = {
            "username": async_test_user.email,  # OAuth2 standard field name
            "password": "testpassword123"
        }
        
        response = await async_client.post("/api/v1/auth/login", data=login_data)
        tokens = response.json()
        
        # Use refresh token
        response = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]}
        )
        assert response.status_code == 200
        
        result = response.json()
        assert "access_token" in result
        assert "refresh_token" in result
        assert result["access_token"] != tokens["access_token"]

    async def test_refresh_token_invalid(
        self, async_client: AsyncClient
    ) -> None:
        """Test refresh token with invalid token."""
        response = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid_token"}
        )
        assert response.status_code == 401

    async def test_refresh_token_with_access_token(
        self, async_client: AsyncClient, db: AsyncSession, async_test_user: User
    ) -> None:
        """Test refresh endpoint with access token instead of refresh token."""
        # Create access token
        access_token = create_access_token(subject=str(async_test_user.id))
        
        response = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": access_token}
        )
        assert response.status_code == 401

    async def test_get_current_user(
        self, async_client: AsyncClient, db: AsyncSession, async_test_user: User
    ) -> None:
        """Test get current user endpoint."""
        # First login to get token
        login_data = {
            "username": async_test_user.email,  # OAuth2 standard field name
            "password": "testpassword123"
        }
        
        response = await async_client.post("/api/v1/auth/login", data=login_data)
        tokens = response.json()
        
        # Get current user
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
        assert response.status_code == 200
        
        result = response.json()
        assert result["email"] == async_test_user.email
        assert result["first_name"] == async_test_user.first_name
        assert result["last_name"] == async_test_user.last_name
        assert "password_hash" not in result

    async def test_get_current_user_no_token(
        self, async_client: AsyncClient
    ) -> None:
        """Test get current user without token."""
        response = await async_client.get("/api/v1/auth/me")
        assert response.status_code == 401

    async def test_get_current_user_invalid_token(
        self, async_client: AsyncClient
    ) -> None:
        """Test get current user with invalid token."""
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401

    async def test_register_with_company_id(
        self, async_client: AsyncClient, db: AsyncSession, async_test_company
    ) -> None:
        """Test registration with company ID."""
        data = {
            "email": "companyuser@example.com",
            "password": "ValidPassword123!",
            "first_name": "Company",
            "last_name": "User",
            "company_id": str(async_test_company.id)
        }
        
        response = await async_client.post("/api/v1/auth/register", json=data)
        assert response.status_code == 201
        
        result = response.json()
        assert result["company_id"] == str(async_test_company.id)

    async def test_login_rate_limiting(
        self, async_client: AsyncClient
    ) -> None:
        """Test login rate limiting."""
        login_data = {
            "email": "test@example.com",  # OAuth2 standard field name
            "password": "password"
        }
        
        # Make multiple requests
        for i in range(15):
            response = await async_client.post("/api/v1/auth/login", data=login_data)
            if i < 10:
                assert response.status_code in [401, 403]  # Normal error
            else:
                assert response.status_code == 429  # Rate limited

    async def test_register_rate_limiting(
        self, async_client: AsyncClient
    ) -> None:
        """Test register rate limiting."""
        # Make multiple registration attempts
        for i in range(10):
            data = {
                "email": f"user{i}@example.com",
                "password": "ValidPassword123!",
                "first_name": "User",
                "last_name": f"Number{i}"
            }
            
            response = await async_client.post("/api/v1/auth/register", json=data)
            if i < 5:
                assert response.status_code in [201, 400]  # Normal response
            else:
                assert response.status_code == 429  # Rate limited