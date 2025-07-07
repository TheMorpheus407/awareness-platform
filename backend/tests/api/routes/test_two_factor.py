"""Tests for Two-Factor Authentication endpoints."""

import pytest
import pyotp
import json
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from core.two_factor_auth import two_factor_auth
from models.user import User
from models.two_fa_attempt import TwoFAAttempt


@pytest.mark.asyncio
async def test_setup_2fa_success(
    async_client,
    test_user: User,
    auth_headers: dict,
    db_session: AsyncSession
):
    """Test successful 2FA setup."""
    # Setup request with correct password
    response = await async_client.post(
        "/api/auth/2fa/setup",
        json={"password": "TestPassword123!"},
        headers=auth_headers
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
    async_client,
    test_user: User,
    auth_headers: dict
):
    """Test 2FA setup with wrong password."""
    response = await async_client.post(
        "/api/auth/2fa/setup",
        json={"password": "WrongPassword"},
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Invalid password"


@pytest.mark.asyncio
async def test_setup_2fa_already_enabled(
    async_client,
    test_user: User,
    auth_headers: dict,
    db_session: AsyncSession
):
    """Test 2FA setup when already enabled."""
    # Enable 2FA for the user
    test_user.totp_enabled = True
    test_user.totp_secret = two_factor_auth.encrypt_secret("TESTSECRET")
    await db_session.commit()
    
    response = await async_client.post(
        "/api/auth/2fa/setup",
        json={"password": "TestPassword123!"},
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Two-factor authentication is already enabled"


@pytest.mark.asyncio
async def test_verify_2fa_success(
    async_client,
    test_user: User,
    auth_headers: dict,
    db_session: AsyncSession
):
    """Test successful 2FA verification."""
    # Setup 2FA first
    secret = two_factor_auth.generate_secret()
    test_user.totp_secret = two_factor_auth.encrypt_secret(secret)
    await db_session.commit()
    
    # Generate valid TOTP code
    totp = pyotp.TOTP(secret)
    code = totp.now()
    
    response = await async_client.post(
        "/api/auth/2fa/verify",
        json={"totp_code": code},
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Two-factor authentication enabled successfully"
    
    # Refresh user and check 2FA is enabled
    await db_session.refresh(test_user)
    assert test_user.totp_enabled is True
    assert test_user.totp_verified_at is not None


@pytest.mark.asyncio
async def test_verify_2fa_invalid_code(
    async_client,
    test_user: User,
    auth_headers: dict,
    db_session: AsyncSession
):
    """Test 2FA verification with invalid code."""
    # Setup 2FA
    secret = two_factor_auth.generate_secret()
    test_user.totp_secret = two_factor_auth.encrypt_secret(secret)
    await db_session.commit()
    
    response = await async_client.post(
        "/api/auth/2fa/verify",
        json={"totp_code": "000000"},
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Invalid verification code"


@pytest.mark.asyncio
async def test_login_with_2fa_enabled(
    async_client,
    test_user: User,
    db_session: AsyncSession
):
    """Test login when 2FA is enabled."""
    # Enable 2FA for user
    secret = two_factor_auth.generate_secret()
    test_user.totp_enabled = True
    test_user.totp_secret = two_factor_auth.encrypt_secret(secret)
    await db_session.commit()
    
    # Try standard login
    response = await async_client.post(
        "/api/auth/login",
        data={
            "username": test_user.email,
            "password": "TestPassword123!"
        }
    )
    
    assert response.status_code == status.HTTP_428_PRECONDITION_REQUIRED
    assert response.json()["detail"] == "Two-factor authentication required"
    assert response.headers.get("X-2FA-Required") == "true"


@pytest.mark.asyncio
async def test_login_2fa_success(
    async_client,
    test_user: User,
    db_session: AsyncSession
):
    """Test successful login with 2FA."""
    # Enable 2FA for user
    secret = two_factor_auth.generate_secret()
    test_user.totp_enabled = True
    test_user.totp_secret = two_factor_auth.encrypt_secret(secret)
    await db_session.commit()
    
    # Generate valid TOTP code
    totp = pyotp.TOTP(secret)
    code = totp.now()
    
    response = await async_client.post(
        "/api/auth/login-2fa",
        json={
            "email": test_user.email,
            "password": "TestPassword123!",
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
    async_client,
    test_user: User,
    db_session: AsyncSession
):
    """Test login with invalid 2FA code."""
    # Enable 2FA for user
    secret = two_factor_auth.generate_secret()
    test_user.totp_enabled = True
    test_user.totp_secret = two_factor_auth.encrypt_secret(secret)
    await db_session.commit()
    
    response = await async_client.post(
        "/api/auth/login-2fa",
        json={
            "email": test_user.email,
            "password": "TestPassword123!",
            "totp_code": "000000"
        }
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Invalid two-factor authentication code"


@pytest.mark.asyncio
async def test_disable_2fa_success(
    async_client,
    test_user: User,
    auth_headers: dict,
    db_session: AsyncSession
):
    """Test successful 2FA disable."""
    # Enable 2FA for user
    secret = two_factor_auth.generate_secret()
    test_user.totp_enabled = True
    test_user.totp_secret = two_factor_auth.encrypt_secret(secret)
    test_user.backup_codes = json.dumps(["TEST1-CODE1", "TEST2-CODE2"])
    await db_session.commit()
    
    # Generate valid TOTP code
    totp = pyotp.TOTP(secret)
    code = totp.now()
    
    response = await async_client.post(
        "/api/auth/2fa/disable",
        json={
            "password": "TestPassword123!",
            "totp_code": code
        },
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Two-factor authentication disabled successfully"
    
    # Verify 2FA is disabled
    await db_session.refresh(test_user)
    assert test_user.totp_enabled is False
    assert test_user.totp_secret is None
    assert test_user.backup_codes is None


@pytest.mark.asyncio
async def test_backup_codes_status(
    async_client,
    test_user: User,
    auth_headers: dict,
    db_session: AsyncSession
):
    """Test getting backup codes status."""
    # Enable 2FA with backup codes
    test_user.totp_enabled = True
    test_user.totp_secret = two_factor_auth.encrypt_secret("SECRET")
    
    # Generate and hash backup codes
    codes = two_factor_auth.generate_backup_codes()
    hashed_codes = [two_factor_auth.hash_backup_code(code) for code in codes]
    test_user.set_backup_codes(hashed_codes)
    test_user.two_fa_recovery_codes_used = 2
    await db_session.commit()
    
    response = await async_client.get(
        "/api/auth/2fa/backup-codes",
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total_codes"] == 8
    assert data["used_codes"] == 2
    assert data["remaining_codes"] == 6


@pytest.mark.asyncio
async def test_login_with_backup_code(
    async_client,
    test_user: User,
    db_session: AsyncSession
):
    """Test login using backup code."""
    # Enable 2FA and set backup codes
    test_user.totp_enabled = True
    test_user.totp_secret = two_factor_auth.encrypt_secret("SECRET")
    
    # Generate backup codes
    backup_code = "TEST1-CODE1"
    hashed_code = two_factor_auth.hash_backup_code(backup_code)
    test_user.set_backup_codes([hashed_code, "HASH2", "HASH3"])
    test_user.two_fa_recovery_codes_used = 0
    await db_session.commit()
    
    response = await async_client.post(
        "/api/auth/login-backup-code",
        json={
            "email": test_user.email,
            "password": "TestPassword123!",
            "backup_code": backup_code
        }
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    
    # Verify backup code was marked as used
    await db_session.refresh(test_user)
    assert test_user.two_fa_recovery_codes_used == 1
    codes = test_user.get_backup_codes()
    assert codes[0] == "USED"


@pytest.mark.asyncio
async def test_rate_limiting_2fa_attempts(
    async_client,
    test_user: User,
    db_session: AsyncSession
):
    """Test rate limiting for 2FA attempts."""
    # Enable 2FA
    test_user.totp_enabled = True
    test_user.totp_secret = two_factor_auth.encrypt_secret("SECRET")
    await db_session.commit()
    
    # Make 5 failed attempts
    for i in range(5):
        response = await async_client.post(
            "/api/auth/login-2fa",
            json={
                "email": test_user.email,
                "password": "TestPassword123!",
                "totp_code": "000000"
            }
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    # 6th attempt should be rate limited
    response = await async_client.post(
        "/api/auth/login-2fa",
        json={
            "email": test_user.email,
            "password": "TestPassword123!",
            "totp_code": "000000"
        }
    )
    
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert "Too many failed attempts" in response.json()["detail"]