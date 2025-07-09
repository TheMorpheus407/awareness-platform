"""Two-factor authentication routes."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import pyotp

from api.dependencies.auth import get_current_active_user
from api.dependencies.common import get_db
from core.security import SecurityUtils
from core.two_factor_auth import TwoFactorAuth
from models.user import User
from models.two_fa_attempt import TwoFAAttempt
from schemas.auth import (
    TwoFactorSetupRequest,
    TwoFactorSetupResponse,
    TwoFactorVerifyRequest,
    TwoFactorLoginRequest,
    TokenResponse,
)

router = APIRouter()


@router.post("/setup", response_model=TwoFactorSetupResponse)
async def setup_two_factor(
    setup_request: TwoFactorSetupRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TwoFactorSetupResponse:
    """
    Set up two-factor authentication for user.
    
    Args:
        setup_request: Setup request with current password
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Setup response with QR code and backup codes
        
    Raises:
        HTTPException: If password is incorrect or 2FA already enabled
    """
    # Verify current password
    if not SecurityUtils.verify_password(setup_request.password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect password"
        )
    
    # Check if 2FA is already enabled
    if current_user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Two-factor authentication is already enabled"
        )
    
    # Generate secret and QR code
    two_fa = TwoFactorAuth()
    secret = two_fa.generate_secret()
    qr_code = two_fa.generate_qr_code(
        secret,
        current_user.email
    )
    
    # Generate backup codes
    backup_codes = two_fa.generate_backup_codes()
    
    # Store secret temporarily (will be confirmed on verification)
    current_user.two_factor_secret = secret
    current_user.two_factor_backup_codes = backup_codes
    
    await db.commit()
    
    return TwoFactorSetupResponse(
        secret=secret,
        qr_code=qr_code,
        backup_codes=backup_codes,
    )


@router.post("/verify")
async def verify_two_factor(
    verify_request: TwoFactorVerifyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Verify and enable two-factor authentication.
    
    Args:
        verify_request: Verification request with TOTP code
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If code is invalid or 2FA not set up
    """
    # Check if secret is set
    if not current_user.two_factor_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Two-factor authentication not set up"
        )
    
    # Verify the code
    two_fa = TwoFactorAuth()
    if not two_fa.verify_token(current_user.two_factor_secret, verify_request.code):
        # Log failed attempt
        attempt = TwoFAAttempt(
            user_id=current_user.id,
            attempt_type="2fa_setup",
            success=False,
            ip_address="unknown",  # TODO: Get from request
        )
        db.add(attempt)
        await db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code"
        )
    
    # Enable 2FA
    current_user.two_factor_enabled = True
    
    # Log successful setup
    attempt = TwoFactorAttempt(
        user_id=current_user.id,
        attempt_type="2fa_setup",
        success=True,
        ip_address="unknown",  # TODO: Get from request
    )
    db.add(attempt)
    
    await db.commit()
    
    return {"message": "Two-factor authentication enabled successfully"}


@router.post("/disable")
async def disable_two_factor(
    password: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Disable two-factor authentication.
    
    Args:
        password: Current password for verification
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If password is incorrect or 2FA not enabled
    """
    # Check if 2FA is enabled
    if not current_user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Two-factor authentication is not enabled"
        )
    
    # Verify password
    if not SecurityUtils.verify_password(password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect password"
        )
    
    # Disable 2FA
    current_user.two_factor_enabled = False
    current_user.two_factor_secret = None
    current_user.two_factor_backup_codes = None
    
    # Log disable event
    attempt = TwoFactorAttempt(
        user_id=current_user.id,
        attempt_type="2fa_disable",
        success=True,
        ip_address="unknown",  # TODO: Get from request
    )
    db.add(attempt)
    
    await db.commit()
    
    return {"message": "Two-factor authentication disabled successfully"}


@router.post("/backup-codes/regenerate")
async def regenerate_backup_codes(
    password: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Regenerate backup codes.
    
    Args:
        password: Current password for verification
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        New backup codes
        
    Raises:
        HTTPException: If password is incorrect or 2FA not enabled
    """
    # Check if 2FA is enabled
    if not current_user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Two-factor authentication is not enabled"
        )
    
    # Verify password
    if not SecurityUtils.verify_password(password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect password"
        )
    
    # Generate new backup codes
    two_fa = TwoFactorAuth()
    backup_codes = two_fa.generate_backup_codes()
    current_user.two_factor_backup_codes = backup_codes
    
    await db.commit()
    
    return {
        "message": "Backup codes regenerated successfully",
        "backup_codes": backup_codes,
    }


@router.post("/verify-login", response_model=TokenResponse)
async def verify_two_factor_login(
    login_request: TwoFactorLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Verify 2FA code during login.
    
    Args:
        login_request: Login request with session token and 2FA code
        db: Database session
        
    Returns:
        Access and refresh tokens
        
    Raises:
        HTTPException: If session token or code is invalid
    """
    # TODO: Implement session token verification and actual token generation
    # This is a placeholder implementation
    
    # Token functions are available via SecurityUtils
    from core.config import settings
    from jose import jwt, JWTError
    
    try:
        # Decode temporary session token
        payload = jwt.decode(
            login_request.session_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        if not payload.get("temp") or payload.get("purpose") != "2fa":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid session token"
            )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid session token"
            )
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session token"
        )
    
    # Get user
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # Verify 2FA code
    is_valid = False
    
    # Try TOTP code first
    two_fa = TwoFactorAuth()
    if two_fa.verify_token(user.two_factor_secret, login_request.code):
        is_valid = True
    else:
        # Try backup codes
        if user.two_factor_backup_codes and login_request.code in user.two_factor_backup_codes:
            # Remove used backup code
            backup_codes = user.two_factor_backup_codes.copy()
            backup_codes.remove(login_request.code)
            user.two_factor_backup_codes = backup_codes
            is_valid = True
    
    if not is_valid:
        # Log failed attempt
        attempt = TwoFAAttempt(
            user_id=user.id,
            attempt_type="2fa_login",
            success=False,
            ip_address="unknown",  # TODO: Get from request
        )
        db.add(attempt)
        await db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code"
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    
    # Log successful 2FA
    attempt = TwoFactorAttempt(
        user_id=user.id,
        attempt_type="2fa_login",
        success=True,
        ip_address="unknown",  # TODO: Get from request
    )
    db.add(attempt)
    
    await db.commit()
    
    # Create tokens
    access_token = SecurityUtils.create_access_token(subject=str(user.id))
    refresh_token = SecurityUtils.create_refresh_token(subject=str(user.id))
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )