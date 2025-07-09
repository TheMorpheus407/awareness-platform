"""Password reset routes."""

from datetime import datetime, timedelta
import secrets

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from api.dependencies.common import get_db
from core.security import SecurityUtils
from models.user import User
from models.password_reset_token import PasswordResetToken
from schemas.auth import ForgotPasswordRequest, ResetPasswordRequest
from services.email import EmailService

router = APIRouter()


@router.post("/forgot")
async def forgot_password(
    request: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Request password reset email.
    
    Args:
        request: Forgot password request with email
        background_tasks: Background task queue
        db: Database session
        
    Returns:
        Success message (always returns success for security)
    """
    # Find user by email
    result = await db.execute(
        select(User).where(User.email == request.email.lower())
    )
    user = result.scalar_one_or_none()
    
    # Always return success to prevent email enumeration
    if not user:
        return {
            "message": "If an account with that email exists, a password reset link has been sent."
        }
    
    # Check if user is active
    if not user.is_active:
        return {
            "message": "If an account with that email exists, a password reset link has been sent."
        }
    
    # Delete any existing tokens for this user
    await db.execute(
        select(PasswordResetToken)
        .where(PasswordResetToken.user_id == user.id)
        .delete()
    )
    
    # Generate reset token
    token = secrets.token_urlsafe(32)
    reset_token = PasswordResetToken(
        user_id=user.id,
        token=token,
        expires_at=datetime.utcnow() + timedelta(hours=1),
    )
    db.add(reset_token)
    await db.commit()
    
    # Send reset email in background
    email_service = EmailService()
    background_tasks.add_task(
        email_service.send_password_reset_email,
        user=user,
        token=token,
    )
    
    return {
        "message": "If an account with that email exists, a password reset link has been sent."
    }


@router.post("/reset")
async def reset_password(
    request: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Reset password with token.
    
    Args:
        request: Reset password request with token and new password
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    # Find valid token
    result = await db.execute(
        select(PasswordResetToken)
        .where(
            and_(
                PasswordResetToken.token == request.token,
                PasswordResetToken.expires_at > datetime.utcnow(),
                PasswordResetToken.used_at.is_(None),
            )
        )
    )
    reset_token = result.scalar_one_or_none()
    
    if not reset_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Get user
    result = await db.execute(
        select(User).where(User.id == reset_token.user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Update password
    user.password_hash = SecurityUtils.hash_password(request.new_password)
    
    # Mark token as used
    reset_token.used_at = datetime.utcnow()
    
    await db.commit()
    
    # TODO: Send confirmation email
    
    return {"message": "Password reset successfully"}


@router.post("/validate-token")
async def validate_reset_token(
    token: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Validate password reset token.
    
    Args:
        token: Reset token to validate
        db: Database session
        
    Returns:
        Validation result
    """
    # Find valid token
    result = await db.execute(
        select(PasswordResetToken)
        .where(
            and_(
                PasswordResetToken.token == token,
                PasswordResetToken.expires_at > datetime.utcnow(),
                PasswordResetToken.used_at.is_(None),
            )
        )
    )
    reset_token = result.scalar_one_or_none()
    
    if not reset_token:
        return {
            "valid": False,
            "message": "Invalid or expired token"
        }
    
    # Check if user is still active
    result = await db.execute(
        select(User).where(
            and_(
                User.id == reset_token.user_id,
                User.is_active == True,
            )
        )
    )
    user = result.scalar_one_or_none()
    
    if not user:
        return {
            "valid": False,
            "message": "Invalid or expired token"
        }
    
    return {
        "valid": True,
        "message": "Token is valid",
        "email": user.email,
    }