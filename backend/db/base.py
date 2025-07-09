"""Database base configuration and imports."""

# Import all SQLAlchemy models here to ensure they are registered
# with SQLAlchemy's base model class before creating database tables

from models.base import Base  # noqa
from models.user import User  # noqa
from models.company import Company  # noqa
from models.course import Course, Quiz, QuizQuestion, UserCourseProgress  # noqa
from models.phishing import PhishingCampaign, PhishingTemplate, PhishingResult  # noqa
from models.analytics import AnalyticsEvent  # noqa
from models.audit import AuditLog  # noqa
from models.payment import (  # noqa
    Subscription,
    PaymentMethod,
    Invoice,
    Payment,
    SubscriptionUsage,
)
from models.email_campaign import (  # noqa
    EmailTemplate,
    EmailCampaign,
    EmailLog,
    EmailEvent,
    EmailPreferences,
    EmailBounce,
)
from models.two_fa_attempt import TwoFAAttempt  # noqa
from models.password_reset_token import PasswordResetToken  # noqa

# Re-export Base for convenience
__all__ = ["Base"]