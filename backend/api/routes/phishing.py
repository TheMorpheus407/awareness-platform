"""Phishing simulation routes."""

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
    PhishingEmail,
    PhishingResult,
    CampaignStatus,
)
from models.user import User, UserRole
from schemas.phishing import (
    PhishingCampaignCreate,
    PhishingCampaignUpdate,
    PhishingCampaign as PhishingCampaignSchema,
    PhishingCampaignListResponse,
    PhishingTemplateCreate,
    PhishingTemplate as PhishingTemplateSchema,
    PhishingResultCreate,
    PhishingResult as PhishingResultSchema,
    CampaignStatistics,
)
from services.phishing_service import PhishingService

router = APIRouter()


@router.get("/campaigns", response_model=PhishingCampaignListResponse)
async def list_campaigns(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_company_admin),
    pagination: tuple[int, int] = Depends(get_pagination_params),
    status: Optional[CampaignStatus] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search in campaign name"),
) -> PhishingCampaignListResponse:
    """
    List phishing campaigns for company.
    
    Args:
        db: Database session
        current_user: Current authenticated user (must be company admin)
        pagination: Offset and limit
        status: Filter by campaign status
        search: Search term
        
    Returns:
        Paginated list of phishing campaigns
    """
    offset, limit = pagination
    
    # Base query - filter by company
    query = select(PhishingCampaign).where(
        PhishingCampaign.company_id == current_user.company_id
    )
    
    # Apply status filter
    if status:
        query = query.where(PhishingCampaign.status == status)
    
    # Apply search filter
    if search:
        search_term = f"%{search}%"
        query = query.where(PhishingCampaign.name.ilike(search_term))
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination and ordering
    query = query.order_by(PhishingCampaign.created_at.desc()).offset(offset).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    campaigns = result.scalars().all()
    
    return PhishingCampaignListResponse(
        items=campaigns,
        total=total,
        page=(offset // limit) + 1,
        size=limit,
        pages=(total + limit - 1) // limit,
    )


@router.post("/campaigns", response_model=PhishingCampaignSchema)
async def create_campaign(
    campaign_data: PhishingCampaignCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_company_admin),
) -> PhishingCampaign:
    """
    Create new phishing campaign.
    
    Args:
        campaign_data: Campaign creation data
        background_tasks: Background task queue
        db: Database session
        current_user: Current authenticated user (must be company admin)
        
    Returns:
        Created phishing campaign
    """
    # Verify template exists
    template_result = await db.execute(
        select(PhishingTemplate).where(
            PhishingTemplate.id == campaign_data.template_id
        )
    )
    template = template_result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    # Create campaign
    campaign = PhishingCampaign(
        **campaign_data.model_dump(exclude={"target_users"}),
        company_id=current_user.company_id,
        created_by=current_user.id,
        status=CampaignStatus.DRAFT,
    )
    db.add(campaign)
    await db.flush()  # Get campaign ID
    
    # Create phishing emails for target users
    phishing_service = PhishingService(db)
    await phishing_service.create_campaign_emails(
        campaign_id=campaign.id,
        template_id=campaign_data.template_id,
        target_user_ids=campaign_data.target_users,
    )
    
    await db.commit()
    await db.refresh(campaign)
    
    # Schedule campaign if needed
    if campaign_data.scheduled_at:
        background_tasks.add_task(
            phishing_service.schedule_campaign,
            campaign_id=campaign.id,
            scheduled_at=campaign_data.scheduled_at,
        )
    
    return campaign


@router.get("/campaigns/{campaign_id}", response_model=PhishingCampaignSchema)
async def get_campaign(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_company_admin),
) -> PhishingCampaign:
    """
    Get phishing campaign by ID.
    
    Args:
        campaign_id: Campaign ID
        db: Database session
        current_user: Current authenticated user (must be company admin)
        
    Returns:
        Phishing campaign details
        
    Raises:
        HTTPException: If campaign not found or no access
    """
    # Get campaign
    result = await db.execute(
        select(PhishingCampaign)
        .options(selectinload(PhishingCampaign.template))
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
    
    return campaign


@router.post("/campaigns/{campaign_id}/launch")
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
        background_tasks: Background task queue
        db: Database session
        current_user: Current authenticated user (must be company admin)
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If campaign not found or cannot be launched
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
    
    if campaign.status != CampaignStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Campaign can only be launched from draft status"
        )
    
    # Update campaign status
    campaign.status = CampaignStatus.SCHEDULED
    campaign.scheduled_at = datetime.utcnow()
    await db.commit()
    
    # Launch campaign in background
    phishing_service = PhishingService(db)
    background_tasks.add_task(
        phishing_service.launch_campaign,
        campaign_id=campaign.id,
    )
    
    return {"message": "Campaign launched successfully"}


