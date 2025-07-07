"""Authentication endpoints."""

from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
import secrets

from api.dependencies.auth import get_current_user
from core.config import settings
from core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
    get_password_hash,
    decode_token,
)
from core.two_factor_auth import two_factor_auth
from core.middleware import limiter
from db.session import get_db
from models.user import User
from models.two_fa_attempt import TwoFAAttempt
from schemas.user import Token, UserCreate, UserResponse, TwoFactorLoginRequest, BackupCodeVerifyRequest
from services.email import send_verification_email

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(
    request: Request,
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Register a new user.
    
    Args:
        user_data: User registration data
        db: Database session
        
    Returns:
        Created user
        
    Raises:
        HTTPException: If email already exists
    """
    # Check if user already exists by email
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    
    # Generate email verification token
    verification_token = secrets.token_urlsafe(32)
    
    # Create new user
    user = User(
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        phone=user_data.phone,
        role=user_data.role,
        is_active=user_data.is_active,
        company_id=user_data.company_id,
        email_verification_token=verification_token,
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # Send verification email in background
    verification_url = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"
    background_tasks.add_task(
        send_verification_email,
        email=user.email,
        name=user.full_name,
        verification_url=verification_url,
    )
    
    return user


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
async def login(
    request: Request,
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    """
    Login endpoint for OAuth2 password flow with 2FA support.
    
    Args:
        db: Database session
        form_data: OAuth2 form data with username (email) and password
        
    Returns:
        Access and refresh tokens
        
    Raises:
        HTTPException: If credentials are invalid or 2FA is required
    """
    # Get user by email
    result = await db.execute(
        select(User).where(User.email == form_data.username)
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    
    # Check if 2FA is enabled
    if user.has_2fa_enabled:
        # Check for TOTP code in form_data.scopes (OAuth2 hack for additional fields)
        # Since OAuth2PasswordRequestForm doesn't support custom fields,
        # we need to use a different endpoint for 2FA login
        raise HTTPException(
            status_code=status.HTTP_428_PRECONDITION_REQUIRED,
            detail="Two-factor authentication required",
            headers={"X-2FA-Required": "true"},
        )
    
    # Create tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = create_refresh_token(
        subject=user.id, expires_delta=refresh_token_expires
    )
    
    # Update last login
    user.last_login = datetime.utcnow()
    await db.commit()
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/login-2fa", response_model=Token)
@limiter.limit("10/minute")
async def login_with_2fa(
    request: Request,
    login_data: TwoFactorLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Login endpoint with Two-Factor Authentication support.
    
    Args:
        request: FastAPI request object
        login_data: Login credentials with optional TOTP code
        db: Database session
        
    Returns:
        Access and refresh tokens
        
    Raises:
        HTTPException: If credentials or TOTP code are invalid
    """
    # Get user by email
    result = await db.execute(
        select(User).where(User.email == login_data.email)
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    
    # Check if 2FA is enabled
    if user.has_2fa_enabled:
        if not login_data.totp_code:
            raise HTTPException(
                status_code=status.HTTP_428_PRECONDITION_REQUIRED,
                detail="Two-factor authentication code required",
            )
        
        # Check rate limit
        time_threshold = datetime.utcnow() - timedelta(minutes=15)
        result = await db.execute(
            select(func.count(TwoFAAttempt.id))
            .where(
                and_(
                    TwoFAAttempt.user_id == user.id,
                    TwoFAAttempt.attempt_type == "totp",
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
        
        # Verify TOTP code
        try:
            secret = two_factor_auth.decrypt_secret(user.totp_secret)
            is_valid = two_factor_auth.verify_totp(secret, login_data.totp_code)
        except:
            is_valid = False
        
        # Log attempt
        attempt = TwoFAAttempt(
            user_id=user.id,
            attempt_type="totp",
            success=is_valid,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("User-Agent", "")[:500]
        )
        db.add(attempt)
        
        if not is_valid:
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid two-factor authentication code",
            )
    
    # Create tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = create_refresh_token(
        subject=user.id, expires_delta=refresh_token_expires
    )
    
    # Update last login
    user.last_login_at = datetime.utcnow()
    await db.commit()
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/login-backup-code", response_model=Token)
@limiter.limit("5/hour")
async def login_with_backup_code(
    request: Request,
    login_data: BackupCodeVerifyRequest,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Login using a backup code when TOTP is not available.
    
    Args:
        request: FastAPI request object
        login_data: Login credentials with backup code
        db: Database session
        
    Returns:
        Access and refresh tokens
        
    Raises:
        HTTPException: If credentials or backup code are invalid
    """
    # Get user by email
    result = await db.execute(
        select(User).where(User.email == login_data.email)
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    
    if not user.has_2fa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Two-factor authentication is not enabled",
        )
    
    # Get backup codes
    backup_codes = user.get_backup_codes()
    if not backup_codes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No backup codes available",
        )
    
    # Check if all codes are used
    if user.two_fa_recovery_codes_used >= len(backup_codes):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="All backup codes have been used",
        )
    
    # Verify backup code
    code_valid = False
    code_index = -1
    
    for i, hashed_code in enumerate(backup_codes):
        if two_factor_auth.verify_backup_code(login_data.backup_code, hashed_code):
            code_valid = True
            code_index = i
            break
    
    # Log attempt
    attempt = TwoFAAttempt(
        user_id=user.id,
        attempt_type="backup_code",
        success=code_valid,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent", "")[:500]
    )
    db.add(attempt)
    
    if not code_valid:
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid backup code",
        )
    
    # Mark code as used by replacing it with "USED"
    backup_codes[code_index] = "USED"
    user.set_backup_codes(backup_codes)
    user.two_fa_recovery_codes_used += 1
    
    # Create tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = create_refresh_token(
        subject=user.id, expires_delta=refresh_token_expires
    )
    
    # Update last login
    user.last_login_at = datetime.utcnow()
    await db.commit()
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Refresh access token using refresh token.
    
    Args:
        refresh_token: Valid refresh token
        db: Database session
        
    Returns:
        New access and refresh tokens
        
    Raises:
        HTTPException: If refresh token is invalid
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise credentials_exception
            
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
            
    except Exception:
        raise credentials_exception
    
    # Get user
    result = await db.execute(
        select(User).where(User.id == int(user_id))
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise credentials_exception
    
    # Create new tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    new_refresh_token = create_refresh_token(
        subject=user.id, expires_delta=refresh_token_expires
    )
    
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get current user information.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User information
    """
    return current_user