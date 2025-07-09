"""Password reset endpoints."""

import secrets
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.config import settings
from core.security import get_password_hash, verify_password
from db.session import get_db
from models.user import User
from schemas.base import MessageResponse
from services.email import send_password_reset_email

router = APIRouter()


class PasswordResetRequest(BaseModel):
    """Password reset request schema."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation schema."""
    token: str
    new_password: str


@router.post("/request", response_model=MessageResponse)
async def request_password_reset(
    background_tasks: BackgroundTasks,
    data: PasswordResetRequest,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Request password reset email.
    
    Args:
        background_tasks: Background tasks for sending email
        data: Password reset request data
        db: Database session
        
    Returns:
        Success message (always returns success for security)
    """
    # Find user by email
    result = await db.execute(
        select(User).where(User.email == data.email)
    )
    user = result.scalar_one_or_none()
    
    # Always return success for security (don't reveal if email exists)
    success_message = "If the email exists, a password reset link has been sent"
    
    if not user:
        return {"message": success_message}
    
    # Generate reset token and expiry
    reset_token = secrets.token_urlsafe(32)
    user.password_reset_token = reset_token
    user.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
    
    await db.commit()
    
    # Send reset email in background
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
    background_tasks.add_task(
        send_password_reset_email,
        email=user.email,
        name=user.full_name,
        reset_url=reset_url,
    )
    
    return {"message": success_message}


@router.post("/reset", response_model=MessageResponse)
async def reset_password(
    data: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Reset password with token.
    
    Args:
        data: Password reset confirmation data
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    # Find user by reset token
    result = await db.execute(
        select(User).where(User.password_reset_token == data.token)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token",
        )
    
    # Check if token has expired
    if user.password_reset_expires < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired",
        )
    
    # Validate password strength
    if len(data.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long",
        )
    
    # Update password
    user.password_hash = get_password_hash(data.new_password)
    user.password_reset_token = None
    user.password_reset_expires = None
    user.password_changed_at = datetime.utcnow()
    
    await db.commit()
    
    return {"message": "Password reset successfully"}


@router.post("/validate-token", response_model=MessageResponse)
async def validate_reset_token(
    token: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Validate a password reset token.
    
    Args:
        token: Reset token to validate
        db: Database session
        
    Returns:
        Success message if token is valid
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    # Find user by reset token
    result = await db.execute(
        select(User).where(User.password_reset_token == token)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token",
        )
    
    # Check if token has expired
    if user.password_reset_expires < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired",
        )
    
    return {"message": "Token is valid"}