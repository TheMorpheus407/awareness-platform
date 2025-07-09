"""Tests for password reset endpoints."""

import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from models.password_reset_token import PasswordResetToken
from core.security import get_password_hash, verify_password


@pytest.mark.asyncio
class TestPasswordReset:
    """Test password reset routes."""

    async def test_request_password_reset_success(
        self, async_client: AsyncClient, async_test_user: User
    ) -> None:
        """Test successful password reset request."""
        response = await async_client.post(
            "/api/v1/auth/password/reset-request",
            json={"email": async_test_user.email}
        )
        
        assert response.status_code == 200
        assert response.json()["message"] == "Password reset email sent"

    async def test_request_password_reset_nonexistent_user(
        self, async_client: AsyncClient
    ) -> None:
        """Test password reset request for non-existent user."""
        response = await async_client.post(
            "/api/v1/auth/password/reset-request",
            json={"email": "nonexistent@example.com"}
        )
        
        # Should return success to prevent email enumeration
        assert response.status_code == 200
        assert response.json()["message"] == "Password reset email sent"

    async def test_request_password_reset_inactive_user(
        self, async_client: AsyncClient, db: AsyncSession
    ) -> None:
        """Test password reset request for inactive user."""
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
        
        response = await async_client.post(
            "/api/v1/auth/password/reset-request",
            json={"email": user.email}
        )
        
        # Should return success to prevent information leak
        assert response.status_code == 200
        assert response.json()["message"] == "Password reset email sent"

    async def test_verify_reset_token_success(
        self, async_client: AsyncClient, async_test_user: User, db: AsyncSession
    ) -> None:
        """Test successful reset token verification."""
        # Create reset token
        reset_token = PasswordResetToken(
            user_id=async_test_user.id,
            token="test-reset-token",
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        db.add(reset_token)
        await db.commit()
        
        response = await async_client.get(
            f"/api/auth/password/verify-reset-token?token=test-reset-token"
        )
        
        assert response.status_code == 200
        assert response.json()["valid"] is True

    async def test_verify_reset_token_invalid(
        self, async_client: AsyncClient
    ) -> None:
        """Test verification of invalid reset token."""
        response = await async_client.get(
            "/api/auth/password/verify-reset-token?token=invalid-token"
        )
        
        assert response.status_code == 400
        assert "Invalid or expired reset token" in response.json()["detail"]

    async def test_verify_reset_token_expired(
        self, async_client: AsyncClient, async_test_user: User, db: AsyncSession
    ) -> None:
        """Test verification of expired reset token."""
        # Create expired token
        reset_token = PasswordResetToken(
            user_id=async_test_user.id,
            token="expired-reset-token",
            expires_at=datetime.utcnow() - timedelta(hours=1)
        )
        db.add(reset_token)
        await db.commit()
        
        response = await async_client.get(
            "/api/auth/password/verify-reset-token?token=expired-reset-token"
        )
        
        assert response.status_code == 400
        assert "Invalid or expired reset token" in response.json()["detail"]

    async def test_reset_password_success(
        self, async_client: AsyncClient, async_test_user: User, db: AsyncSession
    ) -> None:
        """Test successful password reset."""
        # Create reset token
        reset_token = PasswordResetToken(
            user_id=async_test_user.id,
            token="valid-reset-token",
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        db.add(reset_token)
        await db.commit()
        
        new_password = "NewSecurePassword123!"
        response = await async_client.post(
            "/api/v1/auth/password/reset",
            json={
                "token": "valid-reset-token",
                "new_password": new_password
            }
        )
        
        assert response.status_code == 200
        assert response.json()["message"] == "Password reset successfully"
        
        # Verify password was changed
        await db.refresh(async_test_user)
        assert verify_password(new_password, async_test_user.password_hash)
        
        # Verify token was deleted
        token_check = await db.get(PasswordResetToken, reset_token.id)
        assert token_check is None

    async def test_reset_password_weak_password(
        self, async_client: AsyncClient, async_test_user: User, db: AsyncSession
    ) -> None:
        """Test password reset with weak password."""
        # Create reset token
        reset_token = PasswordResetToken(
            user_id=async_test_user.id,
            token="weak-pass-token",
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        db.add(reset_token)
        await db.commit()
        
        response = await async_client.post(
            "/api/v1/auth/password/reset",
            json={
                "token": "weak-pass-token",
                "new_password": "weak"
            }
        )
        
        assert response.status_code == 422
        assert "Password must be at least 8 characters" in str(response.json())

    async def test_reset_password_invalid_token(
        self, async_client: AsyncClient
    ) -> None:
        """Test password reset with invalid token."""
        response = await async_client.post(
            "/api/v1/auth/password/reset",
            json={
                "token": "invalid-token",
                "new_password": "NewSecurePassword123!"
            }
        )
        
        assert response.status_code == 400
        assert "Invalid or expired reset token" in response.json()["detail"]

    async def test_reset_password_used_token(
        self, async_client: AsyncClient, async_test_user: User, db: AsyncSession
    ) -> None:
        """Test password reset with already used token."""
        # Create used token
        reset_token = PasswordResetToken(
            user_id=async_test_user.id,
            token="used-reset-token",
            expires_at=datetime.utcnow() + timedelta(hours=1),
            used_at=datetime.utcnow()
        )
        db.add(reset_token)
        await db.commit()
        
        response = await async_client.post(
            "/api/v1/auth/password/reset",
            json={
                "token": "used-reset-token",
                "new_password": "NewSecurePassword123!"
            }
        )
        
        assert response.status_code == 400
        assert "Invalid or expired reset token" in response.json()["detail"]

    async def test_password_reset_rate_limit(
        self, async_client: AsyncClient, async_test_user: User
    ) -> None:
        """Test rate limiting on password reset requests."""
        # Make multiple requests
        for i in range(5):
            response = await async_client.post(
                "/api/v1/auth/password/reset-request",
                json={"email": async_test_user.email}
            )
            if i < 3:
                assert response.status_code == 200
            else:
                assert response.status_code == 429