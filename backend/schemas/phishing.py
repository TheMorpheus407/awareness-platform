"""
Phishing simulation and campaign-related schemas.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import Field, field_validator

from .base import BaseSchema, PaginatedResponse, TimestampMixin, UUIDMixin


class PhishingDifficulty(str, Enum):
    """Phishing template difficulty levels."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


class PhishingCategory(str, Enum):
    """Phishing attack categories."""

    CREDENTIAL = "credential"  # Credential harvesting
    ATTACHMENT = "attachment"  # Malicious attachment
    LINK = "link"  # Malicious link
    MIXED = "mixed"  # Combination of techniques


class CampaignStatus(str, Enum):
    """Phishing campaign status."""

    DRAFT = "draft"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PhishingRedFlag(BaseSchema):
    """Red flag indicator in phishing template."""

    type: str = Field(..., description="Type of red flag (e.g., 'sender', 'urgency')")
    description: str = Field(..., description="Description of the red flag")
    severity: str = Field(
        "medium", description="Severity level", pattern="^(low|medium|high)$"
    )


class PhishingTemplate(BaseSchema, UUIDMixin):
    """Phishing email template."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., max_length=1000)
    category: PhishingCategory
    difficulty: PhishingDifficulty
    subject: str = Field(..., min_length=1, max_length=255)
    sender_name: str = Field(..., min_length=1, max_length=100)
    sender_email: str = Field(..., max_length=255)
    preview: str = Field(..., max_length=500, description="Email preview text")
    html_content: Optional[str] = Field(None, description="HTML email content")
    text_content: str = Field(..., description="Plain text email content")
    red_flags: List[PhishingRedFlag] = Field(
        default_factory=list, description="Red flags to educate users"
    )
    language: str = Field("de", max_length=2)
    is_active: bool = Field(True)
    success_rate: Optional[float] = Field(
        None, ge=0, le=100, description="Historical success rate"
    )
    tags: List[str] = Field(default_factory=list)

    @field_validator("sender_email")
    @classmethod
    def validate_sender_email(cls, v: str) -> str:
        """Ensure sender email doesn't use real company domains."""
        blocked_domains = ["microsoft.com", "google.com", "apple.com", "amazon.com"]
        domain = v.split("@")[-1].lower()
        if any(blocked in domain for blocked in blocked_domains):
            raise ValueError("Cannot use real company domains in phishing templates")
        return v.lower()


