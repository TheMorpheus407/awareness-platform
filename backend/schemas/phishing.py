"""Phishing simulation schemas."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict, field_validator
import re


# Enums
class CampaignStatus(str, Enum):
    """Campaign status enum."""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TemplateDifficulty(str, Enum):
    """Template difficulty enum."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class TemplateCategory(str, Enum):
    """Template category enum."""
    CREDENTIAL_HARVESTING = "credential_harvesting"
    MALWARE = "malware"
    BUSINESS_EMAIL_COMPROMISE = "business_email_compromise"
    SOCIAL_ENGINEERING = "social_engineering"
    TECH_SUPPORT = "tech_support"
    INVOICE_FRAUD = "invoice_fraud"
    PACKAGE_DELIVERY = "package_delivery"
    SOCIAL_MEDIA = "social_media"
    GENERAL = "general"


# Template Schemas
class PhishingTemplateBase(BaseModel):
    """Base schema for phishing templates."""
    name: str = Field(..., min_length=1, max_length=255)
    category: TemplateCategory
    difficulty: TemplateDifficulty
    subject: str = Field(..., min_length=1, max_length=500)
    sender_name: str = Field(..., min_length=1, max_length=255)
    sender_email: str = Field(..., min_length=1, max_length=255)
    html_content: str = Field(..., min_length=1)
    text_content: Optional[str] = None
    landing_page_html: Optional[str] = None
    language: str = Field(default="de", max_length=10)
    is_public: bool = True

    @field_validator('sender_email')
    @classmethod
    def validate_email(cls, v):
        """Validate email format."""
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, v):
            raise ValueError('Invalid email format')
        return v


class PhishingTemplateCreate(PhishingTemplateBase):
    """Schema for creating phishing templates."""
    pass


class PhishingTemplateUpdate(BaseModel):
    """Schema for updating phishing templates."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    category: Optional[TemplateCategory] = None
    difficulty: Optional[TemplateDifficulty] = None
    subject: Optional[str] = Field(None, min_length=1, max_length=500)
    sender_name: Optional[str] = Field(None, min_length=1, max_length=255)
    sender_email: Optional[str] = Field(None, min_length=1, max_length=255)
    html_content: Optional[str] = Field(None, min_length=1)
    text_content: Optional[str] = None
    landing_page_html: Optional[str] = None
    language: Optional[str] = Field(None, max_length=10)
    is_public: Optional[bool] = None


class PhishingTemplateResponse(PhishingTemplateBase):
    """Response schema for phishing templates."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    company_id: Optional[int]
    created_at: datetime
    updated_at: datetime


# Campaign Schemas
class CampaignTargetGroup(BaseModel):
    """Schema for campaign target groups."""
    type: str = Field(..., description="Type of target: department, role, or users")
    value: List[str] = Field(..., description="List of department names, roles, or user IDs")


class CampaignSettings(BaseModel):
    """Schema for campaign settings."""
    track_opens: bool = True
    track_clicks: bool = True
    capture_credentials: bool = False
    redirect_url: Optional[str] = None
    landing_page_url: Optional[str] = None
    training_url: Optional[str] = None
    send_rate_per_hour: Optional[int] = Field(None, ge=1, le=1000)
    randomize_send_times: bool = True


class PhishingCampaignBase(BaseModel):
    """Base schema for phishing campaigns."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    template_id: int
    target_groups: List[CampaignTargetGroup]
    scheduled_at: Optional[datetime] = None
    settings: CampaignSettings


class PhishingCampaignCreate(PhishingCampaignBase):
    """Schema for creating phishing campaigns."""
    pass


class PhishingCampaignUpdate(BaseModel):
    """Schema for updating phishing campaigns."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    template_id: Optional[int] = None
    target_groups: Optional[List[CampaignTargetGroup]] = None
    scheduled_at: Optional[datetime] = None
    settings: Optional[CampaignSettings] = None
    status: Optional[CampaignStatus] = None


