"""Company management routes."""

from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, or_
from sqlalchemy.orm import selectinload

from api.dependencies.auth import require_admin, get_current_active_user
from api.dependencies.common import get_db, get_pagination_params
from models.company import Company, SubscriptionTier
from models.user import User
from schemas.company import (
    CompanyRegistration,
    Company as CompanySchema,
    CompanyListResponse,
    CompanyStats,
)
from schemas.user import User as UserSchema

router = APIRouter()


@router.get("/", response_model=CompanyListResponse)
async def list_companies(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
    pagination: tuple[int, int] = Depends(get_pagination_params),
    search: Optional[str] = Query(None, description="Search in company name"),
    tier: Optional[str] = Query(None, description="Filter by subscription tier"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
) -> CompanyListResponse:
    """
    List all companies (admin only).
    
    Args:
        db: Database session
        current_user: Current authenticated user (must be admin)
        pagination: Offset and limit
        search: Search term
        tier: Filter by subscription tier
        is_active: Filter by active status
        
    Returns:
        Paginated list of companies
    """
    offset, limit = pagination
    
    # Base query
    query = select(Company)
    
    # Apply search filter
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Company.name.ilike(search_term),
                Company.domain.ilike(search_term),
            )
        )
    
    # Apply tier filter
    if tier:
        query = query.where(Company.subscription_tier == tier)
    
    # Apply active status filter
    if is_active is not None:
        query = query.where(Company.is_active == is_active)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination and ordering
    query = query.order_by(Company.created_at.desc()).offset(offset).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    companies = result.scalars().all()
    
    return CompanyListResponse(
        items=companies,
        total=total,
        page=(offset // limit) + 1,
        size=limit,
        pages=(total + limit - 1) // limit,
    )


@router.post("/", response_model=CompanySchema)
async def create_company(
    company_data: CompanyRegistration,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Company:
    """
    Create new company (admin only).
    
    Args:
        company_data: Company creation data
        db: Database session
        current_user: Current authenticated user (must be admin)
        
    Returns:
        Created company
        
    Raises:
        HTTPException: If company name or domain already exists
    """
    # Check if company name already exists
    result = await db.execute(
        select(Company).where(Company.name == company_data.name)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Company name already exists"
        )
    
    # Check if domain already exists
    if company_data.domain:
        result = await db.execute(
            select(Company).where(Company.domain == company_data.domain)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Domain already registered"
            )
    
    # Create company
    company = Company(**company_data.model_dump())
    db.add(company)
    await db.commit()
    await db.refresh(company)
    
    return company


@router.get("/{company_id}", response_model=CompanySchema)
async def get_company(
    company_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> CompanySchema:
    """
    Get company by ID.
    
    Args:
        company_id: Company ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Company details with statistics
        
    Raises:
        HTTPException: If company not found or no access
    """
    # Get company
    result = await db.execute(
        select(Company).where(Company.id == company_id)
    )
    company = result.scalar_one_or_none()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    # Check access permissions
    if current_user.role == "user" and current_user.company_id != company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No access to this company"
        )
    
    # Get user count
    user_count_result = await db.execute(
        select(func.count(User.id)).where(
            User.company_id == company_id,
            User.is_active == True
        )
    )
    user_count = user_count_result.scalar()
    
    # Get admin count
    admin_count_result = await db.execute(
        select(func.count(User.id)).where(
            User.company_id == company_id,
            User.role == "company_admin",
            User.is_active == True
        )
    )
    admin_count = admin_count_result.scalar()
    
    # Create response with stats
    return CompanySchema(
        **company.__dict__,
        user_count=user_count,
        admin_count=admin_count,
        # TODO: Add more statistics like course enrollments, completion rates, etc.
    )


@router.patch("/{company_id}", response_model=CompanySchema)
async def update_company(
    company_id: UUID,
    company_update: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Company:
    """
    Update company (admin only).
    
    Args:
        company_id: Company ID
        company_update: Company update data
        db: Database session
        current_user: Current authenticated user (must be admin)
        
    Returns:
        Updated company
        
    Raises:
        HTTPException: If company not found
    """
    # Get company
    result = await db.execute(
        select(Company).where(Company.id == company_id)
    )
    company = result.scalar_one_or_none()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    # Check if new name already exists
    if company_update.name and company_update.name != company.name:
        result = await db.execute(
            select(Company).where(Company.name == company_update.name)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Company name already exists"
            )
    
    # Check if new domain already exists
    if company_update.domain and company_update.domain != company.domain:
        result = await db.execute(
            select(Company).where(Company.domain == company_update.domain)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Domain already registered"
            )
    
    # Update company fields
    update_data = company_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(company, field, value)
    
    await db.commit()
    await db.refresh(company)
    
    return company


@router.delete("/{company_id}")
async def delete_company(
    company_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict:
    """
    Delete company (soft delete, admin only).
    
    Args:
        company_id: Company ID
        db: Database session
        current_user: Current authenticated user (must be admin)
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If company not found
    """
    # Get company
    result = await db.execute(
        select(Company).where(Company.id == company_id)
    )
    company = result.scalar_one_or_none()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    # Check if company has active users
    user_count_result = await db.execute(
        select(func.count(User.id)).where(
            User.company_id == company_id,
            User.is_active == True
        )
    )
    if user_count_result.scalar() > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete company with active users"
        )
    
    # Soft delete (deactivate)
    company.is_active = False
    await db.commit()
    
    return {"message": "Company deactivated successfully"}


@router.post("/{company_id}/activate")
async def activate_company(
    company_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict:
    """
    Activate company (admin only).
    
    Args:
        company_id: Company ID
        db: Database session
        current_user: Current authenticated user (must be admin)
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If company not found
    """
    # Get company
    result = await db.execute(
        select(Company).where(Company.id == company_id)
    )
    company = result.scalar_one_or_none()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    # Activate company
    company.is_active = True
    await db.commit()
    
    return {"message": "Company activated successfully"}


@router.get("/{company_id}/users", response_model=List[UserSchema])
async def get_company_users(
    company_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
) -> List[UserSchema]:
    """
    Get users of a company.
    
    Args:
        company_id: Company ID
        db: Database session
        current_user: Current authenticated user
        is_active: Filter by active status
        
    Returns:
        List of company users
        
    Raises:
        HTTPException: If no access to company
    """
    # Check access permissions
    if current_user.role == "user" and current_user.company_id != company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No access to this company"
        )
    elif current_user.role == "company_admin" and current_user.company_id != company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only view users from your company"
        )
    
    # Get users
    query = select(User).where(User.company_id == company_id)
    
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    
    query = query.order_by(User.created_at.desc())
    
    result = await db.execute(query)
    users = result.scalars().all()
    
    return users