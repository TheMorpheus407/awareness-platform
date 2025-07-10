"""Simplified phishing simulation for MVP."""
from typing import List
from uuid import UUID, uuid4
from datetime import datetime, timedelta
import random

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/phishing", tags=["phishing"])

# In-memory storage for MVP
CAMPAIGNS = {}
TEMPLATES = {}
RESULTS = {}


class PhishingTemplate(BaseModel):
    """Phishing email template."""
    id: UUID
    name: str
    subject: str
    body: str
    difficulty: str  # easy, medium, hard
    category: str  # credential, attachment, link


class CampaignCreate(BaseModel):
    """Campaign creation request."""
    name: str
    template_id: UUID
    target_emails: List[EmailStr]
    scheduled_at: Optional[datetime] = None


class CampaignResponse(BaseModel):
    """Campaign response."""
    id: UUID
    name: str
    template_id: UUID
    status: str  # draft, scheduled, active, completed
    target_count: int
    created_at: datetime
    scheduled_at: Optional[datetime]
    completed_at: Optional[datetime]


class CampaignResult(BaseModel):
    """Campaign results."""
    campaign_id: UUID
    total_sent: int
    emails_opened: int
    links_clicked: int
    data_submitted: int
    reported_as_phishing: int
    success_rate: float


@router.get("/templates", response_model=List[PhishingTemplate])
def get_templates():
    """Get all phishing templates."""
    return list(TEMPLATES.values())


@router.get("/campaigns", response_model=List[CampaignResponse])
def get_campaigns():
    """Get all campaigns."""
    return list(CAMPAIGNS.values())


@router.post("/campaigns", response_model=CampaignResponse)
def create_campaign(campaign: CampaignCreate):
    """Create a new phishing campaign."""
    if campaign.template_id not in TEMPLATES:
        raise HTTPException(status_code=404, detail="Template not found")
    
    campaign_id = uuid4()
    new_campaign = CampaignResponse(
        id=campaign_id,
        name=campaign.name,
        template_id=campaign.template_id,
        status="scheduled" if campaign.scheduled_at else "draft",
        target_count=len(campaign.target_emails),
        created_at=datetime.utcnow(),
        scheduled_at=campaign.scheduled_at,
        completed_at=None
    )
    
    CAMPAIGNS[campaign_id] = new_campaign
    
    # Initialize results
    RESULTS[campaign_id] = {
        "campaign_id": campaign_id,
        "targets": campaign.target_emails,
        "sent": [],
        "opened": [],
        "clicked": [],
        "submitted": [],
        "reported": []
    }
    
    return new_campaign


@router.post("/campaigns/{campaign_id}/start")
def start_campaign(campaign_id: UUID):
    """Start a phishing campaign."""
    if campaign_id not in CAMPAIGNS:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    campaign = CAMPAIGNS[campaign_id]
    campaign.status = "active"
    
    # Simulate sending emails
    results = RESULTS[campaign_id]
    results["sent"] = results["targets"].copy()
    
    return {"message": "Campaign started", "emails_sent": len(results["sent"])}


@router.post("/track/{campaign_id}/open")
def track_email_open(campaign_id: UUID, email: EmailStr):
    """Track email open event."""
    if campaign_id not in RESULTS:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    results = RESULTS[campaign_id]
    if email in results["targets"] and email not in results["opened"]:
        results["opened"].append(email)
    
    return {"tracked": True}


@router.post("/track/{campaign_id}/click")
def track_link_click(campaign_id: UUID, email: EmailStr):
    """Track link click event."""
    if campaign_id not in RESULTS:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    results = RESULTS[campaign_id]
    if email in results["targets"] and email not in results["clicked"]:
        results["clicked"].append(email)
        
        # Show educational content
        return {
            "tracked": True,
            "message": "This was a simulated phishing email!",
            "tips": [
                "Check the sender's email address carefully",
                "Hover over links before clicking",
                "Be suspicious of urgent requests",
                "Verify requests through official channels"
            ]
        }
    
    return {"tracked": False}


@router.post("/track/{campaign_id}/report")
def report_phishing(campaign_id: UUID, email: EmailStr):
    """Report email as phishing."""
    if campaign_id not in RESULTS:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    results = RESULTS[campaign_id]
    if email in results["targets"] and email not in results["reported"]:
        results["reported"].append(email)
    
    return {
        "message": "Thank you for reporting this phishing attempt!",
        "correct": True
    }


@router.get("/campaigns/{campaign_id}/results", response_model=CampaignResult)
def get_campaign_results(campaign_id: UUID):
    """Get campaign results."""
    if campaign_id not in CAMPAIGNS:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if campaign_id not in RESULTS:
        raise HTTPException(status_code=400, detail="No results available")
    
    results = RESULTS[campaign_id]
    total = len(results["targets"])
    clicked = len(results["clicked"])
    
    return CampaignResult(
        campaign_id=campaign_id,
        total_sent=len(results["sent"]),
        emails_opened=len(results["opened"]),
        links_clicked=clicked,
        data_submitted=len(results["submitted"]),
        reported_as_phishing=len(results["reported"]),
        success_rate=round((clicked / total * 100) if total > 0 else 0, 2)
    )


# Initialize demo templates
def init_demo_templates():
    """Initialize demo phishing templates."""
    templates = [
        {
            "name": "IT Support Password Reset",
            "subject": "Urgent: Password Reset Required",
            "body": "Your password will expire in 24 hours. Click here to reset: {link}",
            "difficulty": "easy",
            "category": "credential"
        },
        {
            "name": "CEO Urgent Request",
            "subject": "Urgent Request - Please Response ASAP",
            "body": "I need you to process a wire transfer immediately. Reply for details.",
            "difficulty": "medium",
            "category": "link"
        },
        {
            "name": "Package Delivery",
            "subject": "Your package could not be delivered",
            "body": "We attempted delivery but nobody was home. Reschedule here: {link}",
            "difficulty": "easy",
            "category": "link"
        }
    ]
    
    for template_data in templates:
        template_id = uuid4()
        TEMPLATES[template_id] = PhishingTemplate(
            id=template_id,
            **template_data
        )


# Initialize demo data
init_demo_templates()