"""Email campaign API routes."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Response
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from api.dependencies import get_db, get_current_active_user, require_company_admin, require_role
from models.user import User, UserRole
from models.email_campaign import (
    EmailTemplate, EmailCampaign, EmailLog, EmailPreference,
    EmailTemplateType, CampaignStatus
)
from schemas.email_campaign import (
    EmailTemplateCreate, EmailTemplateUpdate, EmailTemplateResponse,
    EmailCampaignCreate, EmailCampaignUpdate, EmailCampaignResponse,
    EmailLogResponse, EmailPreferenceUpdate, EmailPreferenceResponse,
    EmailTestRequest, EmailCampaignSendRequest, EmailCampaignStatsResponse
)
from services.email_campaign import campaign_service
from services.email_scheduler import schedule_campaign
from core.security import create_random_token

router = APIRouter(prefix="/api/v1/email", tags=["email-campaigns"])


# Email Templates
@router.post("/templates", response_model=EmailTemplateResponse)
async def create_email_template(
    template: EmailTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.SYSTEM_ADMIN, UserRole.COMPANY_ADMIN])),
):
    """Create a new email template."""
    # Check if slug already exists
    existing = db.query(EmailTemplate).filter(
        EmailTemplate.slug == template.slug
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Template with this slug already exists"
        )
    
    db_template = EmailTemplate(
        **template.model_dump(),
        created_by_id=current_user.id,
    )
    
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    
    return db_template


@router.get("/templates", response_model=List[EmailTemplateResponse])
async def list_email_templates(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    type: Optional[EmailTemplateType] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List email templates."""
    query = db.query(EmailTemplate)
    
    if type:
        query = query.filter(EmailTemplate.type == type)
    
    if is_active is not None:
        query = query.filter(EmailTemplate.is_active == is_active)
    
    templates = query.offset(skip).limit(limit).all()
    return templates


