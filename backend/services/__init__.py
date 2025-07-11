"""
Services package for business logic implementation.

This package contains all service classes that implement the core business logic
of the Cybersecurity Awareness Platform. Services follow the dependency injection
pattern and are designed to be testable and loosely coupled.
"""

from .email import EmailService
from .email_service import ExtendedEmailService
from .email_template import EmailTemplateService
from .email_campaign import EmailCampaignService
from .email_scheduler import EmailSchedulerService
from .phishing_service import PhishingService
from .certificate_generator import CertificateGenerator
from .stripe_service import StripeService
from .analytics_collector import AnalyticsCollector
from .campaign_scheduler import CampaignScheduler
from .course_service import CourseService
from .quiz_service import QuizService
from .progress_service import ProgressService
from .gamification_service import GamificationService
from .notification_service import NotificationService, notification_service, notification_manager

# Conditional import of ContentDeliveryService due to boto3 dependency
try:
    from .content_delivery import ContentDeliveryService
except ImportError as e:
    import logging
    logging.warning(f"ContentDeliveryService not available: {str(e)}")
    ContentDeliveryService = None

__all__ = [
    "EmailService",
    "ExtendedEmailService",
    "EmailTemplateService",
    "EmailCampaignService",
    "EmailSchedulerService",
    "PhishingService",
    "CertificateGenerator",
    "ContentDeliveryService",
    "StripeService",
    "AnalyticsCollector",
    "CampaignScheduler",
    "CourseService",
    "QuizService",
    "ProgressService",
    "GamificationService",
    "NotificationService",
    "notification_service",
    "notification_manager",
]