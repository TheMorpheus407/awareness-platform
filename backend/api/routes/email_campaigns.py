"""Email campaigns routes."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from db.session import get_db
from api.dependencies.auth import get_current_active_user, require_company_admin
from api.dependencies.common import get_pagination_params
from models.user import User
from models.email_campaign import EmailCampaign, CampaignStatus
from services.email_campaign import EmailCampaignService
from schemas.base import PaginatedResponse

router = APIRouter()


@router.get("/", response_model=PaginatedResponse)
async def list_campaigns(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    pagination: tuple[int, int] = Depends(get_pagination_params),
    status: Optional[str] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search in campaign name"),
):
    """
    List email campaigns for the current user's company.
    
    Args:
        db: Database session
        current_user: Current authenticated user
        pagination: Offset and limit
        status: Optional status filter
        search: Optional search term
        
    Returns:
        Paginated list of campaigns
    """
    offset, limit = pagination
    
    # Build query
    query = select(EmailCampaign).where(
        EmailCampaign.company_id == current_user.company_id
    )
    
    # Apply filters
    if status:
        query = query.where(EmailCampaign.status == status)
        
    if search:
        query = query.where(EmailCampaign.name.ilike(f"%{search}%"))
        
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination and ordering
    query = query.order_by(EmailCampaign.created_at.desc()).offset(offset).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    campaigns = result.scalars().all()
    
    return PaginatedResponse(
        items=[{
            "id": c.id,
            "name": c.name,
            "status": c.status,
            "template_id": c.template_id,
            "total_recipients": c.total_recipients,
            "emails_sent": c.emails_sent,
            "emails_failed": c.emails_failed,
            "scheduled_at": c.scheduled_at.isoformat() if c.scheduled_at else None,
            "started_at": c.started_at.isoformat() if c.started_at else None,
            "completed_at": c.completed_at.isoformat() if c.completed_at else None,
            "created_at": c.created_at.isoformat(),
        } for c in campaigns],
        total=total,
        page=(offset // limit) + 1,
        size=limit,
        pages=(total + limit - 1) // limit,
    )


@router.post("/", response_model=dict)
async def create_campaign(
    campaign_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_company_admin),
) -> dict:
    """
    Create a new email campaign (admin only).
    
    Args:
        campaign_data: Campaign creation data
        db: Database session
        current_user: Current authenticated user (must be admin)
        
    Returns:
        Created campaign
    """
    campaign_service = EmailCampaignService(db)
    
    try:
        campaign = await campaign_service.create_campaign(
            name=campaign_data.get("name"),
            template_id=campaign_data.get("template_id"),
            company_id=current_user.company_id,
            target_users=campaign_data.get("target_users"),
            target_filters=campaign_data.get("target_filters"),
            scheduled_at=campaign_data.get("scheduled_at"),
            variables=campaign_data.get("variables"),
            created_by=current_user.id,
        )
        
        return {
            "id": campaign.id,
            "name": campaign.name,
            "status": campaign.status,
            "total_recipients": campaign.total_recipients,
            "created_at": campaign.created_at.isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{campaign_id}", response_model=dict)
async def get_campaign(
    campaign_id: int,
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
    """
    # Get campaign
    result = await db.execute(
        select(EmailCampaign).where(
            and_(
                EmailCampaign.id == campaign_id,
                EmailCampaign.company_id == current_user.company_id,
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
        "id": campaign.id,
        "name": campaign.name,
        "status": campaign.status,
        "template_id": campaign.template_id,
        "total_recipients": campaign.total_recipients,
        "emails_sent": campaign.emails_sent,
        "emails_failed": campaign.emails_failed,
        "target_filters": campaign.target_filters,
        "variables": campaign.variables,
        "scheduled_at": campaign.scheduled_at.isoformat() if campaign.scheduled_at else None,
        "started_at": campaign.started_at.isoformat() if campaign.started_at else None,
        "completed_at": campaign.completed_at.isoformat() if campaign.completed_at else None,
        "created_at": campaign.created_at.isoformat(),
    }


@router.patch("/{campaign_id}", response_model=dict)
async def update_campaign(
    campaign_id: int,
    updates: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_company_admin),
) -> dict:
    """
    Update campaign details (admin only).
    
    Args:
        campaign_id: Campaign ID
        updates: Fields to update
        db: Database session
        current_user: Current authenticated user (must be admin)
        
    Returns:
        Updated campaign
    """
    campaign_service = EmailCampaignService(db)
    
    try:
        campaign = await campaign_service.update_campaign(
            campaign_id=campaign_id,
            **updates
        )
        
        return {
            "id": campaign.id,
            "name": campaign.name,
            "status": campaign.status,
            "updated_at": campaign.updated_at.isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{campaign_id}/schedule", response_model=dict)
async def schedule_campaign(
    campaign_id: int,
    schedule_data: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_company_admin),
) -> dict:
    """
    Schedule a campaign for sending (admin only).
    
    Args:
        campaign_id: Campaign ID
        schedule_data: Scheduling data (scheduled_at, send_immediately)
        db: Database session
        current_user: Current authenticated user (must be admin)
        
    Returns:
        Updated campaign
    """
    campaign_service = EmailCampaignService(db)
    
    try:
        scheduled_at = schedule_data.get("scheduled_at")
        if scheduled_at and isinstance(scheduled_at, str):
            scheduled_at = datetime.fromisoformat(scheduled_at.replace('Z', '+00:00'))
            
        campaign = await campaign_service.schedule_campaign(
            campaign_id=campaign_id,
            scheduled_at=scheduled_at,
            send_immediately=schedule_data.get("send_immediately", False),
        )
        
        return {
            "id": campaign.id,
            "name": campaign.name,
            "status": campaign.status,
            "scheduled_at": campaign.scheduled_at.isoformat() if campaign.scheduled_at else None,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{campaign_id}/pause", response_model=dict)
async def pause_campaign(
    campaign_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_company_admin),
) -> dict:
    """
    Pause a running campaign (admin only).
    
    Args:
        campaign_id: Campaign ID
        db: Database session
        current_user: Current authenticated user (must be admin)
        
    Returns:
        Updated campaign
    """
    campaign_service = EmailCampaignService(db)
    
    try:
        campaign = await campaign_service.pause_campaign(campaign_id)
        
        return {
            "id": campaign.id,
            "name": campaign.name,
            "status": campaign.status,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{campaign_id}/resume", response_model=dict)
async def resume_campaign(
    campaign_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_company_admin),
) -> dict:
    """
    Resume a paused campaign (admin only).
    
    Args:
        campaign_id: Campaign ID
        db: Database session
        current_user: Current authenticated user (must be admin)
        
    Returns:
        Updated campaign
    """
    campaign_service = EmailCampaignService(db)
    
    try:
        campaign = await campaign_service.resume_campaign(campaign_id)
        
        return {
            "id": campaign.id,
            "name": campaign.name,
            "status": campaign.status,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{campaign_id}/cancel", response_model=dict)
async def cancel_campaign(
    campaign_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_company_admin),
) -> dict:
    """
    Cancel a campaign (admin only).
    
    Args:
        campaign_id: Campaign ID
        db: Database session
        current_user: Current authenticated user (must be admin)
        
    Returns:
        Updated campaign
    """
    campaign_service = EmailCampaignService(db)
    
    try:
        campaign = await campaign_service.cancel_campaign(campaign_id)
        
        return {
            "id": campaign.id,
            "name": campaign.name,
            "status": campaign.status,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{campaign_id}/stats", response_model=dict)
async def get_campaign_stats(
    campaign_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Get campaign statistics.
    
    Args:
        campaign_id: Campaign ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Campaign statistics
    """
    campaign_service = EmailCampaignService(db)
    
    try:
        stats = await campaign_service.get_campaign_stats(campaign_id)
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{campaign_id}/duplicate", response_model=dict)
async def duplicate_campaign(
    campaign_id: int,
    duplicate_data: Dict[str, str] = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_company_admin),
) -> dict:
    """
    Create a copy of an existing campaign (admin only).
    
    Args:
        campaign_id: Campaign ID to duplicate
        duplicate_data: New campaign name
        db: Database session
        current_user: Current authenticated user (must be admin)
        
    Returns:
        New campaign
    """
    campaign_service = EmailCampaignService(db)
    
    try:
        new_campaign = await campaign_service.duplicate_campaign(
            campaign_id=campaign_id,
            new_name=duplicate_data.get("name"),
            created_by=current_user.id,
        )
        
        return {
            "id": new_campaign.id,
            "name": new_campaign.name,
            "status": new_campaign.status,
            "created_at": new_campaign.created_at.isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{campaign_id}/test", response_model=dict)
async def test_campaign(
    campaign_id: int,
    test_data: Dict[str, List[str]] = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_company_admin),
) -> dict:
    """
    Send test emails for a campaign (admin only).
    
    Args:
        campaign_id: Campaign ID
        test_data: Dictionary with 'emails' list
        db: Database session
        current_user: Current authenticated user (must be admin)
        
    Returns:
        Test results
    """
    campaign_service = EmailCampaignService(db)
    
    try:
        results = await campaign_service.test_campaign(
            campaign_id=campaign_id,
            test_emails=test_data.get("emails", []),
        )
        
        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
