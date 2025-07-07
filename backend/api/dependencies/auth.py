"""Authentication dependencies."""

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.security import decode_token
from db.session import get_db
from models.user import User
from schemas.user import TokenPayload

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> User:
    """
    Get current authenticated user from JWT token.
    
    Args:
        db: Database session
        token: JWT token from Authorization header
        
    Returns:
        Current user object
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = decode_token(token)
        token_data = TokenPayload(**payload)
        
        if token_data.type != "access":
            raise credentials_exception
            
    except (JWTError, ValueError):
        raise credentials_exception
    
    # Get user from database
    result = await db.execute(
        select(User).where(User.id == int(token_data.sub))
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
        
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current active user.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Current user if active
        
    Raises:
        HTTPException: If user is not active
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


async def require_admin(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Require admin privileges.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Current user if admin
        
    Raises:
        HTTPException: If user is not admin
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user


async def require_company_admin(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Require company admin privileges.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Current user if company admin or platform admin
        
    Raises:
        HTTPException: If user is not company admin
    """
    if not (current_user.is_company_admin or current_user.is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Company admin privileges required",
        )
    return current_user