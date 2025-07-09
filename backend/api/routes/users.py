"""User management routes."""

from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, or_
from sqlalchemy.orm import selectinload

from api.dependencies.auth import (
    get_current_active_user,
    require_admin,
    require_company_admin,
    require_company_member,
)
from api.dependencies.common import get_db, get_pagination_params
from core.security import get_password_hash
from models.user import User, UserRole
from models.company import Company
from schemas.user import (
    UserCreate,
    UserUpdate,
    User as UserSchema,
    UserListResponse,
    UserWithCompany,
)

router = APIRouter()


@router.get("/", response_model=UserListResponse)
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    pagination: tuple[int, int] = Depends(get_pagination_params),
    search: Optional[str] = Query(None, description="Search in name or email"),
    role: Optional[UserRole] = Query(None, description="Filter by role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    company_id: Optional[UUID] = Query(None, description="Filter by company"),
) -> UserListResponse:
    """
    List users with pagination and filters.
    
    Args:
        db: Database session
        current_user: Current authenticated user
        pagination: Offset and limit
        search: Search term
        role: Filter by role
        is_active: Filter by active status
        company_id: Filter by company
        
    Returns:
        Paginated list of users
    """
    offset, limit = pagination
    
    # Base query
    query = select(User).options(selectinload(User.company))
    
    # Apply filters based on user role
    if current_user.role == UserRole.COMPANY_ADMIN:
        # Company admins can only see users from their company
        query = query.where(User.company_id == current_user.company_id)
    elif current_user.role == UserRole.USER:
        # Regular users can only see themselves
        query = query.where(User.id == current_user.id)
    elif company_id and current_user.role in [UserRole.ADMIN, UserRole.SUPERUSER]:
        # Admins can filter by company
        query = query.where(User.company_id == company_id)
    
    # Apply search filter
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                User.email.ilike(search_term),
                User.first_name.ilike(search_term),
                User.last_name.ilike(search_term),
            )
        )
    
    # Apply role filter
    if role:
        query = query.where(User.role == role)
    
    # Apply active status filter
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination and ordering
    query = query.order_by(User.created_at.desc()).offset(offset).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    users = result.scalars().all()
    
    return UserListResponse(
        items=users,
        total=total,
        page=(offset // limit) + 1,
        size=limit,
        pages=(total + limit - 1) // limit,
    )


@router.post("/", response_model=UserSchema)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_company_admin),
) -> User:
    """
    Create new user.
    
    Args:
        user_data: User creation data
        db: Database session
        current_user: Current authenticated user (must be company admin)
        
    Returns:
        Created user
        
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
    
    # Set company based on current user's role
    if current_user.role == UserRole.COMPANY_ADMIN:
        company_id = current_user.company_id
        # Company admins can only create regular users
        if user_data.role not in [UserRole.USER, None]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Company admins can only create regular users"
            )
    else:
        # Admins must specify company
        if not user_data.company_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Company ID is required"
            )
        company_id = user_data.company_id
    
    # Create user
    user = User(
        **user_data.model_dump(exclude={"password", "company_id"}),
        password_hash=get_password_hash(user_data.password),
        company_id=company_id,
        role=user_data.role or UserRole.USER,
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # TODO: Send welcome email
    
    return user


@router.get("/{user_id}", response_model=UserWithCompany)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Get user by ID.
    
    Args:
        user_id: User ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        User details with company
        
    Raises:
        HTTPException: If user not found or no access
    """
    # Get user with company
    result = await db.execute(
        select(User)
        .options(selectinload(User.company))
        .where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check access permissions
    if current_user.role == UserRole.USER and user.id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No access to this user"
        )
    elif current_user.role == UserRole.COMPANY_ADMIN and user.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not in your company"
        )
    
    return user


@router.patch("/{user_id}", response_model=UserSchema)
async def update_user(
    user_id: UUID,
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Update user.
    
    Args:
        user_id: User ID
        user_update: User update data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Updated user
        
    Raises:
        HTTPException: If user not found or no access
    """
    # Get user
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check permissions
    if current_user.role == UserRole.USER:
        # Users can only update themselves
        if user.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot update other users"
            )
        # Users cannot change their role or active status
        if user_update.role is not None or user_update.is_active is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot change role or active status"
            )
    elif current_user.role == UserRole.COMPANY_ADMIN:
        # Company admins can only update users in their company
        if user.company_id != current_user.company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User not in your company"
            )
        # Company admins cannot promote users to admin roles
        if user_update.role in [UserRole.ADMIN, UserRole.SUPERUSER]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot assign admin roles"
            )
    
    # Update user fields
    update_data = user_update.model_dump(exclude_unset=True)
    
    # Handle password update
    if "password" in update_data:
        update_data["password_hash"] = get_password_hash(update_data.pop("password"))
    
    # Update user
    for field, value in update_data.items():
        setattr(user, field, value)
    
    await db.commit()
    await db.refresh(user)
    
    return user


@router.delete("/{user_id}")
async def delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict:
    """
    Delete user (soft delete).
    
    Args:
        user_id: User ID
        db: Database session
        current_user: Current authenticated user (must be admin)
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If user not found
    """
    # Get user
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent deleting superusers
    if user.role == UserRole.SUPERUSER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete superuser accounts"
        )
    
    # Soft delete (deactivate)
    user.is_active = False
    await db.commit()
    
    return {"message": "User deactivated successfully"}


@router.post("/{user_id}/activate")
async def activate_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_company_admin),
) -> dict:
    """
    Activate user.
    
    Args:
        user_id: User ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If user not found or no access
    """
    # Get user
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check permissions
    if current_user.role == UserRole.COMPANY_ADMIN and user.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not in your company"
        )
    
    # Activate user
    user.is_active = True
    await db.commit()
    
    return {"message": "User activated successfully"}


@router.post("/{user_id}/deactivate")
async def deactivate_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_company_admin),
) -> dict:
    """
    Deactivate user.
    
    Args:
        user_id: User ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If user not found or no access
    """
    # Get user
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check permissions
    if current_user.role == UserRole.COMPANY_ADMIN and user.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not in your company"
        )
    
    # Prevent deactivating self
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate yourself"
        )
    
    # Deactivate user
    user.is_active = False
    await db.commit()
    
    return {"message": "User deactivated successfully"}