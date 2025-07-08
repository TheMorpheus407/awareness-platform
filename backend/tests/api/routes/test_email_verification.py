"""Tests for email verification endpoints."""

import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from core.security import create_email_verification_token, get_password_hash


@pytest.mark.asyncio
class TestEmailVerification:
    """Test email verification routes."""

    async def test_send_verification_email(
        self, async_client: AsyncClient, db: AsyncSession
    ) -> None:
        """Test sending verification email."""
        # Create unverified user
        user = User(
            email="unverified@example.com",
            password_hash=get_password_hash("testpassword123"),
            first_name="Unverified",
            last_name="User",
            is_active=True,
            email_verified=False
        )
        db.add(user)
        await db.commit()
        
        # Login to get token
        login_response = await async_client.post(
            "/api/v1/auth/login",
            data={
                "email": user.email,
                "password": "testpassword123"
            }
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Request verification email
        response = await async_client.post(
            "/api/v1/auth/email/send-verification",
            headers=headers
        )
        
        assert response.status_code == 200
        assert response.json()["message"] == "Verification email sent"

    async def test_send_verification_email_already_verified(
        self, async_client: AsyncClient, async_test_user: User, async_auth_headers: dict
    ) -> None:
        """Test sending verification email when already verified."""
        response = await async_client.post(
            "/api/v1/auth/email/send-verification",
            headers=async_auth_headers
        )
        
        assert response.status_code == 400
        assert "already verified" in response.json()["detail"]

    async def test_verify_email_success(
        self, async_client: AsyncClient, db: AsyncSession
    ) -> None:
        """Test successful email verification."""
        # Create unverified user
        user = User(
            email="toverify@example.com",
            password_hash=get_password_hash("testpassword123"),
            first_name="ToVerify",
            last_name="User",
            is_active=True,
            email_verified=False
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        # Create valid verification token
        token = create_email_verification_token(email=user.email)
        
        # Verify email
        response = await async_client.get(
            f"/api/v1/auth/email/verify?token={token}"
        )
        
        assert response.status_code == 200
        assert response.json()["message"] == "Email verified successfully"
        
        # Check user is verified
        await db.refresh(user)
        assert user.email_verified is True
        assert user.email_verified_at is not None

    async def test_verify_email_invalid_token(
        self, async_client: AsyncClient
    ) -> None:
        """Test email verification with invalid token."""
        response = await async_client.get(
            "/api/v1/auth/email/verify?token=invalid_token"
        )
        
        assert response.status_code == 400
        assert "Invalid verification token" in response.json()["detail"]

    async def test_verify_email_expired_token(
        self, async_client: AsyncClient, db: AsyncSession
    ) -> None:
        """Test email verification with expired token."""
        # Create unverified user
        user = User(
            email="expired@example.com",
            password_hash=get_password_hash("testpassword123"),
            first_name="Expired",
            last_name="User",
            is_active=True,
            email_verified=False
        )
        db.add(user)
        await db.commit()
        
        # Create expired token (negative expiry)
        from jose import jwt
        from core.config import settings
        
        expire = datetime.utcnow() - timedelta(hours=1)
        to_encode = {"sub": user.email, "exp": expire, "type": "email_verification"}
        token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        
        response = await async_client.get(
            f"/api/v1/auth/email/verify?token={token}"
        )
        
        assert response.status_code == 400
        assert "Token has expired" in response.json()["detail"]

    async def test_verify_email_nonexistent_user(
        self, async_client: AsyncClient
    ) -> None:
        """Test email verification for non-existent user."""
        # Create token for non-existent email
        token = create_email_verification_token(email="nonexistent@example.com")
        
        response = await async_client.get(
            f"/api/v1/auth/email/verify?token={token}"
        )
        
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]

    async def test_resend_verification_rate_limit(
        self, async_client: AsyncClient, db: AsyncSession
    ) -> None:
        """Test rate limiting on resend verification email."""
        # Create unverified user
        user = User(
            email="ratelimit@example.com",
            password_hash=get_password_hash("testpassword123"),
            first_name="RateLimit",
            last_name="User",
            is_active=True,
            email_verified=False
        )
        db.add(user)
        await db.commit()
        
        # Login to get token
        login_response = await async_client.post(
            "/api/v1/auth/login",
            data={
                "email": user.email,
                "password": "testpassword123"
            }
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Send multiple requests
        for i in range(5):
            response = await async_client.post(
                "/api/v1/auth/email/send-verification",
                headers=headers
            )
            if i < 3:
                assert response.status_code == 200
            else:
                assert response.status_code == 429