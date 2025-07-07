"""Email verification endpoints."""

import secrets
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from api.dependencies.auth import get_current_user
from core.config import settings
from db.session import get_db
from models.user import User
from schemas.base import MessageResponse
from services.email import send_verification_email

router = APIRouter()


@router.post("/send-verification", response_model=MessageResponse)
async def send_verification_email_endpoint(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Send verification email to current user.
    
    Args:
        background_tasks: Background tasks for sending email
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If user is already verified
    """
    if current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified",
        )
    
    # Generate verification token
    verification_token = secrets.token_urlsafe(32)
    current_user.email_verification_token = verification_token
    
    await db.commit()
    
    # Send email in background
    verification_url = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"
    background_tasks.add_task(
        send_verification_email,
        email=current_user.email,
        name=current_user.full_name or current_user.username,
        verification_url=verification_url,
    )
    
    return {"message": "Verification email sent successfully"}


@router.post("/verify/{token}", response_model=MessageResponse)
async def verify_email(
    token: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Verify email with token.
    
    Args:
        token: Verification token from email
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    # Find user by verification token
    result = await db.execute(
        select(User).where(User.email_verification_token == token)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token",
        )
    
    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified",
        )
    
    # Verify the user
    user.is_verified = True
    user.verified_at = datetime.utcnow()
    user.email_verification_token = None  # Clear the token
    
    await db.commit()
    
    return {"message": "Email verified successfully"}


@router.post("/resend-verification", response_model=MessageResponse)
async def resend_verification_email(
    background_tasks: BackgroundTasks,
    email: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Resend verification email for unverified users.
    
    Args:
        background_tasks: Background tasks for sending email
        email: User's email address
        db: Database session
        
    Returns:
        Success message (always returns success for security)
    """
    # Find user by email
    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()
    
    # Always return success for security (don't reveal if email exists)
    if not user or user.is_verified:
        return {"message": "If the email exists and is unverified, a verification email has been sent"}
    
    # Generate new verification token
    verification_token = secrets.token_urlsafe(32)
    user.email_verification_token = verification_token
    
    await db.commit()
    
    # Send email in background
    verification_url = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"
    background_tasks.add_task(
        send_verification_email,
        email=user.email,
        name=user.full_name or user.username,
        verification_url=verification_url,
    )
    
    return {"message": "If the email exists and is unverified, a verification email has been sent"}