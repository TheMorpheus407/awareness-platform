"""Email verification routes."""

import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from api.dependencies.auth import get_current_active_user
from api.dependencies.common import get_db
from models.user import User
from schemas.auth import VerifyEmailRequest
from services.email import EmailService

router = APIRouter()


@router.post("/verify")
async def verify_email(
    request: VerifyEmailRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Verify email address with token.
    
    Args:
        request: Email verification request with token
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If token is invalid
    """
    # Find user by verification token
    result = await db.execute(
        select(User).where(
            and_(
                User.verification_token == request.token,
                User.is_verified == False,
            )
        )
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token"
        )
    
    # Check if token is expired (24 hours)
    if user.created_at < datetime.utcnow() - timedelta(hours=24):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token expired"
        )
    
    # Verify user
    user.is_verified = True
    user.verification_token = None
    user.verified_at = datetime.utcnow()
    
    await db.commit()
    
    return {"message": "Email verified successfully"}


@router.post("/resend")
async def resend_verification_email(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Resend email verification.
    
    Args:
        background_tasks: Background task queue
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If email already verified
    """
    # Check if already verified
    if current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )
    
    # Generate new verification token
    current_user.verification_token = secrets.token_urlsafe(32)
    await db.commit()
    
    # Send verification email in background
    email_service = EmailService()
    background_tasks.add_task(
        email_service.send_verification_email,
        user=current_user,
    )
    
    return {"message": "Verification email sent"}


@router.get("/status")
async def get_verification_status(
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Get email verification status.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Verification status
    """
    return {
        "email": current_user.email,
        "is_verified": current_user.is_verified,
        "verified_at": current_user.verified_at,
    }