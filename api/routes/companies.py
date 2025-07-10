"""Company management endpoints."""

from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from api.dependencies import (
    get_current_active_user,
    require_admin,
    require_company_admin,
    get_pagination_params,
)
from db.session import get_db
from models.company import Company
from models.user import User
from schemas.company import CompanyCreate, CompanyUpdate, CompanyResponse
from schemas.user import UserResponse

router = APIRouter()


@router.get("/", response_model=List[CompanyResponse])
async def get_companies(
    db: AsyncSession = Depends(get_db),
    pagination: tuple[int, int] = Depends(get_pagination_params),
    current_user: User = Depends(require_admin),
) -> Any:
    """
    Get all companies (admin only).
    
    Args:
        db: Database session
        pagination: Skip and limit values
        current_user: Current admin user
        
    Returns:
        List of companies
    """
    skip, limit = pagination
    
    result = await db.execute(
        select(Company)
        .offset(skip)
        .limit(limit)
        .order_by(Company.created_at.desc())
    )
    companies = result.scalars().all()
    
    return companies


@router.get("/count", response_model=dict)
async def get_companies_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Any:
    """
    Get total company count (admin only).
    
    Args:
        db: Database session
        current_user: Current admin user
        
    Returns:
        Total company count
    """
    result = await db.execute(select(func.count(Company.id)))
    count = result.scalar()
    
    return {"count": count}


@router.get("/my", response_model=CompanyResponse)
async def get_my_company(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get current user's company.
    
    Args:
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Company information
        
    Raises:
        HTTPException: If user has no company
    """
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not associated with any company",
        )
    
    result = await db.execute(
        select(Company).where(Company.id == current_user.company_id)
    )
    company = result.scalar_one_or_none()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )
    
    return company


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get a specific company.
    
    Args:
        company_id: Company ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Company information
        
    Raises:
        HTTPException: If company not found or unauthorized
    """
    # Users can only view their own company unless they're admin
    if company_id != current_user.company_id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this company",
        )
    
    result = await db.execute(
        select(Company).where(Company.id == company_id)
    )
    company = result.scalar_one_or_none()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )
    
    return company


@router.post("/", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
async def create_company(
    company_data: CompanyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Any:
    """
    Create a new company (admin only).
    
    Args:
        company_data: Company creation data
        db: Database session
        current_user: Current admin user
        
    Returns:
        Created company
        
    Raises:
        HTTPException: If company name already exists
    """
    # Check if company already exists
    result = await db.execute(
        select(Company).where(Company.name == company_data.name)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Company with this name already exists",
        )
    
    # Check domain uniqueness if provided
    if company_data.domain:
        result = await db.execute(
            select(Company).where(Company.domain == company_data.domain)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Company with this domain already exists",
            )
    
    # Create new company
    company = Company(**company_data.model_dump())
    
    db.add(company)
    await db.commit()
    await db.refresh(company)
    
    return company


@router.patch("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: int,
    company_update: CompanyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_company_admin),
) -> Any:
    """
    Update a company.
    
    Args:
        company_id: Company ID
        company_update: Company update data
        db: Database session
        current_user: Current authenticated user (must be company admin)
        
    Returns:
        Updated company
        
    Raises:
        HTTPException: If company not found or unauthorized
    """
    # Company admins can only update their own company
    if not current_user.is_admin and company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this company",
        )
    
    # Get company
    result = await db.execute(
        select(Company).where(Company.id == company_id)
    )
    company = result.scalar_one_or_none()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )
    
    # Only platform admins can change subscription plans
    if company_update.subscription_plan and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only platform admins can change subscription plans",
        )
    
    # Update company fields
    update_data = company_update.model_dump(exclude_unset=True)
    
    # Check if name is being changed and if it's already taken
    if "name" in update_data and update_data["name"] != company.name:
        result = await db.execute(
            select(Company).where(Company.name == update_data["name"])
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Company with this name already exists",
            )
    
    # Check domain uniqueness if being changed
    if "domain" in update_data and update_data["domain"] != company.domain:
        result = await db.execute(
            select(Company).where(Company.domain == update_data["domain"])
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Company with this domain already exists",
            )
    
    # Apply updates
    for field, value in update_data.items():
        setattr(company, field, value)
    
    await db.commit()
    await db.refresh(company)
    
    return company


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(
    company_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> None:
    """
    Delete a company (admin only).
    
    Args:
        company_id: Company ID
        db: Database session
        current_user: Current admin user
        
    Raises:
        HTTPException: If company not found or has users
    """
    # Get company
    result = await db.execute(
        select(Company).where(Company.id == company_id)
    )
    company = result.scalar_one_or_none()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )
    
    # Check if company has users
    result = await db.execute(
        select(func.count(User.id)).where(User.company_id == company_id)
    )
    user_count = result.scalar()
    
    if user_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete company with {user_count} active users",
        )
    
    # Delete company
    await db.delete(company)
    await db.commit()


@router.get("/{company_id}/users", response_model=List[UserResponse])
async def get_company_users(
    company_id: int,
    db: AsyncSession = Depends(get_db),
    pagination: tuple[int, int] = Depends(get_pagination_params),
    current_user: User = Depends(require_company_admin),
) -> Any:
    """
    Get all users in a company.
    
    Args:
        company_id: Company ID
        db: Database session
        pagination: Skip and limit values
        current_user: Current authenticated user (must be company admin)
        
    Returns:
        List of users in the company
        
    Raises:
        HTTPException: If unauthorized
    """
    # Company admins can only view their own company users
    if not current_user.is_admin and company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view users from this company",
        )
    
    skip, limit = pagination
    
    result = await db.execute(
        select(User)
        .where(User.company_id == company_id)
        .offset(skip)
        .limit(limit)
        .order_by(User.created_at.desc())
    )
    users = result.scalars().all()
    
    return users