@router.get("/templates/{template_id}", response_model=EmailTemplateResponse)
async def get_email_template(
    template_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get an email template by ID."""
    template = db.query(EmailTemplate).filter(
        EmailTemplate.id == template_id
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    return template


@router.patch("/templates/{template_id}", response_model=EmailTemplateResponse)
async def update_email_template(
    template_id: UUID,
    updates: EmailTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.SYSTEM_ADMIN, UserRole.COMPANY_ADMIN])),
):
    """Update an email template."""
    template = db.query(EmailTemplate).filter(
        EmailTemplate.id == template_id
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(template, field, value)
    
    template.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(template)
    
    return template


@router.delete("/templates/{template_id}")
async def delete_email_template(
    template_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.SYSTEM_ADMIN, UserRole.COMPANY_ADMIN])),
):
    """Delete an email template."""
    template = db.query(EmailTemplate).filter(
        EmailTemplate.id == template_id
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    # Check if template is used in any campaigns
    campaign_count = db.query(EmailCampaign).filter(
        EmailCampaign.template_id == template_id
    ).count()
    
    if campaign_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete template used in {campaign_count} campaigns"
        )
    
    db.delete(template)
    db.commit()
    
    return {"message": "Template deleted successfully"}


@router.post("/templates/{template_id}/test")
async def test_email_template(
    template_id: UUID,
    test_request: EmailTestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.SYSTEM_ADMIN, UserRole.COMPANY_ADMIN])),
):
    """Send a test email using a template."""
    template = db.query(EmailTemplate).filter(
        EmailTemplate.id == template_id
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    # Create a test email log
    from services.email_template import template_engine, EmailPersonalization
    from services.email import email_service
    
    # Get test user for personalization
    test_user = db.query(User).filter(
        User.email == test_request.to_email
    ).first()
    
    if test_user:
        variables = EmailPersonalization.get_default_variables(test_user, test_user.company)
    else:
        variables = {
            'user_name': test_request.to_email.split('@')[0],
            'user_email': test_request.to_email,
        }
    
    # Merge with custom variables
    variables.update(test_request.variables)
    
    # Render template
    rendered = template_engine.render_template(
        template.html_content,
        variables,
        template.text_content,
    )
    
    # Send test email
    success = await email_service.send_email(
        to_email=test_request.to_email,
        subject=f"[TEST] {template.subject}",
        html_content=rendered['html'],
        text_content=rendered['text'],
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send test email"
        )
    
    return {"message": "Test email sent successfully"}


# Email Campaigns
@router.post("/campaigns", response_model=EmailCampaignResponse)
async def create_email_campaign(
    campaign: EmailCampaignCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.SYSTEM_ADMIN, UserRole.COMPANY_ADMIN])),
):
    """Create a new email campaign."""
    # Verify template exists
    template = db.query(EmailTemplate).filter(
        EmailTemplate.id == campaign.template_id
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    db_campaign = await campaign_service.create_campaign(
        db,
        campaign.model_dump(),
        current_user.company_id,
        current_user.id,
    )
    
    return db_campaign


@router.get("/campaigns", response_model=List[EmailCampaignResponse])
async def list_email_campaigns(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[CampaignStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.SYSTEM_ADMIN, UserRole.COMPANY_ADMIN])),
):
    """List email campaigns for the current company."""
    query = db.query(EmailCampaign).filter(
        EmailCampaign.company_id == current_user.company_id
    )
    
    if status:
        query = query.filter(EmailCampaign.status == status)
    
    campaigns = query.order_by(
        EmailCampaign.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    return campaigns


@router.get("/campaigns/{campaign_id}", response_model=EmailCampaignResponse)
async def get_email_campaign(
    campaign_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.SYSTEM_ADMIN, UserRole.COMPANY_ADMIN])),
):
    """Get an email campaign by ID."""
    campaign = db.query(EmailCampaign).filter(
        EmailCampaign.id == campaign_id,
        EmailCampaign.company_id == current_user.company_id,
    ).first()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    return campaign


@router.patch("/campaigns/{campaign_id}", response_model=EmailCampaignResponse)
async def update_email_campaign(
    campaign_id: UUID,
    updates: EmailCampaignUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.SYSTEM_ADMIN, UserRole.COMPANY_ADMIN])),
):
    """Update an email campaign."""
    campaign = db.query(EmailCampaign).filter(
        EmailCampaign.id == campaign_id,
        EmailCampaign.company_id == current_user.company_id,
    ).first()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    updated_campaign = await campaign_service.update_campaign(
        db,
        str(campaign_id),
        updates.model_dump(exclude_unset=True),
    )
    
    return updated_campaign


@router.post("/campaigns/{campaign_id}/send")
async def send_email_campaign(
    campaign_id: UUID,
    send_request: EmailCampaignSendRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.SYSTEM_ADMIN, UserRole.COMPANY_ADMIN])),
):
    """Send an email campaign."""
    campaign = db.query(EmailCampaign).filter(
        EmailCampaign.id == campaign_id,
        EmailCampaign.company_id == current_user.company_id,
    ).first()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    if send_request.send_immediately:
        # Send immediately
        from services.email_scheduler import send_campaign_task
        
        task = send_campaign_task.apply_async(
            args=[str(campaign_id)],
            kwargs={
                'test_mode': send_request.test_mode,
                'test_recipients': send_request.test_recipients,
            },
        )
        
        return {
            "message": "Campaign queued for sending",
            "task_id": task.id,
        }
    else:
        # Schedule for later
        if not campaign.scheduled_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Scheduled time not set"
            )
        
        schedule_campaign(str(campaign_id), campaign.scheduled_at)
        
        return {
            "message": f"Campaign scheduled for {campaign.scheduled_at}",
        }


@router.get("/campaigns/{campaign_id}/recipients")
async def get_campaign_recipients(
    campaign_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.SYSTEM_ADMIN, UserRole.COMPANY_ADMIN])),
):
    """Get list of recipients for a campaign."""
    campaign = db.query(EmailCampaign).filter(
        EmailCampaign.id == campaign_id,
        EmailCampaign.company_id == current_user.company_id,
    ).first()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    recipients = await campaign_service.get_campaign_recipients(db, campaign)
    
    return {
        "total": len(recipients),
        "recipients": [
            {
                "id": str(r.id),
                "email": r.email,
                "name": r.full_name,
                "role": r.role.value if r.role else None,
            }
            for r in recipients[:100]  # Limit to first 100 for preview
        ],
    }


@router.get("/campaigns/{campaign_id}/stats", response_model=EmailCampaignStatsResponse)
async def get_campaign_stats(
    campaign_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.SYSTEM_ADMIN, UserRole.COMPANY_ADMIN])),
):
    """Get detailed campaign statistics."""
    campaign = db.query(EmailCampaign).filter(
        EmailCampaign.id == campaign_id,
        EmailCampaign.company_id == current_user.company_id,
    ).first()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    stats = await campaign_service.get_campaign_analytics(db, str(campaign_id))
    return stats


@router.get("/campaigns/{campaign_id}/logs", response_model=List[EmailLogResponse])
async def get_campaign_logs(
    campaign_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.SYSTEM_ADMIN, UserRole.COMPANY_ADMIN])),
):
    """Get email logs for a campaign."""
    # Verify campaign belongs to user's company
    campaign = db.query(EmailCampaign).filter(
        EmailCampaign.id == campaign_id,
        EmailCampaign.company_id == current_user.company_id,
    ).first()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    query = db.query(EmailLog).filter(
        EmailLog.campaign_id == campaign_id
    )
    
    if status:
        query = query.filter(EmailLog.status == status)
    
    logs = query.order_by(
        EmailLog.sent_at.desc()
    ).offset(skip).limit(limit).all()
    
    return logs


# Email Preferences
@router.get("/preferences", response_model=EmailPreferenceResponse)
async def get_email_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get current user's email preferences."""
    pref = db.query(EmailPreference).filter(
        EmailPreference.user_id == current_user.id
    ).first()
    
    if not pref:
        # Create default preferences
        pref = EmailPreference(
            user_id=current_user.id,
            unsubscribe_token=create_random_token(),
        )
        db.add(pref)
        db.commit()
        db.refresh(pref)
    
    return pref


@router.patch("/preferences", response_model=EmailPreferenceResponse)
async def update_email_preferences(
    updates: EmailPreferenceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update current user's email preferences."""
    pref = db.query(EmailPreference).filter(
        EmailPreference.user_id == current_user.id
    ).first()
    
    if not pref:
        # Create preferences if they don't exist
        pref = EmailPreference(
            user_id=current_user.id,
            unsubscribe_token=create_random_token(),
        )
        db.add(pref)
    
    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(pref, field, value)
    
    pref.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(pref)
    
    return pref


@router.post("/unsubscribe")
async def unsubscribe_email(
    user: str = Query(...),
    token: str = Query(...),
    db: Session = Depends(get_db),
):
    """Unsubscribe from emails using token."""
    success = await campaign_service.handle_unsubscribe(db, user, token)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid unsubscribe token"
        )
    
    return {"message": "Successfully unsubscribed from emails"}


# Email Tracking
@router.get("/track/open/{email_log_id}")
async def track_email_open(
    email_log_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
):
    """Track email open event."""
    # Extract request data
    request_data = {
        'ip_address': request.client.host,
        'user_agent': request.headers.get('user-agent'),
    }
    
    await campaign_service.track_email_open(db, str(email_log_id), request_data)
    
    # Return 1x1 transparent pixel
    pixel = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00\x21\xF9\x04\x01\x00\x00\x00\x00\x2C\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3B'
    
    return Response(content=pixel, media_type="image/gif")


@router.get("/track/click")
async def track_email_click(
    url: str = Query(...),
    id: str = Query(...),
    pos: Optional[int] = Query(None),
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Track email click event and redirect."""
    # Extract request data
    request_data = {
        'ip_address': request.client.host,
        'user_agent': request.headers.get('user-agent'),
    }
    
    await campaign_service.track_email_click(db, id, url, pos, request_data)
    
    # Redirect to original URL
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=url)