class Campaign(BaseSchema, UUIDMixin, TimestampMixin):
    """Phishing campaign summary."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    template_id: UUID
    status: CampaignStatus = Field(CampaignStatus.DRAFT)
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_recipients: int = Field(0, ge=0)
    track_duration_days: int = Field(7, ge=1, le=30)
    company_id: UUID


class CampaignCreate(BaseSchema):
    """Schema for creating a phishing campaign."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    template_id: UUID
    target_groups: List[str] = Field(
        ...,
        min_length=1,
        description="Target groups (e.g., 'all', 'department:IT', 'role:manager')",
    )
    excluded_users: List[UUID] = Field(
        default_factory=list, description="User IDs to exclude"
    )
    scheduled_at: Optional[datetime] = Field(
        None, description="When to launch the campaign"
    )
    track_duration_days: int = Field(
        7, ge=1, le=30, description="How long to track interactions"
    )
    landing_page_url: Optional[str] = Field(
        None, description="Custom landing page for clicked links"
    )
    send_training_on_failure: bool = Field(
        True, description="Auto-assign training for users who click"
    )

    @field_validator("target_groups")
    @classmethod
    def validate_target_groups(cls, v: List[str]) -> List[str]:
        """Validate target group format."""
        valid_prefixes = ["all", "department:", "role:", "risk_score:"]
        for group in v:
            if not any(group.startswith(prefix) for prefix in valid_prefixes):
                raise ValueError(
                    f"Invalid target group: {group}. Must start with one of: {valid_prefixes}"
                )
        return v

    @field_validator("scheduled_at")
    @classmethod
    def validate_scheduled_at(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Ensure scheduled time is in the future."""
        if v and v <= datetime.utcnow():
            raise ValueError("Scheduled time must be in the future")
        return v


class CampaignDetail(Campaign):
    """Detailed campaign information with statistics."""

    template: PhishingTemplate
    emails_sent: int = Field(0, ge=0)
    emails_delivered: int = Field(0, ge=0)
    emails_opened: int = Field(0, ge=0)
    links_clicked: int = Field(0, ge=0)
    data_submitted: int = Field(0, ge=0)
    reported_suspicious: int = Field(0, ge=0)
    delivery_rate: float = Field(0.0, ge=0, le=100)
    open_rate: float = Field(0.0, ge=0, le=100)
    click_rate: float = Field(0.0, ge=0, le=100)
    report_rate: float = Field(0.0, ge=0, le=100)
    training_completed: int = Field(0, ge=0)


class UserPhishingResult(BaseSchema):
    """Individual user result for a phishing campaign."""

    user_id: UUID
    email: str
    first_name: str
    last_name: str
    department: Optional[str]
    role: str
    email_sent_at: Optional[datetime]
    email_opened: bool = False
    email_opened_at: Optional[datetime]
    link_clicked: bool = False
    link_clicked_at: Optional[datetime]
    data_submitted: bool = False
    data_submitted_at: Optional[datetime]
    reported_suspicious: bool = False
    reported_at: Optional[datetime]
    time_to_click: Optional[str] = Field(
        None, description="Time between send and click"
    )
    risk_score_before: float = Field(50.0, ge=0, le=100)
    risk_score_after: float = Field(50.0, ge=0, le=100)
    training_assigned: bool = False
    training_completed: bool = False
    training_completed_at: Optional[datetime]


class CampaignSummary(BaseSchema):
    """Campaign results summary."""

    click_rate: float = Field(..., ge=0, le=100)
    report_rate: float = Field(..., ge=0, le=100)
    average_time_to_click: Optional[str] = None
    risk_score_impact: float = Field(
        ..., description="Average change in risk scores"
    )
    department_breakdown: List[Dict[str, float]] = Field(
        default_factory=list, description="Click rates by department"
    )
    improvement_from_previous: Optional[float] = Field(
        None, description="Improvement from previous campaign"
    )


class CampaignResults(BaseSchema):
    """Complete campaign results."""

    campaign: CampaignDetail
    summary: CampaignSummary
    user_results: List[UserPhishingResult]
    recommendations: List[str] = Field(
        default_factory=list, description="Recommended actions based on results"
    )


class CampaignListResponse(PaginatedResponse[Campaign]):
    """Paginated campaign list response."""

    pass


class PhishingInteraction(BaseSchema):
    """Track user interaction with phishing email."""

    tracking_id: UUID
    interaction_type: str = Field(
        ..., description="Type: opened, clicked, submitted, reported"
    )
    timestamp: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None


class PhishingReport(BaseSchema):
    """User report of suspicious email."""

    user_id: UUID
    campaign_id: Optional[UUID] = None
    tracking_id: Optional[UUID] = None
    reported_at: datetime
    email_subject: str
    email_sender: str
    reason: Optional[str] = Field(None, max_length=500)
    was_legitimate_phishing: bool = Field(
        False, description="Was this an actual phishing simulation"
    )


class PhishingStatistics(BaseSchema):
    """Organization-wide phishing statistics."""

    total_campaigns: int = Field(0, ge=0)
    active_campaigns: int = Field(0, ge=0)
    average_click_rate: float = Field(0.0, ge=0, le=100)
    average_report_rate: float = Field(0.0, ge=0, le=100)
    click_rate_trend: str = Field(
        "stable", description="improving, stable, or declining"
    )
    most_vulnerable_department: Optional[str] = None
    most_successful_category: Optional[PhishingCategory] = None
    users_never_clicked: int = Field(0, ge=0)
    users_always_report: int = Field(0, ge=0)