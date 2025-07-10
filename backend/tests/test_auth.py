"""Comprehensive authentication tests for the backend."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.testclient import TestClient

from core.security import SecurityUtils, get_password_hash
from core.two_factor_auth import TwoFactorAuth
from models.user import User
from models.company import Company
from models.two_fa_attempt import TwoFAAttempt


class TestLoginEndpoint:
    """Test cases for the login endpoint."""

    def test_login_with_valid_credentials(
        self, client: TestClient, test_user: User
    ):
        """Test successful login with valid credentials using form data."""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "testpassword123",
                "grant_type": "password"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0

    def test_login_with_invalid_email(self, client: TestClient):
        """Test login with non-existent email."""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "nonexistent@example.com",
                "password": "wrongpassword",
                "grant_type": "password"
            }
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Incorrect username or password"

    def test_login_with_invalid_password(
        self, client: TestClient, test_user: User
    ):
        """Test login with wrong password."""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "wrongpassword",
                "grant_type": "password"
            }
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Incorrect username or password"

    def test_login_with_inactive_user(
        self, client: TestClient, db_session, test_user: User
    ):
        """Test login with inactive user account."""
        # Make user inactive
        test_user.is_active = False
        db_session.commit()
        
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "testpassword123",
                "grant_type": "password"
            }
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["detail"] == "Inactive user"

    def test_login_updates_last_login(
        self, client: TestClient, db_session, test_user: User
    ):
        """Test that successful login updates last_login timestamp."""
        # Record initial last_login
        initial_last_login = test_user.last_login
        
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "testpassword123",
                "grant_type": "password"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        # Refresh user to get updated last_login
        db_session.refresh(test_user)
        assert test_user.last_login is not None
        assert test_user.last_login > initial_last_login if initial_last_login else True

    def test_login_case_insensitive_email(
        self, client: TestClient, test_user: User
    ):
        """Test that email login is case-insensitive."""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email.upper(),
                "password": "testpassword123",
                "grant_type": "password"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK

    def test_login_with_json_fails(
        self, client: TestClient, test_user: User
    ):
        """Test that login with JSON body fails (OAuth2 requires form data)."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": test_user.email,
                "password": "testpassword123",
                "grant_type": "password"
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestLoginWith2FA:
    """Test cases for login with 2FA enabled."""

    def test_login_with_2fa_returns_temp_token(
        self, client: TestClient, test_user_with_2fa: User
    ):
        """Test login with 2FA enabled returns temporary token."""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user_with_2fa.email,
                "password": "2fapassword123",
                "grant_type": "password"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["refresh_token"] is None  # No refresh token for temp token
        assert data["expires_in"] == 300  # 5 minutes

    def test_complete_2fa_login(
        self, client: TestClient, test_user_with_2fa: User
    ):
        """Test completing 2FA login with valid TOTP code."""
        # First, login to get temp token
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user_with_2fa.email,
                "password": "2fapassword123",
                "grant_type": "password"
            }
        )
        
        temp_token = login_response.json()["access_token"]
        
        # Generate valid TOTP code
        totp = TwoFactorAuth()
        code = totp.generate_totp(test_user_with_2fa._totp_secret)
        
        # Complete 2FA
        response = client.post(
            "/api/v1/auth/two-factor/verify-login",
            json={
                "session_token": temp_token,
                "code": code
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data


class TestRegistration:
    """Test cases for user registration."""

    def test_register_new_company_and_user(self, client: TestClient):
        """Test successful registration of new company and admin user."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "company": {
                    "name": "New Test Company",
                    "domain": "newtestcompany.com",
                    "industry": "Technology",
                    "size": "10-50",
                    "country": "DE",
                    "contact_email": "contact@newtestcompany.com"
                },
                "user": {
                    "email": "newadmin@newtestcompany.com",
                    "password": "NewAdmin123!",
                    "first_name": "New",
                    "last_name": "Admin"
                }
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["company"]["name"] == "New Test Company"
        assert data["user"]["email"] == "newadmin@newtestcompany.com"
        assert data["user"]["role"] == "company_admin"
        assert data["verification_email_sent"] is True

    def test_register_with_existing_email(
        self, client: TestClient, test_user: User
    ):
        """Test registration with already existing email."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "company": {
                    "name": "Another Company",
                    "domain": "anothercompany.com",
                    "industry": "Technology",
                    "size": "10-50",
                    "country": "DE",
                    "contact_email": "contact@anothercompany.com"
                },
                "user": {
                    "email": test_user.email,  # Existing email
                    "password": "Password123!",
                    "first_name": "Test",
                    "last_name": "User"
                }
            }
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["detail"] == "Email already registered"


class TestGetCurrentUser:
    """Test cases for getting current user."""

    def test_get_current_user_authenticated(
        self, client: TestClient, test_user: User, auth_headers: dict
    ):
        """Test getting current user when authenticated."""
        response = client.get(
            "/api/v1/auth/me",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == test_user.email
        assert data["first_name"] == test_user.first_name
        assert data["last_name"] == test_user.last_name

    def test_get_current_user_unauthenticated(self, client: TestClient):
        """Test getting current user without authentication."""
        response = client.get("/api/v1/auth/me")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_current_user_with_invalid_token(self, client: TestClient):
        """Test getting current user with invalid token."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid-token"}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestChangePassword:
    """Test cases for changing password."""

    def test_change_password_success(
        self, client: TestClient, test_user: User, auth_headers: dict
    ):
        """Test successful password change."""
        response = client.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": "testpassword123",
                "new_password": "NewPassword123!",
                "confirm_password": "NewPassword123!"
            },
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["message"] == "Password successfully changed"

    def test_change_password_wrong_current(
        self, client: TestClient, auth_headers: dict
    ):
        """Test password change with wrong current password."""
        response = client.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": "wrongpassword",
                "new_password": "NewPassword123!",
                "confirm_password": "NewPassword123!"
            },
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["detail"] == "Incorrect password"


class TestLogout:
    """Test cases for logout endpoint."""

    def test_logout_success(
        self, client: TestClient, auth_headers: dict
    ):
        """Test successful logout."""
        response = client.post(
            "/api/v1/auth/logout",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["message"] == "Successfully logged out"

    def test_logout_unauthenticated(self, client: TestClient):
        """Test logout without authentication."""
        response = client.post("/api/v1/auth/logout")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestSessionManagement:
    """Test cases for session management."""

    def test_get_user_sessions(
        self, client: TestClient, auth_headers: dict, db_session, test_user: User
    ):
        """Test getting user's authentication sessions."""
        # Create some authentication logs
        attempts = [
            TwoFAAttempt(
                user_id=test_user.id,
                attempt_type="login",
                success=True,
                ip_address="192.168.1.1"
            ),
            TwoFAAttempt(
                user_id=test_user.id,
                attempt_type="logout",
                success=True,
                ip_address="192.168.1.1"
            ),
            TwoFAAttempt(
                user_id=test_user.id,
                attempt_type="password_change",
                success=True,
                ip_address="192.168.1.2"
            )
        ]
        
        for attempt in attempts:
            db_session.add(attempt)
        db_session.commit()
        
        response = client.get(
            "/api/v1/auth/sessions",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 3
        assert any(log["event_type"] == "login" for log in data)
        assert any(log["event_type"] == "logout" for log in data)
        assert any(log["event_type"] == "password_change" for log in data)