"""Phishing simulation routes - simplified implementation."""

from typing import Optional, List
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, or_, and_
from sqlalchemy.orm import selectinload

from api.dependencies.auth import get_current_active_user, require_company_admin
from api.dependencies.common import get_db, get_pagination_params
from models.phishing import (
    PhishingCampaign,
    PhishingTemplate,
    PhishingResult,
)
from models.user import User, UserRole
from schemas.base import PaginatedResponse

router = APIRouter()


@router.get("/campaigns", response_model=PaginatedResponse)
async def list_campaigns(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    pagination: tuple[int, int] = Depends(get_pagination_params),
    status: Optional[str] = Query(None, description="Filter by status", regex="^(draft|scheduled|running|completed|cancelled)$"),
    search: Optional[str] = Query(None, description="Search in campaign name"),
) -> PaginatedResponse:
    """
    List phishing campaigns.
    
    Args:
        db: Database session
        current_user: Current authenticated user
        pagination: Offset and limit
        status: Filter by campaign status
        search: Search term
        
    Returns:
        Paginated list of campaigns
    """
    offset, limit = pagination
    
    # Base query
    query = select(PhishingCampaign).where(
        PhishingCampaign.company_id == current_user.company_id
    )
    
    # Apply filters
    if status:
        query = query.where(PhishingCampaign.status == status)
    
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                PhishingCampaign.name.ilike(search_term),
                PhishingCampaign.description.ilike(search_term),
            )
        )
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination and ordering
    query = query.order_by(PhishingCampaign.created_at.desc()).offset(offset).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    campaigns = result.scalars().all()
    
    return PaginatedResponse(
        items=[{
            "id": str(c.id),
            "name": c.name,
            "status": c.status,
            "created_at": c.created_at.isoformat(),
            "scheduled_at": c.scheduled_at.isoformat() if c.scheduled_at else None,
            "statistics": c.get_statistics(),
        } for c in campaigns],
        total=total,
        page=(offset // limit) + 1,
        size=limit,
        pages=(total + limit - 1) // limit,
    )


@router.post("/campaigns", response_model=dict)
async def create_campaign(
    campaign_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_company_admin),
) -> dict:
    """
    Create new phishing campaign.
    
    Args:
        campaign_data: Campaign creation data
        db: Database session
        current_user: Current authenticated user (must be admin)
        
    Returns:
        Created campaign
    """
    # Create campaign
    campaign = PhishingCampaign(
        company_id=current_user.company_id,
        created_by_id=current_user.id,
        name=campaign_data.get("name", "New Campaign"),
        description=campaign_data.get("description"),
        status="draft",
        template_id=campaign_data.get("template_id"),
        target_groups=campaign_data.get("target_groups", []),
        target_user_ids=campaign_data.get("target_user_ids", []),
        settings=campaign_data.get("settings", {}),
    )
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)
    
    return {
        "id": str(campaign.id),
        "name": campaign.name,
        "status": campaign.status,
        "created_at": campaign.created_at.isoformat(),
    }


