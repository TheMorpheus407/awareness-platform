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
        self, client: AsyncClient, db: AsyncSession
    ) -> None:
        """Test successful user registration."""
        data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "ValidPassword123!",
            "first_name": "New",
            "last_name": "User"
        }
        
        response = await client.post("/api/auth/register", json=data)
        assert response.status_code == 201
        
        result = response.json()
        assert result["email"] == data["email"]
        assert result["username"] == data["username"]
        assert result["first_name"] == data["first_name"]
        assert result["last_name"] == data["last_name"]
        assert "id" in result
        assert "hashed_password" not in result

    async def test_register_duplicate_email(
        self, client: AsyncClient, db: AsyncSession, test_user: User
    ) -> None:
        """Test registration with duplicate email."""
        data = {
            "email": test_user.email,
            "username": "anotheruser",
            "password": "ValidPassword123!",
            "first_name": "Another",
            "last_name": "User"
        }
        
        response = await client.post("/api/auth/register", json=data)
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    async def test_register_duplicate_username(
        self, client: AsyncClient, db: AsyncSession, test_user: User
    ) -> None:
        """Test registration with duplicate username."""
        data = {
            "email": "another@example.com",
            "username": test_user.username,
            "password": "ValidPassword123!",
            "first_name": "Another",
            "last_name": "User"
        }
        
        response = await client.post("/api/auth/register", json=data)
        assert response.status_code == 400
        assert "Username already registered" in response.json()["detail"]

    async def test_register_invalid_email(
        self, client: AsyncClient
    ) -> None:
        """Test registration with invalid email."""
        data = {
            "email": "invalid-email",
            "username": "testuser",
            "password": "ValidPassword123!",
            "first_name": "Test",
            "last_name": "User"
        }
        
        response = await client.post("/api/auth/register", json=data)
        assert response.status_code == 422

    async def test_register_weak_password(
        self, client: AsyncClient
    ) -> None:
        """Test registration with weak password."""
        data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "weak",
            "first_name": "Test",
            "last_name": "User"
        }
        
        response = await client.post("/api/auth/register", json=data)
        assert response.status_code == 422

    async def test_login_success(
        self, client: AsyncClient, db: AsyncSession, test_user: User
    ) -> None:
        """Test successful login."""
        login_data = {
            "username": test_user.email,
            "password": "testpassword123"
        }
        
        response = await client.post("/api/auth/login", data=login_data)
        assert response.status_code == 200
        
        result = response.json()
        assert "access_token" in result
        assert "refresh_token" in result
        assert result["token_type"] == "bearer"

    async def test_login_with_username(
        self, client: AsyncClient, db: AsyncSession, test_user: User
    ) -> None:
        """Test login with username instead of email."""
        login_data = {
            "username": test_user.username,
            "password": "testpassword123"
        }
        
        response = await client.post("/api/auth/login", data=login_data)
        assert response.status_code == 200
        
        result = response.json()
        assert "access_token" in result
        assert "refresh_token" in result

    async def test_login_invalid_credentials(
        self, client: AsyncClient, db: AsyncSession, test_user: User
    ) -> None:
        """Test login with invalid credentials."""
        login_data = {
            "username": test_user.email,
            "password": "wrongpassword"
        }
        
        response = await client.post("/api/auth/login", data=login_data)
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]

    async def test_login_nonexistent_user(
        self, client: AsyncClient
    ) -> None:
        """Test login with non-existent user."""
        login_data = {
            "username": "nonexistent@example.com",
            "password": "anypassword"
        }
        
        response = await client.post("/api/auth/login", data=login_data)
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]

    async def test_login_inactive_user(
        self, client: AsyncClient, db: AsyncSession
    ) -> None:
        """Test login with inactive user."""
        # Create inactive user
        user = User(
            email="inactive@example.com",
            username="inactiveuser",
            hashed_password=get_password_hash("testpassword123"),
            first_name="Inactive",
            last_name="User",
            is_active=False
        )
        db.add(user)
        await db.commit()
        
        login_data = {
            "username": user.email,
            "password": "testpassword123"
        }
        
        response = await client.post("/api/auth/login", data=login_data)
        assert response.status_code == 401
        assert "Inactive user" in response.json()["detail"]

    async def test_login_unverified_user(
        self, client: AsyncClient, db: AsyncSession
    ) -> None:
        """Test login with unverified user (warning only)."""
        # Create unverified user
        user = User(
            email="unverified@example.com",
            username="unverifieduser",
            hashed_password=get_password_hash("testpassword123"),
            first_name="Unverified",
            last_name="User",
            is_verified=False
        )
        db.add(user)
        await db.commit()
        
        login_data = {
            "username": user.email,
            "password": "testpassword123"
        }
        
        response = await client.post("/api/auth/login", data=login_data)
        assert response.status_code == 200
        # Should still allow login but with warning

    async def test_refresh_token_success(
        self, client: AsyncClient, db: AsyncSession, test_user: User
    ) -> None:
        """Test successful token refresh."""
        # First login to get tokens
        login_data = {
            "username": test_user.email,
            "password": "testpassword123"
        }
        
        login_response = await client.post("/api/auth/login", data=login_data)
        tokens = login_response.json()
        
        # Use refresh token
        response = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]}
        )
        assert response.status_code == 200
        
        result = response.json()
        assert "access_token" in result
        assert "refresh_token" in result
        assert result["token_type"] == "bearer"
        # New tokens should be different
        assert result["access_token"] != tokens["access_token"]
        assert result["refresh_token"] != tokens["refresh_token"]

    async def test_refresh_token_invalid(
        self, client: AsyncClient
    ) -> None:
        """Test refresh with invalid token."""
        response = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": "invalid.refresh.token"}
        )
        assert response.status_code == 401
        assert "Invalid refresh token" in response.json()["detail"]

    async def test_refresh_token_expired(
        self, client: AsyncClient, db: AsyncSession, test_user: User
    ) -> None:
        """Test refresh with expired token."""
        # Create expired refresh token
        expired_token = create_access_token(
            data={"sub": str(test_user.id), "type": "refresh"},
            expires_delta=timedelta(seconds=-1)
        )
        
        response = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": expired_token}
        )
        assert response.status_code == 401
        assert "Invalid refresh token" in response.json()["detail"]

    async def test_me_success(
        self, client: AsyncClient, db: AsyncSession, test_user: User, auth_headers: dict
    ) -> None:
        """Test get current user endpoint."""
        response = await client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        
        result = response.json()
        assert result["id"] == test_user.id
        assert result["email"] == test_user.email
        assert result["username"] == test_user.username
        assert "hashed_password" not in result

    async def test_me_no_auth(
        self, client: AsyncClient
    ) -> None:
        """Test get current user without authentication."""
        response = await client.get("/api/auth/me")
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]

    async def test_me_invalid_token(
        self, client: AsyncClient
    ) -> None:
        """Test get current user with invalid token."""
        headers = {"Authorization": "Bearer invalid.token.here"}
        response = await client.get("/api/auth/me", headers=headers)
        assert response.status_code == 401
        assert "Could not validate credentials" in response.json()["detail"]

    async def test_logout_success(
        self, client: AsyncClient, db: AsyncSession, test_user: User, auth_headers: dict
    ) -> None:
        """Test successful logout."""
        response = await client.post("/api/auth/logout", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["message"] == "Successfully logged out"

    async def test_logout_no_auth(
        self, client: AsyncClient
    ) -> None:
        """Test logout without authentication."""
        response = await client.post("/api/auth/logout")
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]

    async def test_change_password_success(
        self, client: AsyncClient, db: AsyncSession, test_user: User, auth_headers: dict
    ) -> None:
        """Test successful password change."""
        data = {
            "current_password": "testpassword123",
            "new_password": "NewPassword123!"
        }
        
        response = await client.post("/api/auth/change-password", json=data, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["message"] == "Password updated successfully"
        
        # Verify can login with new password
        login_data = {
            "username": test_user.email,
            "password": "NewPassword123!"
        }
        
        login_response = await client.post("/api/auth/login", data=login_data)
        assert login_response.status_code == 200

    async def test_change_password_wrong_current(
        self, client: AsyncClient, db: AsyncSession, test_user: User, auth_headers: dict
    ) -> None:
        """Test password change with wrong current password."""
        data = {
            "current_password": "wrongpassword",
            "new_password": "NewPassword123!"
        }
        
        response = await client.post("/api/auth/change-password", json=data, headers=auth_headers)
        assert response.status_code == 400
        assert "Current password is incorrect" in response.json()["detail"]

    async def test_change_password_weak_new(
        self, client: AsyncClient, db: AsyncSession, test_user: User, auth_headers: dict
    ) -> None:
        """Test password change with weak new password."""
        data = {
            "current_password": "testpassword123",
            "new_password": "weak"
        }
        
        response = await client.post("/api/auth/change-password", json=data, headers=auth_headers)
        assert response.status_code == 422

    async def test_change_password_no_auth(
        self, client: AsyncClient
    ) -> None:
        """Test password change without authentication."""
        data = {
            "current_password": "anypassword",
            "new_password": "NewPassword123!"
        }
        
        response = await client.post("/api/auth/change-password", json=data)
        assert response.status_code == 401

    async def test_rate_limiting(
        self, client: AsyncClient, db: AsyncSession
    ) -> None:
        """Test rate limiting on auth endpoints."""
        # Make multiple rapid requests
        login_data = {
            "username": "test@example.com",
            "password": "wrongpassword"
        }
        
        # Make 10 rapid requests (assuming rate limit is 5/minute)
        responses = []
        for _ in range(10):
            response = await client.post("/api/auth/login", data=login_data)
            responses.append(response.status_code)
        
        # At least one should be rate limited
        assert 429 in responses