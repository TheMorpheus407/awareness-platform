"""Phishing simulation API routes."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.orm import Session

from backend.api.deps import get_current_user, get_db, require_role
from backend.models import User, UserRole
from backend.schemas.phishing import (
    CampaignStatus,
    PhishingTemplateCreate, PhishingTemplateUpdate, PhishingTemplateResponse,
    PhishingCampaignCreate, PhishingCampaignUpdate, PhishingCampaignResponse,
    PhishingTrackingEvent, PhishingReportRequest,
    CampaignAnalytics, ComplianceReport, TemplateLibraryFilter
)
from backend.services.phishing_service import PhishingService

router = APIRouter(prefix="/phishing", tags=["phishing"])


# Template endpoints
@router.post("/templates", response_model=PhishingTemplateResponse)
def create_template(
    template: PhishingTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.MANAGER]))
):
    """Create a new phishing template."""
    service = PhishingService(db)
    
    # Admins can create public templates, managers create company-specific
    company_id = None if current_user.role == UserRole.ADMIN else current_user.company_id
    
    return service.create_template(
        template_data=template.model_dump(),
        company_id=company_id
    )


@router.get("/templates", response_model=List[PhishingTemplateResponse])
def list_templates(
    categories: Optional[List[str]] = Query(None),
    difficulties: Optional[List[str]] = Query(None),
    languages: Optional[List[str]] = Query(None),
    is_public: Optional[bool] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List available phishing templates."""
    service = PhishingService(db)
    
    filters = {}
    if categories:
        filters["categories"] = categories
    if difficulties:
        filters["difficulties"] = difficulties
    if languages:
        filters["languages"] = languages
    if is_public is not None:
        filters["is_public"] = is_public
    if search:
        filters["search_query"] = search
    
    return service.list_templates(
        company_id=current_user.company_id,
        filters=filters
    )


@router.get("/templates/{template_id}", response_model=PhishingTemplateResponse)
def get_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific phishing template."""
    service = PhishingService(db)
    return service.get_template(template_id, current_user.company_id)


@router.put("/templates/{template_id}", response_model=PhishingTemplateResponse)
def update_template(
    template_id: int,
    template: PhishingTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.MANAGER]))
):
    """Update a phishing template."""
    service = PhishingService(db)
    return service.update_template(
        template_id,
        template.model_dump(exclude_unset=True),
        current_user.company_id
    )


@router.delete("/templates/{template_id}", status_code=204)
def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.MANAGER]))
):
    """Delete a phishing template."""
    service = PhishingService(db)
    service.delete_template(template_id, current_user.company_id)
    return Response(status_code=204)


# Campaign endpoints
@router.post("/campaigns", response_model=PhishingCampaignResponse)
def create_campaign(
    campaign: PhishingCampaignCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.MANAGER]))
):
    """Create a new phishing campaign."""
    service = PhishingService(db)
    return service.create_campaign(
        campaign_data=campaign.model_dump(),
        company_id=current_user.company_id,
        created_by_id=current_user.id
    )


@router.get("/campaigns", response_model=List[PhishingCampaignResponse])
def list_campaigns(
    status: Optional[CampaignStatus] = None,
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.MANAGER]))
):
    """List phishing campaigns."""
    service = PhishingService(db)
    campaigns = service.list_campaigns(
        company_id=current_user.company_id,
        status=status,
        limit=limit,
        offset=offset
    )
    
    # Calculate response metrics for each campaign
    for campaign in campaigns:
        results = campaign.results
        campaign.total_recipients = len(results)
        campaign.emails_sent = len([r for r in results if r.email_sent_at])
        campaign.emails_opened = len([r for r in results if r.email_opened_at])
        campaign.links_clicked = len([r for r in results if r.link_clicked_at])
        campaign.credentials_entered = len([r for r in results if r.data_submitted_at])
        campaign.reported = len([r for r in results if r.reported_at])
        
        if campaign.emails_sent > 0:
            campaign.open_rate = campaign.emails_opened / campaign.emails_sent * 100
            campaign.click_rate = campaign.links_clicked / campaign.emails_sent * 100
            campaign.report_rate = campaign.reported / campaign.emails_sent * 100
    
    return campaigns


@router.get("/campaigns/{campaign_id}", response_model=PhishingCampaignResponse)
def get_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.MANAGER]))
):
    """Get a specific phishing campaign."""
    service = PhishingService(db)
    campaign = service.get_campaign(campaign_id, current_user.company_id)
    
    # Calculate response metrics
    results = campaign.results
    campaign.total_recipients = len(results)
    campaign.emails_sent = len([r for r in results if r.email_sent_at])
    campaign.emails_opened = len([r for r in results if r.email_opened_at])
    campaign.links_clicked = len([r for r in results if r.link_clicked_at])
    campaign.credentials_entered = len([r for r in results if r.data_submitted_at])
    campaign.reported = len([r for r in results if r.reported_at])
    
    if campaign.emails_sent > 0:
        campaign.open_rate = campaign.emails_opened / campaign.emails_sent * 100
        campaign.click_rate = campaign.links_clicked / campaign.emails_sent * 100
        campaign.report_rate = campaign.reported / campaign.emails_sent * 100
    
    return campaign


@router.put("/campaigns/{campaign_id}", response_model=PhishingCampaignResponse)
def update_campaign(
    campaign_id: int,
    campaign: PhishingCampaignUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.MANAGER]))
):
    """Update a phishing campaign."""
    service = PhishingService(db)
    return service.update_campaign(
        campaign_id,
        campaign.model_dump(exclude_unset=True),
        current_user.company_id
    )


@router.post("/campaigns/{campaign_id}/schedule", response_model=PhishingCampaignResponse)
def schedule_campaign(
    campaign_id: int,
    scheduled_at: datetime,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.MANAGER]))
):
    """Schedule a phishing campaign."""
    service = PhishingService(db)
    return service.schedule_campaign(campaign_id, scheduled_at, current_user.company_id)


@router.post("/campaigns/{campaign_id}/start", response_model=PhishingCampaignResponse)
def start_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.MANAGER]))
):
    """Start a scheduled phishing campaign."""
    service = PhishingService(db)
    return service.start_campaign(campaign_id, current_user.company_id)


@router.post("/campaigns/{campaign_id}/cancel", response_model=PhishingCampaignResponse)
def cancel_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.MANAGER]))
):
    """Cancel a phishing campaign."""
    service = PhishingService(db)
    return service.cancel_campaign(campaign_id, current_user.company_id)


# Tracking endpoints (public, no auth required)
@router.get("/track/open/{tracking_id}")
def track_email_open(
    tracking_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Track email open event."""
    service = PhishingService(db)
    
    tracking_event = PhishingTrackingEvent(
        tracking_id=tracking_id,
        event_type="open",
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
        timestamp=datetime.utcnow()
    )
    
    service.track_email_open(tracking_event)
    
    # Return 1x1 transparent pixel
    pixel = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00\x21\xF9\x04\x01\x00\x00\x00\x00\x2C\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3B'
    return Response(content=pixel, media_type="image/gif")


