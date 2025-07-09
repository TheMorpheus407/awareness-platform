"""Two-Factor Authentication endpoints."""

from datetime import datetime, timedelta
from typing import Any, List
import json

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from api.dependencies.auth import get_current_user
from core.security import verify_password
from core.two_factor_auth import two_factor_auth
from core.middleware import limiter
from db.session import get_db
from models.user import User
from models.two_fa_attempt import TwoFAAttempt
from schemas.user import (
    TwoFactorSetupRequest,
    TwoFactorSetupResponse,
    TwoFactorVerifyRequest,
    TwoFactorDisableRequest,
)

router = APIRouter()


async def check_rate_limit(db: AsyncSession, user_id: str, attempt_type: str) -> None:
    """Check if user has exceeded rate limit for 2FA attempts."""
    # Check attempts in last 15 minutes
    time_threshold = datetime.utcnow() - timedelta(minutes=15)
    
    result = await db.execute(
        select(func.count(TwoFAAttempt.id))
        .where(
            and_(
                TwoFAAttempt.user_id == user_id,
                TwoFAAttempt.attempt_type == attempt_type,
                TwoFAAttempt.created_at >= time_threshold,
                TwoFAAttempt.success == False
            )
        )
    )
    
    failed_attempts = result.scalar() or 0
    
    if failed_attempts >= 5:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed attempts. Please try again later."
        )


async def log_attempt(
    db: AsyncSession,
    user_id: str,
    attempt_type: str,
    success: bool,
    request: Request
) -> None:
    """Log a 2FA attempt."""
    attempt = TwoFAAttempt(
        user_id=user_id,
        attempt_type=attempt_type,
        success=success,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent", "")[:500]  # Limit length
    )
    db.add(attempt)
    await db.commit()


@router.post("/setup", response_model=TwoFactorSetupResponse)
@limiter.limit("3/hour")
async def setup_two_factor(
    request: Request,
    setup_request: TwoFactorSetupRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Setup Two-Factor Authentication for the current user.
    
    Requires password confirmation for security.
    Returns QR code and backup codes.
    """
    # Verify password
    if not verify_password(setup_request.password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password"
        )
    
    # Check if 2FA is already enabled
    if current_user.has_2fa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Two-factor authentication is already enabled"
        )
    
    # Generate new secret
    secret = two_factor_auth.generate_secret()
    
    # Generate QR code
    qr_code = two_factor_auth.generate_qr_code(current_user.email, secret)
    
    # Generate backup codes
    backup_codes = two_factor_auth.generate_backup_codes()
    
    # Hash backup codes for storage
    hashed_codes = [two_factor_auth.hash_backup_code(code) for code in backup_codes]
    
    # Store encrypted secret and hashed backup codes (but don't enable yet)
    current_user.totp_secret = two_factor_auth.encrypt_secret(secret)
    current_user.set_backup_codes(hashed_codes)
    
    await db.commit()
    
    return TwoFactorSetupResponse(
        secret=secret,
        qr_code=qr_code,
        backup_codes=backup_codes,
        manual_entry_key=secret  # For manual entry
    )


@router.post("/verify")
@limiter.limit("10/hour")
async def verify_two_factor_setup(
    request: Request,
    verify_request: TwoFactorVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Verify 2FA setup by validating a TOTP code.
    
    This completes the 2FA setup process.
    """
    # Check rate limit
    await check_rate_limit(db, str(current_user.id), "totp")
    
    # Check if secret exists
    if not current_user.totp_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Two-factor authentication setup not started"
        )
    
    # Decrypt secret
    try:
        secret = two_factor_auth.decrypt_secret(current_user.totp_secret)
    except:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to decrypt 2FA secret"
        )
    
    # Verify TOTP code
    if two_factor_auth.verify_totp(secret, verify_request.totp_code):
        # Enable 2FA
        current_user.totp_enabled = True
        current_user.totp_verified_at = datetime.utcnow()
        
        # Log successful attempt
        await log_attempt(db, str(current_user.id), "totp", True, request)
        
        await db.commit()
        
        return {"message": "Two-factor authentication enabled successfully"}
    else:
        # Log failed attempt
        await log_attempt(db, str(current_user.id), "totp", False, request)
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code"
        )


@router.post("/disable")
@limiter.limit("5/hour")
async def disable_two_factor(
    request: Request,
    disable_request: TwoFactorDisableRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Disable Two-Factor Authentication.
    
    Requires both password and TOTP code for security.
    """
    # Check if 2FA is enabled
    if not current_user.has_2fa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Two-factor authentication is not enabled"
        )
    
    # Verify password
    if not verify_password(disable_request.password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password"
        )
    
    # Check rate limit
    await check_rate_limit(db, str(current_user.id), "totp")
    
    # Decrypt secret and verify TOTP
    try:
        secret = two_factor_auth.decrypt_secret(current_user.totp_secret)
    except:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to decrypt 2FA secret"
        )
    
    if two_factor_auth.verify_totp(secret, disable_request.totp_code):
        # Disable 2FA
        current_user.totp_enabled = False
        current_user.totp_secret = None
        current_user.totp_verified_at = None
        current_user.backup_codes = None
        current_user.two_fa_recovery_codes_used = 0
        
        # Log successful attempt
        await log_attempt(db, str(current_user.id), "totp", True, request)
        
        await db.commit()
        
        return {"message": "Two-factor authentication disabled successfully"}
    else:
        # Log failed attempt
        await log_attempt(db, str(current_user.id), "totp", False, request)
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code"
        )


@router.get("/backup-codes")
async def get_backup_codes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get the number of remaining backup codes.
    
    Does not return the actual codes for security.
    """
    if not current_user.has_2fa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Two-factor authentication is not enabled"
        )
    
    codes = current_user.get_backup_codes()
    if codes:
        total_codes = len(codes)
        used_codes = current_user.two_fa_recovery_codes_used
        remaining = total_codes - used_codes
        
        return {
            "total_codes": total_codes,
            "used_codes": used_codes,
            "remaining_codes": remaining
        }
    
    return {
        "total_codes": 0,
        "used_codes": 0,
        "remaining_codes": 0
    }


@router.post("/regenerate-backup-codes")
@limiter.limit("2/day")
async def regenerate_backup_codes(
    request: Request,
    regenerate_request: TwoFactorDisableRequest,  # Reuse schema - requires password and TOTP
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Regenerate backup codes.
    
    Requires password and TOTP code for security.
    Returns new backup codes.
    """
    # Check if 2FA is enabled
    if not current_user.has_2fa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Two-factor authentication is not enabled"
        )
    
    # Verify password
    if not verify_password(regenerate_request.password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password"
        )
    
    # Verify TOTP
    try:
        secret = two_factor_auth.decrypt_secret(current_user.totp_secret)
    except:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to decrypt 2FA secret"
        )
    
    if not two_factor_auth.verify_totp(secret, regenerate_request.totp_code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code"
        )
    
    # Generate new backup codes
    backup_codes = two_factor_auth.generate_backup_codes()
    
    # Hash and store
    hashed_codes = [two_factor_auth.hash_backup_code(code) for code in backup_codes]
    current_user.set_backup_codes(hashed_codes)
    current_user.two_fa_recovery_codes_used = 0
    
    await db.commit()
    
    return {
        "backup_codes": backup_codes,
        "message": "New backup codes generated. Please save them securely."
    }