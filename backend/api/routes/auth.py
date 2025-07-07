"""Authentication endpoints."""

from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
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
from core.middleware import limiter
from db.session import get_db
from models.user import User
from schemas.user import Token, UserCreate, UserResponse
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
    
    # Check if username already exists
    result = await db.execute(
        select(User).where(User.username == user_data.username)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )
    
    # Generate email verification token
    verification_token = secrets.token_urlsafe(32)
    
    # Create new user
    user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=get_password_hash(user_data.password),
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
    Login endpoint for OAuth2 password flow.
    
    Args:
        db: Database session
        form_data: OAuth2 form data with username (email) and password
        
    Returns:
        Access and refresh tokens
        
    Raises:
        HTTPException: If credentials are invalid
    """
    # Get user by email
    result = await db.execute(
        select(User).where(User.email == form_data.username)
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
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
    user.last_login = db.func.now()
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