@router.get("/track/click/{tracking_id}")
def track_link_click(
    tracking_id: str,
    url: str = Query(..., description="Original URL to redirect to"),
    request: Request,
    db: Session = Depends(get_db)
):
    """Track link click event and redirect."""
    service = PhishingService(db)
    
    tracking_event = PhishingTrackingEvent(
        tracking_id=tracking_id,
        event_type="click",
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
        timestamp=datetime.utcnow(),
        additional_data={"original_url": url}
    )
    
    redirect_url = service.track_link_click(tracking_event)
    
    # Redirect to training or original URL
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=redirect_url or url, status_code=302)


@router.post("/track/submit/{tracking_id}")
def track_data_submission(
    tracking_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Track credential submission event."""
    service = PhishingService(db)
    
    tracking_event = PhishingTrackingEvent(
        tracking_id=tracking_id,
        event_type="submit",
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
        timestamp=datetime.utcnow()
    )
    
    service.track_data_submission(tracking_event)
    
    return {"status": "tracked"}


# Reporting endpoints
@router.post("/report")
def report_phishing(
    report: PhishingReportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Report a phishing email."""
    service = PhishingService(db)
    service.report_phishing(
        campaign_id=report.campaign_id,
        user_id=current_user.id,
        reason=report.reason
    )
    
    return {"status": "reported", "message": "Thank you for reporting this phishing attempt!"}


# Analytics endpoints
@router.get("/campaigns/{campaign_id}/analytics", response_model=CampaignAnalytics)
def get_campaign_analytics(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.MANAGER]))
):
    """Get detailed analytics for a campaign."""
    service = PhishingService(db)
    return service.get_campaign_analytics(campaign_id, current_user.company_id)


@router.get("/compliance-report", response_model=ComplianceReport)
def get_compliance_report(
    start_date: datetime = Query(..., description="Report start date"),
    end_date: datetime = Query(..., description="Report end date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.MANAGER]))
):
    """Generate compliance report for phishing simulations."""
    service = PhishingService(db)
    return service.get_compliance_report(
        current_user.company_id,
        start_date,
        end_date
    )


# Dashboard endpoint for quick stats
@router.get("/dashboard")
def get_phishing_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.MANAGER]))
):
    """Get phishing simulation dashboard data."""
    service = PhishingService(db)
    
    # Get recent campaigns
    recent_campaigns = service.list_campaigns(
        company_id=current_user.company_id,
        limit=5,
        offset=0
    )
    
    # Calculate overall metrics
    total_campaigns = len(recent_campaigns)
    total_users_tested = sum(len(c.results) for c in recent_campaigns)
    total_clicks = sum(len([r for r in c.results if r.link_clicked_at]) for c in recent_campaigns)
    
    overall_click_rate = (total_clicks / total_users_tested * 100) if total_users_tested > 0 else 0
    
    return {
        "total_campaigns": total_campaigns,
        "active_campaigns": len([c for c in recent_campaigns if c.status == CampaignStatus.RUNNING]),
        "total_users_tested": total_users_tested,
        "overall_click_rate": round(overall_click_rate, 2),
        "recent_campaigns": [
            {
                "id": c.id,
                "name": c.name,
                "status": c.status,
                "click_rate": c.click_rate if hasattr(c, 'click_rate') else 0,
                "started_at": c.started_at
            }
            for c in recent_campaigns[:5]
        ]
    }