"""Database models package."""

from .base import (
    Base,
    BaseModel,
    BaseUUIDModel,
    IntegerPrimaryKeyMixin,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    SoftDeleteMixin
)

# User and Company models
from .user import User, UserRole
from .company import Company, CompanySize, CompanyStatus, SubscriptionTier

# Course models
from .course import Course, Quiz, QuizQuestion, UserCourseProgress

# Phishing models
from .phishing import PhishingCampaign, PhishingTemplate, PhishingResult

# Analytics and Audit models
from .analytics import AnalyticsEvent
from .audit import AuditLog

# Payment models
from .payment import (
    Subscription,
    SubscriptionStatus,
    BillingInterval,
    PaymentMethod,
    PaymentMethodType,
    Invoice,
    InvoiceStatus,
    Payment,
    PaymentStatus,
    SubscriptionUsage
)

# Email campaign models
from .email_campaign import (
    EmailTemplate,
    EmailTemplateType,
    EmailCampaign,
    CampaignStatus,
    EmailLog,
    EmailStatus,
    EmailEvent,
    EmailPreferences,
    EmailFrequency,
    EmailBounce
)

# Authentication models
from .two_fa_attempt import TwoFAAttempt
from .password_reset_token import PasswordResetToken

# Re-export all models and enums
__all__ = [
    # Base classes
    "Base",
    "BaseModel",
    "BaseUUIDModel",
    "IntegerPrimaryKeyMixin",
    "UUIDPrimaryKeyMixin",
    "TimestampMixin",
    "SoftDeleteMixin",
    
    # User and Company
    "User",
    "UserRole",
    "Company",
    "CompanySize",
    "CompanyStatus",
    "SubscriptionTier",
    
    # Course
    "Course",
    "Quiz",
    "QuizQuestion",
    "UserCourseProgress",
    
    # Phishing
    "PhishingCampaign",
    "PhishingTemplate",
    "PhishingResult",
    
    # Analytics and Audit
    "AnalyticsEvent",
    "AuditLog",
    
    # Payment
    "Subscription",
    "SubscriptionStatus",
    "BillingInterval",
    "PaymentMethod",
    "PaymentMethodType",
    "Invoice",
    "InvoiceStatus",
    "Payment",
    "PaymentStatus",
    "SubscriptionUsage",
    
    # Email Campaign
    "EmailTemplate",
    "EmailTemplateType",
    "EmailCampaign",
    "CampaignStatus",
    "EmailLog",
    "EmailStatus",
    "EmailEvent",
    "EmailPreferences",
    "EmailFrequency",
    "EmailBounce",
    
    # Authentication
    "TwoFAAttempt",
    "PasswordResetToken",
]