@router.get("/campaigns/{campaign_id}", response_model=dict)
async def get_campaign(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Get campaign details.
    
    Args:
        campaign_id: Campaign ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Campaign details
        
    Raises:
        HTTPException: If campaign not found or no access
    """
    # Get campaign
    result = await db.execute(
        select(PhishingCampaign)
        .options(selectinload(PhishingCampaign.results))
        .where(
            and_(
                PhishingCampaign.id == campaign_id,
                PhishingCampaign.company_id == current_user.company_id,
            )
        )
    )
    campaign = result.scalar_one_or_none()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    return {
        "id": str(campaign.id),
        "name": campaign.name,
        "description": campaign.description,
        "status": campaign.status,
        "created_at": campaign.created_at.isoformat(),
        "scheduled_at": campaign.scheduled_at.isoformat() if campaign.scheduled_at else None,
        "started_at": campaign.started_at.isoformat() if campaign.started_at else None,
        "completed_at": campaign.completed_at.isoformat() if campaign.completed_at else None,
        "statistics": campaign.get_statistics(),
        "template_id": str(campaign.template_id) if campaign.template_id else None,
        "target_groups": campaign.target_groups,
        "target_user_ids": campaign.target_user_ids,
    }


@router.patch("/campaigns/{campaign_id}", response_model=dict)
async def update_campaign(
    campaign_id: UUID,
    campaign_update: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_company_admin),
) -> dict:
    """
    Update phishing campaign.
    
    Args:
        campaign_id: Campaign ID
        campaign_update: Campaign update data
        db: Database session
        current_user: Current authenticated user (must be admin)
        
    Returns:
        Updated campaign
        
    Raises:
        HTTPException: If campaign not found or not in draft status
    """
    # Get campaign
    result = await db.execute(
        select(PhishingCampaign).where(
            and_(
                PhishingCampaign.id == campaign_id,
                PhishingCampaign.company_id == current_user.company_id,
            )
        )
    )
    campaign = result.scalar_one_or_none()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    if campaign.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only update campaigns in draft status"
        )
    
    # Update fields
    for field, value in campaign_update.items():
        if hasattr(campaign, field):
            setattr(campaign, field, value)
    
    await db.commit()
    await db.refresh(campaign)
    
    return {
        "id": str(campaign.id),
        "name": campaign.name,
        "status": campaign.status,
        "updated_at": campaign.updated_at.isoformat(),
    }


@router.post("/campaigns/{campaign_id}/launch", response_model=dict)
async def launch_campaign(
    campaign_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_company_admin),
) -> dict:
    """
    Launch phishing campaign.
    
    Args:
        campaign_id: Campaign ID
        background_tasks: Background task manager
        db: Database session
        current_user: Current authenticated user (must be admin)
        
    Returns:
        Launch confirmation
        
    Raises:
        HTTPException: If campaign not found or not in draft status
    """
    # Get campaign
    result = await db.execute(
        select(PhishingCampaign).where(
            and_(
                PhishingCampaign.id == campaign_id,
                PhishingCampaign.company_id == current_user.company_id,
            )
        )
    )
    campaign = result.scalar_one_or_none()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    if campaign.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Campaign has already been launched"
        )
    
    # Update campaign status
    campaign.status = "scheduled"
    campaign.scheduled_at = datetime.utcnow()
    await db.commit()
    
    # TODO: Add background task to send phishing emails
    
    return {
        "message": "Campaign launched successfully",
        "campaign_id": str(campaign_id),
        "status": campaign.status,
        "scheduled_at": campaign.scheduled_at.isoformat(),
    }


@router.get("/templates", response_model=List[dict])
async def list_templates(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    category: Optional[str] = Query(None, description="Filter by category"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty"),
) -> List[dict]:
    """
    List phishing templates.
    
    Args:
        db: Database session
        current_user: Current authenticated user
        category: Filter by category
        difficulty: Filter by difficulty (easy, medium, hard)
        
    Returns:
        List of templates
    """
    # Base query - show system templates and company templates
    query = select(PhishingTemplate).where(
        or_(
            PhishingTemplate.company_id.is_(None),  # System templates
            PhishingTemplate.company_id == current_user.company_id,  # Company templates
        )
    )
    
    # Apply filters
    if category:
        query = query.where(PhishingTemplate.category == category)
    
    if difficulty:
        query = query.where(PhishingTemplate.difficulty == difficulty)
    
    # Execute query
    result = await db.execute(query.order_by(PhishingTemplate.name))
    templates = result.scalars().all()
    
    return [{
        "id": str(t.id),
        "name": t.name,
        "category": t.category,
        "difficulty": t.difficulty,
        "is_system": t.company_id is None,
    } for t in templates]


@router.get("/track/{tracking_id}/click")
async def track_click(
    tracking_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Track link click in phishing email.
    
    Args:
        tracking_id: Tracking ID
        db: Database session
        
    Returns:
        Redirect URL or success message
    """
    # Find phishing result by ID (using tracking_id as result ID)
    try:
        result_id = int(tracking_id)
        result = await db.execute(
            select(PhishingResult).where(
                PhishingResult.id == result_id
            )
        )
        phishing_result = result.scalar_one_or_none()
        
        if not phishing_result:
            # Don't reveal that the tracking ID is invalid
            return {"redirect": "https://example.com"}
        
        # Update click timestamp if not already clicked
        if not phishing_result.link_clicked_at:
            phishing_result.link_clicked_at = datetime.utcnow()
            await db.commit()
        
        # TODO: Get redirect URL from campaign settings
        return {"redirect": "https://example.com"}
        
    except (ValueError, TypeError):
        # Invalid tracking ID format
        return {"redirect": "https://example.com"}


@router.post("/report/{tracking_id}")
async def report_phishing(
    tracking_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Report suspected phishing email.
    
    Args:
        tracking_id: Tracking ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Success message
    """
    # Find phishing result by ID
    try:
        result_id = int(tracking_id)
        result = await db.execute(
            select(PhishingResult).where(
                and_(
                    PhishingResult.id == result_id,
                    PhishingResult.user_id == current_user.id,
                )
            )
        )
        phishing_result = result.scalar_one_or_none()
        
        if phishing_result and not phishing_result.reported_at:
            phishing_result.reported_at = datetime.utcnow()
            await db.commit()
        
        return {"message": "Thank you for reporting this suspicious email!"}
        
    except (ValueError, TypeError):
        return {"message": "Thank you for reporting this suspicious email!"}