@router.get("/campaigns/{campaign_id}/statistics", response_model=CampaignStatistics)
async def get_campaign_statistics(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_company_admin),
) -> CampaignStatistics:
    """
    Get campaign statistics.
    
    Args:
        campaign_id: Campaign ID
        db: Database session
        current_user: Current authenticated user (must be company admin)
        
    Returns:
        Campaign statistics
        
    Raises:
        HTTPException: If campaign not found or no access
    """
    # Verify campaign exists and user has access
    campaign_result = await db.execute(
        select(PhishingCampaign).where(
            and_(
                PhishingCampaign.id == campaign_id,
                PhishingCampaign.company_id == current_user.company_id,
            )
        )
    )
    campaign = campaign_result.scalar_one_or_none()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    # Get statistics
    phishing_service = PhishingService(db)
    stats = await phishing_service.get_campaign_statistics(campaign_id)
    
    return stats


@router.get("/templates", response_model=List[PhishingTemplateSchema])
async def list_templates(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_company_admin),
    is_custom: Optional[bool] = Query(None, description="Filter by custom templates"),
) -> List[PhishingTemplate]:
    """
    List available phishing templates.
    
    Args:
        db: Database session
        current_user: Current authenticated user (must be company admin)
        is_custom: Filter by custom templates
        
    Returns:
        List of phishing templates
    """
    # Base query - show system templates and company's custom templates
    query = select(PhishingTemplate).where(
        or_(
            PhishingTemplate.is_system == True,
            PhishingTemplate.company_id == current_user.company_id,
        )
    )
    
    # Apply custom filter
    if is_custom is not None:
        if is_custom:
            query = query.where(PhishingTemplate.company_id == current_user.company_id)
        else:
            query = query.where(PhishingTemplate.is_system == True)
    
    # Order by name
    query = query.order_by(PhishingTemplate.name)
    
    # Execute query
    result = await db.execute(query)
    templates = result.scalars().all()
    
    return templates


@router.post("/results/{tracking_id}/click")
async def track_click(
    tracking_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Track phishing email click (public endpoint).
    
    Args:
        tracking_id: Unique tracking ID from email
        db: Database session
        
    Returns:
        Redirect URL or success message
    """
    # Find phishing email by tracking ID
    result = await db.execute(
        select(PhishingEmail).where(
            PhishingEmail.tracking_id == tracking_id
        )
    )
    email = result.scalar_one_or_none()
    
    if not email:
        # Don't reveal that the tracking ID is invalid
        return {"redirect": "https://example.com"}
    
    # Update email status if not already clicked
    if not email.clicked_at:
        email.clicked_at = datetime.utcnow()
        
        # Create result record
        result = PhishingResult(
            campaign_id=email.campaign_id,
            user_id=email.user_id,
            email_id=email.id,
            action="clicked",
            timestamp=datetime.utcnow(),
        )
        db.add(result)
        await db.commit()
    
    # Get template for redirect URL
    template_result = await db.execute(
        select(PhishingTemplate)
        .join(PhishingCampaign)
        .where(PhishingCampaign.id == email.campaign_id)
    )
    template = template_result.scalar_one_or_none()
    
    return {
        "redirect": template.landing_page_url if template else "https://example.com"
    }


@router.post("/results/{tracking_id}/report")
async def report_phishing(
    tracking_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Report phishing email (public endpoint).
    
    Args:
        tracking_id: Unique tracking ID from email
        db: Database session
        
    Returns:
        Success message
    """
    # Find phishing email by tracking ID
    result = await db.execute(
        select(PhishingEmail).where(
            PhishingEmail.tracking_id == tracking_id
        )
    )
    email = result.scalar_one_or_none()
    
    if not email:
        # Don't reveal that the tracking ID is invalid
        return {"message": "Thank you for reporting this email"}
    
    # Update email status if not already reported
    if not email.reported_at:
        email.reported_at = datetime.utcnow()
        
        # Create result record
        result = PhishingResult(
            campaign_id=email.campaign_id,
            user_id=email.user_id,
            email_id=email.id,
            action="reported",
            timestamp=datetime.utcnow(),
        )
        db.add(result)
        await db.commit()
    
    return {"message": "Thank you for reporting this phishing email"}