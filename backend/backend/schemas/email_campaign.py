"""Email campaign schemas."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator

from models.email_campaign import (
    EmailTemplateType, EmailStatus, CampaignStatus, EmailFrequency
)


class EmailTemplateBase(BaseModel):
    """Base email template schema."""
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255)
    type: EmailTemplateType
    subject: str = Field(..., min_length=1, max_length=500)
    html_content: str
    text_content: Optional[str] = None
    variables: Optional[Dict[str, Any]] = Field(default_factory=dict)
    preview_text: Optional[str] = Field(None, max_length=500)
    from_name: Optional[str] = Field(None, max_length=255)
    from_email: Optional[EmailStr] = None
    reply_to: Optional[EmailStr] = None
    is_active: bool = True


class EmailTemplateCreate(EmailTemplateBase):
    """Create email template schema."""
    pass


class EmailTemplateUpdate(BaseModel):
    """Update email template schema."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    subject: Optional[str] = Field(None, min_length=1, max_length=500)
    html_content: Optional[str] = None
    text_content: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None
    preview_text: Optional[str] = Field(None, max_length=500)
    from_name: Optional[str] = Field(None, max_length=255)
    from_email: Optional[EmailStr] = None
    reply_to: Optional[EmailStr] = None
    is_active: Optional[bool] = None


class EmailTemplateResponse(EmailTemplateBase):
    """Email template response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    is_default: bool = False
    created_by_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    total_sent: int = 0
    total_opened: int = 0
    total_clicked: int = 0
    avg_open_rate: float = 0.0
    avg_click_rate: float = 0.0


class EmailCampaignBase(BaseModel):
    """Base email campaign schema."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    template_id: UUID
    scheduled_at: Optional[datetime] = None
    target_all_users: bool = False
    target_user_roles: Optional[List[str]] = Field(default_factory=list)
    target_user_ids: Optional[List[UUID]] = Field(default_factory=list)
    target_segments: Optional[Dict[str, Any]] = Field(default_factory=dict)
    exclude_unsubscribed: bool = True
    custom_subject: Optional[str] = Field(None, max_length=500)
    custom_preview_text: Optional[str] = Field(None, max_length=500)
    custom_variables: Optional[Dict[str, Any]] = Field(default_factory=dict)


class EmailCampaignCreate(EmailCampaignBase):
    """Create email campaign schema."""
    pass


class EmailCampaignUpdate(BaseModel):
    """Update email campaign schema."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    template_id: Optional[UUID] = None
    scheduled_at: Optional[datetime] = None
    status: Optional[CampaignStatus] = None
    target_all_users: Optional[bool] = None
    target_user_roles: Optional[List[str]] = None
    target_user_ids: Optional[List[UUID]] = None
    target_segments: Optional[Dict[str, Any]] = None
    exclude_unsubscribed: Optional[bool] = None
    custom_subject: Optional[str] = Field(None, max_length=500)
    custom_preview_text: Optional[str] = Field(None, max_length=500)
    custom_variables: Optional[Dict[str, Any]] = None


class EmailCampaignResponse(EmailCampaignBase):
    """Email campaign response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    company_id: Optional[UUID] = None
    status: CampaignStatus = CampaignStatus.DRAFT
    sent_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_recipients: int = 0
    total_sent: int = 0
    total_delivered: int = 0
    total_opened: int = 0
    total_clicked: int = 0
    total_bounced: int = 0
    total_unsubscribed: int = 0
    delivery_rate: float = 0.0
    open_rate: float = 0.0
    click_rate: float = 0.0
    bounce_rate: float = 0.0
    unsubscribe_rate: float = 0.0
    created_by_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime


class EmailLogResponse(BaseModel):
    """Email log response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    campaign_id: Optional[UUID] = None
    template_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    to_email: EmailStr
    from_email: EmailStr
    subject: str
    status: EmailStatus
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    first_opened_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None
    first_clicked_at: Optional[datetime] = None
    bounced_at: Optional[datetime] = None
    unsubscribed_at: Optional[datetime] = None
    open_count: int = 0
    click_count: int = 0
    clicked_links: List[str] = Field(default_factory=list)
    error_message: Optional[str] = None
    bounce_type: Optional[str] = None
    provider: Optional[str] = None
    message_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class EmailEventResponse(BaseModel):
    """Email event response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    email_log_id: UUID
    event_type: str
    timestamp: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    location: Optional[Dict[str, Any]] = None
    device_type: Optional[str] = None
    os: Optional[str] = None
    browser: Optional[str] = None
    clicked_url: Optional[str] = None
    click_position: Optional[int] = None
    bounce_reason: Optional[str] = None


class EmailPreferenceBase(BaseModel):
    """Base email preference schema."""
    is_subscribed: bool = True
    marketing_emails: bool = True
    course_updates: bool = True
    security_alerts: bool = True
    newsletter: bool = True
    promotional: bool = True
    email_frequency: EmailFrequency = EmailFrequency.IMMEDIATELY
    digest_day: Optional[int] = Field(None, ge=0, le=6)
    digest_hour: Optional[int] = Field(9, ge=0, le=23)


class EmailPreferenceUpdate(EmailPreferenceBase):
    """Update email preference schema."""
    is_subscribed: Optional[bool] = None
    marketing_emails: Optional[bool] = None
    course_updates: Optional[bool] = None
    security_alerts: Optional[bool] = None
    newsletter: Optional[bool] = None
    promotional: Optional[bool] = None
    email_frequency: Optional[EmailFrequency] = None
    digest_day: Optional[int] = Field(None, ge=0, le=6)
    digest_hour: Optional[int] = Field(None, ge=0, le=23)


class EmailPreferenceResponse(EmailPreferenceBase):
    """Email preference response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    user_id: UUID
    unsubscribed_at: Optional[datetime] = None
    unsubscribe_token: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class EmailBounceResponse(BaseModel):
    """Email bounce response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    email: EmailStr
    bounce_type: str
    bounce_count: int = 1
    last_bounce_at: datetime
    is_suppressed: bool = False
    suppressed_at: Optional[datetime] = None
    reason: Optional[str] = None
    diagnostic_code: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class EmailTestRequest(BaseModel):
    """Email test request schema."""
    template_id: UUID
    to_email: EmailStr
    variables: Optional[Dict[str, Any]] = Field(default_factory=dict)


class EmailCampaignSendRequest(BaseModel):
    """Campaign send request schema."""
    send_immediately: bool = False
    test_mode: bool = False
    test_recipients: Optional[List[EmailStr]] = Field(default_factory=list)


class EmailCampaignStatsResponse(BaseModel):
    """Campaign statistics response."""
    campaign_id: UUID
    name: str
    status: CampaignStatus
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Overall stats
    total_recipients: int = 0
    total_sent: int = 0
    total_delivered: int = 0
    total_opened: int = 0
    total_clicked: int = 0
    total_bounced: int = 0
    total_unsubscribed: int = 0
    
    # Rates
    delivery_rate: float = 0.0
    open_rate: float = 0.0
    click_rate: float = 0.0
    bounce_rate: float = 0.0
    unsubscribe_rate: float = 0.0
    
    # Time-based stats
    opens_by_hour: Dict[int, int] = Field(default_factory=dict)
    clicks_by_hour: Dict[int, int] = Field(default_factory=dict)
    
    # Device stats
    opens_by_device: Dict[str, int] = Field(default_factory=dict)
    clicks_by_device: Dict[str, int] = Field(default_factory=dict)
    
    # Link performance
    link_clicks: List[Dict[str, Any]] = Field(default_factory=list)