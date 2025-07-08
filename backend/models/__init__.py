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
from .audit import AuditLog, AnalyticsEvent
from .two_fa_attempt import TwoFAAttempt
from .payment import (
    Subscription, SubscriptionStatus, BillingInterval,
    PaymentMethod, PaymentMethodType,
    Invoice, InvoiceStatus,
    Payment, PaymentStatus,
    SubscriptionUsage
)
from .analytics import (
    AnalyticsEvent as AnalyticsEventNew,
    CourseAnalytics, UserEngagement, RevenueAnalytics,
    PhishingAnalytics, RealtimeMetric
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
]