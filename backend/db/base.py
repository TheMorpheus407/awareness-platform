"""Database base configuration and imports."""

# Import the base class first
from models.base import Base

# Import all models here to ensure they are registered with SQLAlchemy
# This is important for Alembic migrations to detect all tables
from models.user import User  # noqa
from models.company import Company  # noqa
from models.course import Course, Quiz, QuizQuestion, UserCourseProgress  # noqa
from models.phishing import PhishingCampaign, PhishingTemplate, PhishingResult  # noqa
from models.audit import AuditLog, AuditAnalyticsEvent  # noqa

# This ensures all models are available
__all__ = [
    "Base",
    "User",
    "Company",
    "Course",
    "Quiz",
    "QuizQuestion",
    "UserCourseProgress",
    "PhishingCampaign",
    "PhishingTemplate",
    "PhishingResult",
    "AuditLog",
    "AuditAnalyticsEvent",
]