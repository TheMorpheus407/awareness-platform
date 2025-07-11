"""Authentication routes."""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Form, Response, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from api.dependencies.auth import get_current_active_user
from api.dependencies.common import get_db
from core.config import settings
from core.security import SecurityUtils
from core.two_factor_auth import TwoFactorAuth
from models.user import User
from models.company import Company
from models.two_fa_attempt import TwoFAAttempt
from schemas.auth import (
    TokenResponse,
    LoginRequest,
    RefreshTokenRequest,
    RegistrationResponse,
    TwoFactorSetupRequest,
    TwoFactorSetupResponse,
    TwoFactorVerifyRequest,
    TwoFactorLoginRequest,
    ChangePasswordRequest,
    APIKeyCreate,
    APIKeyResponse,
    AuthenticationLog,
)
from schemas.company import CompanyRegistration
from schemas.user import UserCreate, User as UserSchema
from services.email import EmailService

router = APIRouter()


@router.get("/csrf-token")
async def get_csrf_token(request: Request) -> dict:
    """
    Get CSRF token for the current session.
    
    This endpoint is used by the frontend to get the CSRF token
    that must be included in all state-changing requests.
    
    Args:
        request: HTTP request object
        
    Returns:
        Dict containing the CSRF token
    """
    # The CSRF middleware will automatically set the token in the response
    # We just need to trigger it by accessing this endpoint
    csrf_token = getattr(request.state, "csrf_token", None)
    
    if not csrf_token:
        # This shouldn't happen if the middleware is properly configured
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="CSRF token not available"
        )
    
    return {
        "csrf_token": csrf_token,
        "header_name": "X-CSRF-Token",
        "cookie_name": "csrf_token"
    }


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
) -> TokenResponse:
    """
    OAuth2 compatible token login.
    
    Args:
        form_data: OAuth2 form data with username and password
        db: Database session
        request: HTTP request object
        
    Returns:
        Access and refresh tokens
        
    Raises:
        HTTPException: If credentials are invalid
    """
    # Get user by email (username field contains email)
    result = await db.execute(
        select(User).where(User.email == form_data.username.lower())
    )
    user = result.scalar_one_or_none()
    
    # Verify user and password
    if not user or not SecurityUtils.verify_password(form_data.password, user.password_hash):
        # Log failed attempt
        if user:
            attempt = TwoFAAttempt(
                user_id=user.id,
                attempt_type="login",
                success=False,
                ip_address=request.client.host if request else "unknown",
            )
            db.add(attempt)
            await db.commit()
            
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Check if 2FA is enabled
    if user.two_factor_enabled and user.two_factor_secret:
        # Return temporary token for 2FA verification
        temp_token = SecurityUtils.create_access_token(
            subject=str(user.id),
            expires_delta=timedelta(minutes=5),
            additional_claims={"temp": True, "purpose": "2fa"}
        )
        
        return TokenResponse(
            access_token=temp_token,
            token_type="bearer",
            expires_in=300,  # 5 minutes
            refresh_token=None,
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    await db.commit()
    
    # Create tokens
    access_token = SecurityUtils.create_access_token(subject=str(user.id))
    refresh_token = SecurityUtils.create_refresh_token(subject=str(user.id))
    
    # Log successful login
    attempt = TwoFAAttempt(
        user_id=user.id,
        attempt_type="login",
        success=True,
        ip_address=request.client.host if request else "unknown",
    )
    db.add(attempt)
    await db.commit()
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """
    Refresh access token using refresh token.
    
    Args:
        refresh_request: Refresh token request
        db: Database session
        
    Returns:
        New access and refresh tokens
        
    Raises:
        HTTPException: If refresh token is invalid
    """
    # TODO: Implement refresh token validation and new token generation
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Refresh token endpoint not implemented yet"
    )


@router.post("/register", response_model=RegistrationResponse)
async def register(
    company_data: CompanyRegistration,
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
) -> RegistrationResponse:
    """
    Register new company and admin user.
    
    Args:
        company_data: Company registration data
        user_data: User registration data
        db: Database session
        
    Returns:
        Registration response with company and user details
        
    Raises:
        HTTPException: If email already exists
    """
    # Check if email already exists
    result = await db.execute(
        select(User).where(User.email == user_data.email.lower())
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create company
    company = Company(**company_data.model_dump())
    db.add(company)
    await db.flush()  # Get company ID
    
    # Create admin user for the company
    user = User(
        **user_data.model_dump(exclude={"password"}),
        password_hash=SecurityUtils.get_password_hash(user_data.password),
        company_id=company.id,
        role="company_admin",
        is_verified=False,
    )
    db.add(user)
    await db.commit()
    
    # Send verification email
    email_service = EmailService()
    verification_sent = await email_service.send_verification_email(user)
    
    return RegistrationResponse(
        company=company,
        user=user,
        verification_email_sent=verification_sent
    )


@router.post("/logout")
async def logout(
    response: Response,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Logout current user.
    
    Args:
        response: HTTP response object
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Success message
    """
    # Log logout event
    attempt = TwoFAAttempt(
        user_id=current_user.id,
        attempt_type="logout",
        success=True,
        ip_address="unknown",  # TODO: Get from request
    )
    db.add(attempt)
    await db.commit()
    
    # Clear any cookies if used
    response.delete_cookie("access_token")
    
    return {"message": "Successfully logged out"}


@router.post("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Change password for authenticated user.
    
    Args:
        password_data: Password change request
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If current password is incorrect
    """
    # Verify current password
    if not SecurityUtils.verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect password"
        )
    
    # Update password
    current_user.password_hash = SecurityUtils.get_password_hash(password_data.new_password)
    
    # Log password change
    attempt = TwoFAAttempt(
        user_id=current_user.id,
        attempt_type="password_change",
        success=True,
        ip_address="unknown",  # TODO: Get from request
    )
    db.add(attempt)
    
    await db.commit()
    
    # TODO: Send email notification about password change
    
    return {"message": "Password successfully changed"}


@router.get("/me", response_model=UserSchema)
async def get_current_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get current user profile.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Current user details
    """
    return current_user


@router.get("/sessions", response_model=list[AuthenticationLog])
async def get_user_sessions(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> list[AuthenticationLog]:
    """
    Get user's authentication sessions.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of authentication sessions
    """
    # Get recent authentication logs
    result = await db.execute(
        select(TwoFAAttempt)
        .where(TwoFAAttempt.user_id == current_user.id)
        .order_by(TwoFAAttempt.created_at.desc())
        .limit(20)
    )
    attempts = result.scalars().all()
    
    # Convert to authentication logs
    logs = []
    for attempt in attempts:
        logs.append(AuthenticationLog(
            id=str(attempt.id),
            user_id=str(attempt.user_id),
            event_type=attempt.attempt_type,
            success=attempt.success,
            ip_address=attempt.ip_address,
            timestamp=attempt.created_at,
        ))
    
    return logs