"""Tests for Two-Factor Authentication endpoints."""

import pytest
import pyotp
import json
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient

from core.two_factor_auth import TwoFactorAuth
from models.user import User
from models.two_fa_attempt import TwoFAAttempt
from core.security import get_password_hash


@pytest.mark.asyncio
async def test_setup_2fa_success(
    async_client: AsyncClient,
    async_test_user: User,
    async_auth_headers: dict,
    db: AsyncSession
):
    """Test successful 2FA setup."""
    # Setup request with correct password
    response = await async_client.post(
        "/api/v1/auth/2fa/setup",
        json={"password": "testpassword123"},
        headers=async_auth_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # Check response contains required fields
    assert "secret" in data
    assert "qr_code" in data
    assert "backup_codes" in data
    assert "manual_entry_key" in data
    
    # Verify backup codes format
    assert len(data["backup_codes"]) == 8
    for code in data["backup_codes"]:
        assert len(code) == 9  # XXXX-XXXX format
        assert code[4] == "-"
    
    # Verify QR code is base64 encoded
    import base64
    try:
        base64.b64decode(data["qr_code"])
    except:
        pytest.fail("QR code is not valid base64")


@pytest.mark.asyncio
async def test_setup_2fa_wrong_password(
    async_client: AsyncClient,
    async_test_user: User,
    async_auth_headers: dict
):
    """Test 2FA setup with wrong password."""
    response = await async_client.post(
        "/api/v1/auth/2fa/setup",
        json={"password": "WrongPassword"},
        headers=async_auth_headers
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Invalid password"


@pytest.mark.asyncio
async def test_setup_2fa_already_enabled(
    async_client: AsyncClient,
    async_test_user: User,
    async_auth_headers: dict,
    db: AsyncSession
):
    """Test 2FA setup when already enabled."""
    # Enable 2FA for the user
    two_fa = TwoFactorAuth()
    async_test_user.totp_enabled = True
    async_test_user.totp_secret = two_fa.generate_secret()
    await db.commit()
    
    response = await async_client.post(
        "/api/v1/auth/2fa/setup",
        json={"password": "testpassword123"},
        headers=async_auth_headers
    )
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Two-factor authentication is already enabled"


@pytest.mark.asyncio
async def test_verify_2fa_success(
    async_client: AsyncClient,
    async_test_user: User,
    async_auth_headers: dict,
    db: AsyncSession
):
    """Test successful 2FA verification."""
    # Setup 2FA first
    two_fa = TwoFactorAuth()
    secret = two_fa.generate_secret()
    async_test_user.totp_secret = secret
    await db.commit()
    
    # Generate valid TOTP code
    totp = pyotp.TOTP(secret)
    code = totp.now()
    
    response = await async_client.post(
        "/api/v1/auth/2fa/verify",
        json={"totp_code": code},
        headers=async_auth_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Two-factor authentication enabled successfully"
    
    # Refresh user and check 2FA is enabled
    await db.refresh(async_test_user)
    assert async_test_user.totp_enabled is True
    assert async_test_user.totp_verified_at is not None


@pytest.mark.asyncio
async def test_verify_2fa_invalid_code(
    async_client: AsyncClient,
    async_test_user: User,
    async_auth_headers: dict,
    db: AsyncSession
):
    """Test 2FA verification with invalid code."""
    # Setup 2FA
    two_fa = TwoFactorAuth()
    secret = two_fa.generate_secret()
    async_test_user.totp_secret = secret
    await db.commit()
    
    response = await async_client.post(
        "/api/v1/auth/2fa/verify",
        json={"totp_code": "000000"},
        headers=async_auth_headers
    )
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Invalid verification code"


@pytest.mark.asyncio
async def test_login_with_2fa_enabled(
    async_client: AsyncClient,
    async_test_user: User,
    db: AsyncSession
):
    """Test login when 2FA is enabled."""
    # Enable 2FA for user
    two_fa = TwoFactorAuth()
    secret = two_fa.generate_secret()
    async_test_user.totp_enabled = True
    async_test_user.totp_secret = secret
    await db.commit()
    
    # Try standard login
    response = await async_client.post(
        "/api/v1/auth/login",
        data={
            "email": async_test_user.email,
            "password": "testpassword123"
        }
    )
    
    assert response.status_code == status.HTTP_428_PRECONDITION_REQUIRED
    assert response.json()["detail"] == "Two-factor authentication required"
    assert response.headers.get("X-2FA-Required") == "true"


@pytest.mark.asyncio
async def test_login_2fa_success(
    async_client: AsyncClient,
    async_test_user: User,
    db: AsyncSession
):
    """Test successful login with 2FA."""
    # Enable 2FA for user
    two_fa = TwoFactorAuth()
    secret = two_fa.generate_secret()
    async_test_user.totp_enabled = True
    async_test_user.totp_secret = secret
    await db.commit()
    
    # Generate valid TOTP code
    totp = pyotp.TOTP(secret)
    code = totp.now()
    
    response = await async_client.post(
        "/api/v1/auth/login-2fa",
        json={
            "email": async_test_user.email,
            "password": "testpassword123",
            "totp_code": code
        }
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_2fa_invalid_code(
    async_client: AsyncClient,
    async_test_user: User,
    db: AsyncSession
):
    """Test login with invalid 2FA code."""
    # Enable 2FA for user
    two_fa = TwoFactorAuth()
    secret = two_fa.generate_secret()
    async_test_user.totp_enabled = True
    async_test_user.totp_secret = secret
    await db.commit()
    
    response = await async_client.post(
        "/api/v1/auth/login-2fa",
        json={
            "email": async_test_user.email,
            "password": "testpassword123",
            "totp_code": "000000"
        }
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Invalid two-factor authentication code"


@pytest.mark.asyncio
async def test_disable_2fa_success(
    async_client: AsyncClient,
    async_test_user: User,
    async_auth_headers: dict,
    db: AsyncSession
):
    """Test successful 2FA disable."""
    # Enable 2FA for user
    two_fa = TwoFactorAuth()
    secret = two_fa.generate_secret()
    async_test_user.totp_enabled = True
    async_test_user.totp_secret = secret
    backup_codes = two_fa.generate_backup_codes()
    async_test_user.backup_codes = json.dumps([get_password_hash(code) for code in backup_codes])
    await db.commit()
    
    # Generate valid TOTP code
    totp = pyotp.TOTP(secret)
    code = totp.now()
    
    response = await async_client.post(
        "/api/v1/auth/2fa/disable",
        json={
            "password": "testpassword123",
            "totp_code": code
        },
        headers=async_auth_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Two-factor authentication disabled successfully"
    
    # Verify 2FA is disabled
    await db.refresh(async_test_user)
    assert async_test_user.totp_enabled is False
    assert async_test_user.totp_secret is None
    assert async_test_user.backup_codes is None


@pytest.mark.asyncio
async def test_backup_codes_status(
    async_client: AsyncClient,
    async_test_user: User,
    async_auth_headers: dict,
    db: AsyncSession
):
    """Test getting backup codes status."""
    # Enable 2FA with backup codes
    two_fa = TwoFactorAuth()
    async_test_user.totp_enabled = True
    async_test_user.totp_secret = two_fa.generate_secret()
    
    # Generate and hash backup codes
    codes = two_fa.generate_backup_codes()
    hashed_codes = [get_password_hash(code) for code in codes]
    async_test_user.backup_codes = json.dumps(hashed_codes)
    async_test_user.two_fa_recovery_codes_used = 2
    await db.commit()
    
    response = await async_client.get(
        "/api/v1/auth/2fa/backup-codes",
        headers=async_auth_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total_codes"] == 8
    assert data["used_codes"] == 2
    assert data["remaining_codes"] == 6


@pytest.mark.asyncio
async def test_login_with_backup_code(
    async_client: AsyncClient,
    async_test_user: User,
    db: AsyncSession
):
    """Test login using backup code."""
    # Enable 2FA and set backup codes
    two_fa = TwoFactorAuth()
    async_test_user.totp_enabled = True
    async_test_user.totp_secret = two_fa.generate_secret()
    
    # Generate backup codes
    backup_code = "TEST1-CODE"
    hashed_code = get_password_hash(backup_code)
    async_test_user.backup_codes = json.dumps([hashed_code, get_password_hash("OTHER-CODE")])
    async_test_user.two_fa_recovery_codes_used = 0
    await db.commit()
    
    response = await async_client.post(
        "/api/v1/auth/login-backup-code",
        json={
            "email": async_test_user.email,
            "password": "testpassword123",
            "backup_code": backup_code
        }
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    
    # Verify backup code was marked as used
    await db.refresh(async_test_user)
    assert async_test_user.two_fa_recovery_codes_used == 1


@pytest.mark.asyncio
async def test_rate_limiting_2fa_attempts(
    async_client: AsyncClient,
    async_test_user: User,
    db: AsyncSession
):
    """Test rate limiting for 2FA attempts."""
    # Enable 2FA
    two_fa = TwoFactorAuth()
    async_test_user.totp_enabled = True
    async_test_user.totp_secret = two_fa.generate_secret()
    await db.commit()
    
    # Make 5 failed attempts
    for i in range(5):
        response = await async_client.post(
            "/api/v1/auth/login-2fa",
            json={
                "email": async_test_user.email,
                "password": "testpassword123",
                "totp_code": "000000"
            }
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    # 6th attempt should be rate limited
    response = await async_client.post(
        "/api/v1/auth/login-2fa",
        json={
            "email": async_test_user.email,
            "password": "testpassword123",
            "totp_code": "000000"
        }
    )
    
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert "Too many failed attempts" in response.json()["detail"]