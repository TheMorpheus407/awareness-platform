"""Models package."""

from .user import User, UserRole
from .company import Company, CompanySize, CompanyStatus, SubscriptionTier
from .password_reset_token import PasswordResetToken
from .course import (
    Course, Module, Lesson, CourseContent,
    Quiz, QuizQuestion, QuizAttempt, QuizAnswer,
    CourseEnrollment, ModuleProgress, LessonProgress,
    CourseReview, CourseAnnouncement,
    UserCourseProgress,  # Backward compatibility
    ContentType, DifficultyLevel, CourseStatus, ProgressStatus
)
from .phishing import PhishingCampaign, PhishingTemplate, PhishingResult
from .audit import AuditLog, AuditAnalyticsEvent
from .two_fa_attempt import TwoFAAttempt
from .payment import (
    Subscription, SubscriptionStatus, BillingInterval,
    PaymentMethod, PaymentMethodType,
    Invoice, InvoiceStatus,
    Payment, PaymentStatus,
    SubscriptionUsage
)
from .analytics import (
    AnalyticsEvent,
    CourseAnalytics, UserEngagement, RevenueAnalytics,
    PhishingAnalytics, RealtimeMetric
)
from .email_campaign import (
    EmailTemplate, EmailTemplateType,
    EmailCampaign, CampaignStatus,
    EmailLog, EmailStatus,
    EmailEvent, EmailPreference, EmailFrequency,
    EmailBounce
)

__all__ = [
    "User",
    "UserRole",
    "Company",
    "CompanySize",
    "CompanyStatus",
    "SubscriptionTier",
    "PasswordResetToken",
    "Course",
    "Module",
    "Lesson",
    "CourseContent",
    "Quiz",
    "QuizQuestion",
    "QuizAttempt",
    "QuizAnswer",
    "CourseEnrollment",
    "ModuleProgress",
    "LessonProgress",
    "CourseReview",
    "CourseAnnouncement",
    "UserCourseProgress",
    "ContentType",
    "DifficultyLevel",
    "CourseStatus",
    "ProgressStatus",
    "PhishingCampaign",
    "PhishingTemplate",
    "PhishingResult",
    "AuditLog",
    "AnalyticsEvent",
    "TwoFAAttempt",
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
    "CourseAnalytics",
    "UserEngagement",
    "RevenueAnalytics",
    "PhishingAnalytics",
    "RealtimeMetric",
    "EmailTemplate",
    "EmailTemplateType",
    "EmailCampaign",
    "CampaignStatus",
    "EmailLog",
    "EmailStatus",
    "EmailEvent",
    "EmailPreference",
    "EmailFrequency",
    "EmailBounce",
]