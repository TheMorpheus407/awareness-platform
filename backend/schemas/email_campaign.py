"""
Email campaign schemas for automated email communications.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import EmailStr, Field, field_validator

from .base import BaseSchema, PaginatedResponse, TimestampMixin, UUIDMixin


class EmailCampaignStatus(str, Enum):
    """Email campaign status."""

    DRAFT = "draft"
    SCHEDULED = "scheduled"
    SENDING = "sending"
    SENT = "sent"
    CANCELLED = "cancelled"
    FAILED = "failed"


class EmailTemplateType(str, Enum):
    """Email template types."""

    WELCOME = "welcome"
    TRAINING_REMINDER = "training_reminder"
    TRAINING_OVERDUE = "training_overdue"
    CERTIFICATE = "certificate"
    PASSWORD_RESET = "password_reset"
    ACCOUNT_VERIFICATION = "account_verification"
    SECURITY_ALERT = "security_alert"
    COMPLIANCE_UPDATE = "compliance_update"
    CUSTOM = "custom"


class EmailPriority(str, Enum):
    """Email priority levels."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class EmailTemplate(BaseSchema, UUIDMixin, TimestampMixin):
    """Email template definition."""

    name: str = Field(..., min_length=1, max_length=255)
    type: EmailTemplateType
    subject: str = Field(..., min_length=1, max_length=255)
    from_name: str = Field(..., min_length=1, max_length=100)
    from_email: EmailStr
    reply_to: Optional[EmailStr] = None
    html_content: str = Field(..., description="HTML email template with variables")
    text_content: str = Field(..., description="Plain text template with variables")
    variables: List[str] = Field(
        default_factory=list,
        description="List of template variables (e.g., {{first_name}})",
    )
    is_active: bool = Field(True)
    language: str = Field("de", max_length=2)
    tags: List[str] = Field(default_factory=list)

    @field_validator("variables")
    @classmethod
    def extract_variables(cls, v: List[str], info) -> List[str]:
        """Extract variables from template content if not provided."""
        if not v and "html_content" in info.data:
            import re
            # Extract {{variable}} patterns
            pattern = r"\{\{(\w+)\}\}"
            html_vars = re.findall(pattern, info.data.get("html_content", ""))
            text_vars = re.findall(pattern, info.data.get("text_content", ""))
            return list(set(html_vars + text_vars))
        return v


class EmailCampaign(BaseSchema, UUIDMixin, TimestampMixin):
    """Email campaign summary."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    template_id: UUID
    status: EmailCampaignStatus = Field(EmailCampaignStatus.DRAFT)
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_recipients: int = Field(0, ge=0)
    priority: EmailPriority = Field(EmailPriority.NORMAL)
    company_id: UUID


class EmailCampaignCreate(BaseSchema):
    """Schema for creating an email campaign."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    template_id: UUID
    recipient_filters: Dict[str, Any] = Field(
        ...,
        description="Filters to select recipients (e.g., {'department': 'IT', 'training_overdue': true})",
    )
    excluded_users: List[UUID] = Field(
        default_factory=list, description="User IDs to exclude"
    )
    scheduled_at: Optional[datetime] = Field(
        None, description="When to send the campaign"
    )
    priority: EmailPriority = Field(EmailPriority.NORMAL)
    test_recipients: List[EmailStr] = Field(
        default_factory=list,
        max_length=10,
        description="Send test emails before campaign",
    )
    variable_mappings: Dict[str, str] = Field(
        default_factory=dict,
        description="Map template variables to user fields",
    )

    @field_validator("scheduled_at")
    @classmethod
    def validate_scheduled_at(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Ensure scheduled time is in the future."""
        if v and v <= datetime.utcnow():
            raise ValueError("Scheduled time must be in the future")
        return v


class EmailCampaignUpdate(BaseSchema):
    """Schema for updating an email campaign."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    scheduled_at: Optional[datetime] = None
    priority: Optional[EmailPriority] = None


class EmailRecipient(BaseSchema):
    """Email recipient details."""

    user_id: UUID
    email: EmailStr
    first_name: str
    last_name: str
    variables: Dict[str, Any] = Field(
        default_factory=dict, description="Template variables for this recipient"
    )
    status: str = Field("pending", description="Delivery status")
    sent_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None
    bounced: bool = Field(False)
    bounce_reason: Optional[str] = None
    unsubscribed: bool = Field(False)


class EmailCampaignDetail(EmailCampaign):
    """Detailed email campaign with statistics."""

    template: EmailTemplate
    recipients: List[EmailRecipient] = Field(
        default_factory=list, description="First 100 recipients"
    )
    emails_sent: int = Field(0, ge=0)
    emails_delivered: int = Field(0, ge=0)
    emails_opened: int = Field(0, ge=0)
    emails_clicked: int = Field(0, ge=0)
    emails_bounced: int = Field(0, ge=0)
    emails_unsubscribed: int = Field(0, ge=0)
    delivery_rate: float = Field(0.0, ge=0, le=100)
    open_rate: float = Field(0.0, ge=0, le=100)
    click_rate: float = Field(0.0, ge=0, le=100)
    bounce_rate: float = Field(0.0, ge=0, le=100)
    error_messages: List[str] = Field(default_factory=list)

    @field_validator("delivery_rate", "open_rate", "click_rate", "bounce_rate")
    @classmethod
    def round_rates(cls, v: float) -> float:
        """Round rates to 2 decimal places."""
        return round(v, 2)


class EmailCampaignListResponse(PaginatedResponse[EmailCampaign]):
    """Paginated email campaign list response."""

    pass


class EmailEvent(BaseSchema):
    """Email event tracking."""

    id: UUID
    campaign_id: UUID
    recipient_id: UUID
    event_type: str = Field(
        ..., description="Event type: sent, delivered, opened, clicked, bounced"
    )
    timestamp: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    url_clicked: Optional[str] = None
    bounce_reason: Optional[str] = None


class EmailPreference(BaseSchema):
    """User email preferences."""

    user_id: UUID
    receive_training_reminders: bool = Field(True)
    receive_security_alerts: bool = Field(True)
    receive_compliance_updates: bool = Field(True)
    receive_newsletters: bool = Field(True)
    unsubscribed_all: bool = Field(False)
    preferred_language: str = Field("de", max_length=2)
    updated_at: datetime


class EmailStatistics(BaseSchema):
    """Email campaign statistics summary."""

    total_campaigns: int = Field(0, ge=0)
    campaigns_last_30d: int = Field(0, ge=0)
    average_open_rate: float = Field(0.0, ge=0, le=100)
    average_click_rate: float = Field(0.0, ge=0, le=100)
    total_emails_sent: int = Field(0, ge=0)
    total_unsubscribes: int = Field(0, ge=0)
    most_effective_template: Optional[str] = None
    best_sending_time: Optional[str] = None
    delivery_issues: List[Dict[str, Any]] = Field(
        default_factory=list, description="Recent delivery issues"
    )