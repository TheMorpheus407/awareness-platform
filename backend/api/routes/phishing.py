"""Phishing simulation routes - complete implementation with all features."""

import asyncio
from typing import Optional, List
from uuid import UUID
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks, WebSocket
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
from schemas.phishing import (
    PhishingTemplateCreate,
    PhishingTemplateUpdate,
    PhishingTemplateResponse,
    CampaignAnalytics,
    EmailTrackingEvent,
)
from services.phishing_service import PhishingService

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
    from services.phishing_service import PhishingService
    
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
    
    # Add background task to send phishing emails
    phishing_service = PhishingService(db)
    background_tasks.add_task(
        phishing_service.send_phishing_campaign,
        campaign_id
    )
    
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


@router.post("/templates", response_model=PhishingTemplateResponse)
async def create_template(
    template_data: PhishingTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_company_admin),
) -> PhishingTemplateResponse:
    """
    Create custom phishing template.
    
    Args:
        template_data: Template creation data
        db: Database session
        current_user: Current authenticated user (must be admin)
        
    Returns:
        Created template
    """
    # Create template
    template = PhishingTemplate(
        company_id=current_user.company_id,
        name=template_data.name,
        category=template_data.category,
        difficulty=template_data.difficulty,
        subject=template_data.subject,
        sender_name=template_data.sender_name,
        sender_email=template_data.sender_email,
        html_content=template_data.html_content,
        text_content=template_data.text_content,
        landing_page_html=template_data.landing_page_html,
        language=template_data.language,
        is_public=False,  # Company templates are private by default
    )
    db.add(template)
    await db.commit()
    await db.refresh(template)
    
    return PhishingTemplateResponse.from_orm(template)


@router.get("/templates/{template_id}", response_model=PhishingTemplateResponse)
async def get_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PhishingTemplateResponse:
    """
    Get template details.
    
    Args:
        template_id: Template ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Template details
        
    Raises:
        HTTPException: If template not found or no access
    """
    # Get template
    result = await db.execute(
        select(PhishingTemplate).where(
            and_(
                PhishingTemplate.id == template_id,
                or_(
                    PhishingTemplate.company_id.is_(None),  # System template
                    PhishingTemplate.company_id == current_user.company_id,  # Company template
                )
            )
        )
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    return PhishingTemplateResponse.from_orm(template)


@router.patch("/templates/{template_id}", response_model=PhishingTemplateResponse)
async def update_template(
    template_id: UUID,
    template_update: PhishingTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_company_admin),
) -> PhishingTemplateResponse:
    """
    Update phishing template.
    
    Args:
        template_id: Template ID
        template_update: Template update data
        db: Database session
        current_user: Current authenticated user (must be admin)
        
    Returns:
        Updated template
        
    Raises:
        HTTPException: If template not found or is system template
    """
    # Get template
    result = await db.execute(
        select(PhishingTemplate).where(
            and_(
                PhishingTemplate.id == template_id,
                PhishingTemplate.company_id == current_user.company_id,  # Only company templates can be edited
            )
        )
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found or cannot be edited"
        )
    
    # Update fields
    for field, value in template_update.dict(exclude_unset=True).items():
        setattr(template, field, value)
    
    await db.commit()
    await db.refresh(template)
    
    return PhishingTemplateResponse.from_orm(template)


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_company_admin),
) -> None:
    """
    Delete custom phishing template.
    
    Args:
        template_id: Template ID
        db: Database session
        current_user: Current authenticated user (must be admin)
        
    Raises:
        HTTPException: If template not found, is system template, or is in use
    """
    # Get template
    result = await db.execute(
        select(PhishingTemplate).where(
            and_(
                PhishingTemplate.id == template_id,
                PhishingTemplate.company_id == current_user.company_id,
            )
        )
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found or cannot be deleted"
        )
    
    # Check if template is in use
    campaign_count = await db.execute(
        select(func.count()).select_from(PhishingCampaign).where(
            PhishingCampaign.template_id == template_id
        )
    )
    if campaign_count.scalar() > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete template that is used in campaigns"
        )
    
    await db.delete(template)
    await db.commit()


