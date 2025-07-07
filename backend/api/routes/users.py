"""User management endpoints."""

from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from api.dependencies import (
    get_current_active_user,
    require_admin,
    get_pagination_params,
)
from core.security import get_password_hash
from db.session import get_db
from models.user import User
from schemas.user import UserCreate, UserUpdate, UserResponse

router = APIRouter()


@router.get("/", response_model=List[UserResponse])
async def get_users(
    db: AsyncSession = Depends(get_db),
    pagination: tuple[int, int] = Depends(get_pagination_params),
    current_user: User = Depends(require_admin),
) -> Any:
    """
    Get all users (admin only).
    
    Args:
        db: Database session
        pagination: Skip and limit values
        current_user: Current admin user
        
    Returns:
        List of users
    """
    skip, limit = pagination
    
    result = await db.execute(
        select(User)
        .offset(skip)
        .limit(limit)
        .order_by(User.created_at.desc())
    )
    users = result.scalars().all()
    
    return users


@router.get("/count", response_model=dict)
async def get_users_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Any:
    """
    Get total user count (admin only).
    
    Args:
        db: Database session
        current_user: Current admin user
        
    Returns:
        Total user count
    """
    result = await db.execute(select(func.count(User.id)))
    count = result.scalar()
    
    return {"count": count}


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get a specific user.
    
    Args:
        user_id: User ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        User information
        
    Raises:
        HTTPException: If user not found or unauthorized
    """
    # Users can only view their own profile unless they're admin
    if user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this user",
        )
    
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return user


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Any:
    """
    Create a new user (admin only).
    
    Args:
        user_data: User creation data
        db: Database session
        current_user: Current admin user
        
    Returns:
        Created user
        
    Raises:
        HTTPException: If email already exists
    """
    # Check if user already exists
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Create new user
    user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        phone=user_data.phone,
        role=user_data.role,
        is_active=user_data.is_active,
        company_id=user_data.company_id,
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return user


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Update a user.
    
    Args:
        user_id: User ID
        user_update: User update data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Updated user
        
    Raises:
        HTTPException: If user not found or unauthorized
    """
    # Users can only update their own profile unless they're admin
    if user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user",
        )
    
    # Get user
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Only admins can change roles
    if user_update.role and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can change user roles",
        )
    
    # Update user fields
    update_data = user_update.model_dump(exclude_unset=True)
    
    # Hash password if provided
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
        user.password_changed_at = db.func.now()
    
    # Check if email is being changed and if it's already taken
    if "email" in update_data and update_data["email"] != user.email:
        result = await db.execute(
            select(User).where(User.email == update_data["email"])
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
    
    # Apply updates
    for field, value in update_data.items():
        setattr(user, field, value)
    
    await db.commit()
    await db.refresh(user)
    
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> None:
    """
    Delete a user (admin only).
    
    Args:
        user_id: User ID
        db: Database session
        current_user: Current admin user
        
    Raises:
        HTTPException: If user not found
    """
    # Prevent self-deletion
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )
    
    # Get user
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Delete user
    await db.delete(user)
    await db.commit()