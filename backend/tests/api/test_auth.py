import pytest
from fastapi import status
from httpx import AsyncClient

from core.security import verify_password
from models.user import User


class TestAuthEndpoints:
    """Test authentication endpoints."""

    def test_login_success(self, client, test_user):
        """Test successful login."""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "testpassword123"
            }
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_credentials(self, client, test_user):
        """Test login with invalid credentials."""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "wrongpassword"
            }
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Incorrect username or password"

    def test_login_inactive_user(self, client, db_session, test_company):
        """Test login with inactive user."""
        # Create inactive user
        from core.security import get_password_hash
        inactive_user = User(
            email="inactive@example.com",
            password_hash=get_password_hash("password123"),
            full_name="Inactive User",
            company_id=test_company.id,
            is_active=False,
            role="user"
        )
        db_session.add(inactive_user)
        db_session.commit()

        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": inactive_user.email,
                "password": "password123"
            }
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Inactive user"

    def test_register_success(self, client, test_company):
        """Test successful user registration."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "newpassword123",
                "full_name": "New User",
                "company_id": test_company.id
            }
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"
        assert "id" in data
        assert "password_hash" not in data

    def test_register_duplicate_email(self, client, test_user, test_company):
        """Test registration with duplicate email."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": test_user.email,
                "password": "password123",
                "full_name": "Duplicate User",
                "company_id": test_company.id
            }
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already registered" in response.json()["detail"]

    def test_refresh_token_success(self, client, test_user):
        """Test successful token refresh."""
        # First login to get tokens
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "testpassword123"
            }
        )
        refresh_token = login_response.json()["refresh_token"]

        # Use refresh token
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_refresh_token_invalid(self, client):
        """Test refresh with invalid token."""
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid-token"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_logout_success(self, client, auth_headers):
        """Test successful logout."""
        response = client.post(
            "/api/v1/auth/logout",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["message"] == "Successfully logged out"

    def test_me_endpoint(self, client, test_user, auth_headers):
        """Test get current user endpoint."""
        response = client.get(
            "/api/v1/auth/me",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == test_user.email
        assert data["full_name"] == test_user.full_name
        assert "password_hash" not in data

    def test_me_endpoint_unauthorized(self, client):
        """Test get current user without authentication."""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_change_password_success(self, client, test_user, auth_headers, db_session):
        """Test successful password change."""
        response = client.post(
            "/api/v1/auth/change-password",
            headers=auth_headers,
            json={
                "current_password": "testpassword123",
                "new_password": "newpassword456"
            }
        )
        assert response.status_code == status.HTTP_200_OK
        
        # Verify password was changed
        db_session.refresh(test_user)
        assert verify_password("newpassword456", test_user.password_hash)

    def test_change_password_wrong_current(self, client, auth_headers):
        """Test password change with wrong current password."""
        response = client.post(
            "/api/v1/auth/change-password",
            headers=auth_headers,
            json={
                "current_password": "wrongpassword",
                "new_password": "newpassword456"
            }
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Incorrect password" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_async_login(self, async_client: AsyncClient, test_user):
        """Test async login endpoint."""
        response = await async_client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "testpassword123"
            }
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data