@router.get("/track/{tracking_id}/open")
async def track_email_open(
    tracking_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Track email open event.
    
    Args:
        tracking_id: Tracking ID
        db: Database session
        
    Returns:
        1x1 transparent pixel
    """
    # Find phishing result by ID
    try:
        result_id = int(tracking_id)
        result = await db.execute(
            select(PhishingResult).where(
                PhishingResult.id == result_id
            )
        )
        phishing_result = result.scalar_one_or_none()
        
        if phishing_result and not phishing_result.email_opened_at:
            phishing_result.email_opened_at = datetime.utcnow()
            await db.commit()
        
        # Return 1x1 transparent pixel
        return {
            "content_type": "image/gif",
            "data": "R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
        }
        
    except (ValueError, TypeError):
        # Invalid tracking ID format - still return pixel
        return {
            "content_type": "image/gif",
            "data": "R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
        }


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


@router.get("/campaigns/{campaign_id}/analytics", response_model=CampaignAnalytics)
async def get_campaign_analytics(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> CampaignAnalytics:
    """
    Get real-time campaign analytics.
    
    Args:
        campaign_id: Campaign ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Campaign analytics
        
    Raises:
        HTTPException: If campaign not found or no access
    """
    # Get campaign with results
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
    
    # Calculate analytics
    phishing_service = PhishingService(db)
    analytics_data = await phishing_service.get_campaign_analytics(campaign_id)
    
    return CampaignAnalytics(**analytics_data)


@router.get("/campaigns/{campaign_id}/landing-page")
async def get_landing_page(
    campaign_id: UUID,
    tracking_id: Optional[str] = Query(None, description="User tracking ID"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get landing page for phishing campaign.
    
    Args:
        campaign_id: Campaign ID
        tracking_id: Optional tracking ID for personalization
        db: Database session
        
    Returns:
        Landing page HTML
    """
    # Get campaign with template
    result = await db.execute(
        select(PhishingCampaign)
        .options(selectinload(PhishingCampaign.template))
        .where(PhishingCampaign.id == campaign_id)
    )
    campaign = result.scalar_one_or_none()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    # Get user info if tracking ID provided
    user_info = None
    if tracking_id:
        try:
            result_id = int(tracking_id)
            result = await db.execute(
                select(PhishingResult)
                .options(selectinload(PhishingResult.user))
                .where(PhishingResult.id == result_id)
            )
            phishing_result = result.scalar_one_or_none()
            if phishing_result:
                user_info = {
                    "first_name": phishing_result.user.first_name,
                    "last_name": phishing_result.user.last_name,
                    "email": phishing_result.user.email,
                }
                # Update data submitted timestamp
                if not phishing_result.data_submitted_at:
                    phishing_result.data_submitted_at = datetime.utcnow()
                    await db.commit()
        except (ValueError, TypeError):
            pass
    
    # Generate landing page
    phishing_service = PhishingService(db)
    landing_page_html = await phishing_service.generate_landing_page(
        campaign=campaign,
        user_info=user_info
    )
    
    return {
        "html": landing_page_html,
        "campaign_name": campaign.name,
    }


@router.post("/campaigns/{campaign_id}/schedule")
async def schedule_campaign(
    campaign_id: UUID,
    schedule_data: dict,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_company_admin),
) -> dict:
    """
    Schedule phishing campaign for future launch.
    
    Args:
        campaign_id: Campaign ID
        schedule_data: Scheduling data (scheduled_at, batch_size, interval_minutes)
        background_tasks: Background task manager
        db: Database session
        current_user: Current authenticated user (must be admin)
        
    Returns:
        Schedule confirmation
        
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
    
    # Parse schedule data
    scheduled_at = datetime.fromisoformat(schedule_data.get("scheduled_at", datetime.utcnow().isoformat()))
    batch_size = schedule_data.get("batch_size", 50)
    interval_minutes = schedule_data.get("interval_minutes", 5)
    
    if scheduled_at <= datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Scheduled time must be in the future"
        )
    
    # Update campaign
    campaign.status = "scheduled"
    campaign.scheduled_at = scheduled_at
    campaign.settings = campaign.settings or {}
    campaign.settings.update({
        "batch_size": batch_size,
        "interval_minutes": interval_minutes,
    })
    await db.commit()
    
    # Schedule the campaign
    phishing_service = PhishingService(db)
    await phishing_service.schedule_campaign(
        campaign_id=campaign_id,
        scheduled_at=scheduled_at,
        batch_size=batch_size,
        interval_minutes=interval_minutes
    )
    
    return {
        "message": "Campaign scheduled successfully",
        "campaign_id": str(campaign_id),
        "scheduled_at": scheduled_at.isoformat(),
        "batch_size": batch_size,
        "interval_minutes": interval_minutes,
    }


@router.websocket("/campaigns/{campaign_id}/live")
async def campaign_live_updates(
    websocket: WebSocket,
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    WebSocket endpoint for real-time campaign updates.
    
    Args:
        websocket: WebSocket connection
        campaign_id: Campaign ID
        db: Database session
    """
    await websocket.accept()
    
    try:
        # Verify campaign exists
        result = await db.execute(
            select(PhishingCampaign).where(PhishingCampaign.id == campaign_id)
        )
        campaign = result.scalar_one_or_none()
        
        if not campaign:
            await websocket.send_json({"error": "Campaign not found"})
            await websocket.close()
            return
        
        # Send updates every 5 seconds
        while True:
            # Get fresh statistics
            await db.refresh(campaign)
            stats = campaign.get_statistics()
            
            # Get recent events
            recent_events = await db.execute(
                select(PhishingResult).where(
                    and_(
                        PhishingResult.campaign_id == campaign_id,
                        or_(
                            PhishingResult.email_opened_at >= datetime.utcnow() - timedelta(minutes=5),
                            PhishingResult.link_clicked_at >= datetime.utcnow() - timedelta(minutes=5),
                            PhishingResult.reported_at >= datetime.utcnow() - timedelta(minutes=5),
                        )
                    )
                ).limit(10)
            )
            events = []
            for result in recent_events.scalars():
                event = None
                if result.email_opened_at and result.email_opened_at >= datetime.utcnow() - timedelta(minutes=5):
                    event = {"type": "email_opened", "user_id": result.user_id, "timestamp": result.email_opened_at.isoformat()}
                elif result.link_clicked_at and result.link_clicked_at >= datetime.utcnow() - timedelta(minutes=5):
                    event = {"type": "link_clicked", "user_id": result.user_id, "timestamp": result.link_clicked_at.isoformat()}
                elif result.reported_at and result.reported_at >= datetime.utcnow() - timedelta(minutes=5):
                    event = {"type": "reported", "user_id": result.user_id, "timestamp": result.reported_at.isoformat()}
                if event:
                    events.append(event)
            
            # Send update
            await websocket.send_json({
                "statistics": stats,
                "recent_events": events,
                "timestamp": datetime.utcnow().isoformat(),
            })
            
            await asyncio.sleep(5)
            
    except Exception as e:
        await websocket.send_json({"error": str(e)})
        await websocket.close()