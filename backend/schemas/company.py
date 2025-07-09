"""
Company-related schemas for the application.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import EmailStr, Field, field_validator

from .base import BaseSchema, PaginatedResponse, TimestampMixin, UUIDMixin


class CompanySize(str, Enum):
    """Company size categories."""

    SMALL = "small"  # < 50 employees
    MEDIUM = "medium"  # 50-250 employees
    LARGE = "large"  # 250-1000 employees
    ENTERPRISE = "enterprise"  # > 1000 employees


class ComplianceRequirement(str, Enum):
    """Compliance framework requirements."""

    NIS2 = "nis2"
    DSGVO = "dsgvo"
    ISO27001 = "iso27001"
    TISAX = "tisax"
    BAIT = "bait"
    KRITIS = "kritis"


class PhishingFrequency(str, Enum):
    """Phishing campaign frequency options."""

    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


class Language(str, Enum):
    """Supported languages."""

    DE = "de"
    EN = "en"
    FR = "fr"
    IT = "it"


class SubscriptionTier(str, Enum):
    """Subscription tier levels."""

    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class Company(BaseSchema, UUIDMixin, TimestampMixin):
    """Company response schema."""

    name: str = Field(..., min_length=2, max_length=255)
    domain: str = Field(..., max_length=255)
    industry: str = Field(..., max_length=100)
    size: CompanySize
    compliance_requirements: List[ComplianceRequirement] = Field(default_factory=list)
    subscription_tier: SubscriptionTier = Field(SubscriptionTier.FREE)
    is_active: bool = Field(True)
    employee_count: Optional[int] = Field(None, ge=1)

    @field_validator("domain")
    @classmethod
    def validate_domain(cls, v: str) -> str:
        """Ensure domain is lowercase and valid."""
        return v.lower()


class CompanyRegistration(BaseSchema):
    """Schema for company registration."""

    # Company information
    company_name: str = Field(..., min_length=2, max_length=255)
    company_domain: str = Field(
        ...,
        pattern=r"^[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}$",
        description="Company domain (e.g., company.com)",
    )
    industry: str = Field(..., min_length=2, max_length=100)
    size: CompanySize
    compliance_requirements: List[ComplianceRequirement] = Field(
        default_factory=list,
        description="List of compliance frameworks the company needs to follow",
    )

    # Admin user information
    admin_email: EmailStr = Field(..., description="Admin user email")
    admin_password: str = Field(
        ...,
        min_length=8,
        pattern=r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$",
        description="Password must contain uppercase, lowercase, number and special character",
    )
    admin_first_name: str = Field(..., min_length=1, max_length=100)
    admin_last_name: str = Field(..., min_length=1, max_length=100)

    @field_validator("admin_email")
    @classmethod
    def validate_admin_email_domain(cls, v: str, info) -> str:
        """Ensure admin email matches company domain."""
        if "company_domain" in info.data:
            email_domain = v.split("@")[1].lower()
            company_domain = info.data["company_domain"].lower()
            if not email_domain.endswith(company_domain):
                raise ValueError(
                    f"Admin email must use company domain @{company_domain}"
                )
        return v.lower()


class PasswordPolicy(BaseSchema):
    """Password policy configuration."""

    min_length: int = Field(8, ge=8, le=128)
    require_uppercase: bool = Field(True)
    require_lowercase: bool = Field(True)
    require_numbers: bool = Field(True)
    require_special: bool = Field(True)
    expiry_days: Optional[int] = Field(None, ge=1, le=365)
    history_count: int = Field(5, ge=0, le=24, description="Number of previous passwords to remember")
    max_age_days: Optional[int] = Field(90, ge=1, le=365)
    min_age_days: int = Field(1, ge=0, le=30)


class CompanySettings(BaseSchema):
    """Company settings and configuration."""

    phishing_frequency: PhishingFrequency = Field(PhishingFrequency.MONTHLY)
    reminder_days: List[int] = Field(
        default_factory=lambda: [7, 3, 1],
        description="Days before deadline to send reminders",
    )
    auto_assign_courses: bool = Field(
        True, description="Automatically assign mandatory courses to new users"
    )
    language: Language = Field(Language.DE)
    require_2fa: bool = Field(False, description="Require 2FA for all users")
    password_policy: PasswordPolicy = Field(default_factory=PasswordPolicy)
    session_timeout_minutes: int = Field(30, ge=5, le=480)
    allowed_email_domains: List[str] = Field(
        default_factory=list,
        description="Additional allowed email domains for users",
    )
    training_completion_deadline_days: int = Field(
        30, ge=7, le=90, description="Default deadline for training completion"
    )
    phishing_training_redirect_url: Optional[str] = Field(
        None, description="Custom URL for phishing training redirect"
    )

    @field_validator("reminder_days")
    @classmethod
    def validate_reminder_days(cls, v: List[int]) -> List[int]:
        """Ensure reminder days are positive and sorted."""
        if not v:
            return []
        # Remove duplicates and sort descending
        unique_days = sorted(set(d for d in v if d > 0), reverse=True)
        return unique_days[:10]  # Limit to 10 reminders


class CompanySettingsUpdate(BaseSchema):
    """Schema for updating company settings."""

    phishing_frequency: Optional[PhishingFrequency] = None
    reminder_days: Optional[List[int]] = None
    auto_assign_courses: Optional[bool] = None
    language: Optional[Language] = None
    require_2fa: Optional[bool] = None
    password_policy: Optional[PasswordPolicy] = None
    session_timeout_minutes: Optional[int] = Field(None, ge=5, le=480)
    allowed_email_domains: Optional[List[str]] = None
    training_completion_deadline_days: Optional[int] = Field(None, ge=7, le=90)
    phishing_training_redirect_url: Optional[str] = None


class CompanyListResponse(PaginatedResponse[Company]):
    """Paginated company list response."""

    pass


class CompanyStats(BaseSchema):
    """Company statistics summary."""

    company_id: UUID
    total_users: int = Field(0, ge=0)
    active_users: int = Field(0, ge=0)
    average_risk_score: float = Field(50.0, ge=0, le=100)
    high_risk_users: int = Field(0, ge=0)
    courses_available: int = Field(0, ge=0)
    average_completion_rate: float = Field(0.0, ge=0, le=100)
    phishing_campaigns_total: int = Field(0, ge=0)
    phishing_click_rate: float = Field(0.0, ge=0, le=100)
    last_updated: datetime


class CompanyInvitation(BaseSchema):
    """Company invitation for new registrations."""

    id: UUID
    company_name: str
    inviter_email: EmailStr
    invitee_email: EmailStr
    token: str
    expires_at: datetime
    accepted: bool = False
    created_at: datetime