class PhishingCampaignResponse(PhishingCampaignBase):
    """Response schema for phishing campaigns."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    company_id: int
    created_by_id: int
    status: CampaignStatus
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    # Computed fields
    total_recipients: int = 0
    emails_sent: int = 0
    emails_opened: int = 0
    links_clicked: int = 0
    credentials_entered: int = 0
    reported: int = 0
    
    # Rates
    open_rate: float = 0.0
    click_rate: float = 0.0
    report_rate: float = 0.0


# Result Schemas
class PhishingResultBase(BaseModel):
    """Base schema for phishing results."""
    campaign_id: int
    user_id: int


class PhishingResultCreate(PhishingResultBase):
    """Schema for creating phishing results."""
    email_sent_at: Optional[datetime] = None


class PhishingResultUpdate(BaseModel):
    """Schema for updating phishing results."""
    email_opened_at: Optional[datetime] = None
    link_clicked_at: Optional[datetime] = None
    data_submitted_at: Optional[datetime] = None
    reported_at: Optional[datetime] = None
    ip_address: Optional[str] = Field(None, max_length=45)
    user_agent: Optional[str] = None
    location_data: Optional[Dict[str, Any]] = None


class PhishingResultResponse(PhishingResultBase):
    """Response schema for phishing results."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    email_sent_at: Optional[datetime]
    email_opened_at: Optional[datetime]
    link_clicked_at: Optional[datetime]
    data_submitted_at: Optional[datetime]
    reported_at: Optional[datetime]
    ip_address: Optional[str]
    user_agent: Optional[str]
    location_data: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    
    # Computed fields
    was_clicked: bool = False
    was_reported: bool = False
    response_time_seconds: Optional[int] = None


# Tracking Schemas
class PhishingTrackingEvent(BaseModel):
    """Schema for tracking events."""
    tracking_id: str = Field(..., description="Unique tracking ID from email")
    event_type: str = Field(..., description="Type of event: open, click, submit, report")
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    additional_data: Optional[Dict[str, Any]] = None


class PhishingReportRequest(BaseModel):
    """Schema for reporting phishing."""
    campaign_id: int
    reason: Optional[str] = None
    comments: Optional[str] = None


# Campaign Analytics
class CampaignAnalytics(BaseModel):
    """Detailed campaign analytics."""
    campaign_id: int
    campaign_name: str
    status: CampaignStatus
    
    # Timing
    scheduled_at: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_hours: Optional[float]
    
    # Recipients
    total_recipients: int
    emails_sent: int
    emails_pending: int
    emails_failed: int
    
    # Engagement
    unique_opens: int
    total_opens: int
    unique_clicks: int
    total_clicks: int
    credentials_entered: int
    reported_suspicious: int
    
    # Rates
    delivery_rate: float
    open_rate: float
    click_rate: float
    report_rate: float
    failure_rate: float
    
    # Time-based metrics
    avg_time_to_open_minutes: Optional[float]
    avg_time_to_click_minutes: Optional[float]
    fastest_click_minutes: Optional[float]
    
    # Risk scoring
    risk_score: float  # 0-100, higher = more users failed
    
    # Department/role breakdown
    department_stats: List[Dict[str, Any]]
    role_stats: List[Dict[str, Any]]


# Compliance Reporting
class ComplianceReport(BaseModel):
    """Compliance report schema."""
    company_id: int
    report_period_start: datetime
    report_period_end: datetime
    
    # Campaign statistics
    total_campaigns: int
    total_users_tested: int
    unique_users_tested: int
    
    # Results
    total_emails_sent: int
    total_clicks: int
    overall_click_rate: float
    overall_report_rate: float
    
    # Improvement metrics
    click_rate_trend: str  # improving, stable, declining
    report_rate_trend: str
    
    # Training effectiveness
    users_requiring_training: int
    users_completed_training: int
    training_completion_rate: float
    
    # Risk assessment
    high_risk_users: List[Dict[str, Any]]
    departmental_risk_scores: List[Dict[str, Any]]
    
    # Compliance status
    testing_frequency_compliant: bool
    coverage_compliant: bool
    training_compliant: bool
    overall_compliance_score: float  # 0-100


# Template Library
class TemplateLibraryFilter(BaseModel):
    """Filter options for template library."""
    categories: Optional[List[TemplateCategory]] = None
    difficulties: Optional[List[TemplateDifficulty]] = None
    languages: Optional[List[str]] = None
    is_public: Optional[bool] = None
    search_query: Optional[str] = None