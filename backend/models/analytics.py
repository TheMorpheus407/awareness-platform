"""Analytics event tracking model."""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSON

from .base import BaseModel

if TYPE_CHECKING:
    from .user import User
    from .company import Company


class AnalyticsEvent(BaseModel):
    """Analytics event model for tracking user activities and system events."""
    
    __tablename__ = "analytics_events"
    
    # Foreign Keys
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'), nullable=True, index=True)
    
    # Event Information
    event_type = Column(String(100), nullable=False, index=True)
    event_category = Column(String(100), nullable=False)
    event_data = Column(JSON, nullable=True)
    
    # Session Information
    session_id = Column(String(255), nullable=True)
    
    # Request Information
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Relationships
    user: Optional["User"] = relationship("User", back_populates="analytics_events")
    company: Optional["Company"] = relationship("Company", back_populates="analytics_events")
    
    # Common event types
    class EventType:
        # Authentication events
        LOGIN = "user.login"
        LOGOUT = "user.logout"
        LOGIN_FAILED = "user.login_failed"
        PASSWORD_RESET = "user.password_reset"
        PASSWORD_CHANGED = "user.password_changed"
        TWO_FA_ENABLED = "user.2fa_enabled"
        TWO_FA_DISABLED = "user.2fa_disabled"
        
        # Course events
        COURSE_STARTED = "course.started"
        COURSE_PROGRESS = "course.progress"
        COURSE_COMPLETED = "course.completed"
        QUIZ_STARTED = "quiz.started"
        QUIZ_COMPLETED = "quiz.completed"
        CERTIFICATE_ISSUED = "certificate.issued"
        
        # Phishing events
        PHISHING_CAMPAIGN_CREATED = "phishing.campaign_created"
        PHISHING_CAMPAIGN_STARTED = "phishing.campaign_started"
        PHISHING_CAMPAIGN_COMPLETED = "phishing.campaign_completed"
        PHISHING_EMAIL_SENT = "phishing.email_sent"
        PHISHING_EMAIL_OPENED = "phishing.email_opened"
        PHISHING_LINK_CLICKED = "phishing.link_clicked"
        PHISHING_DATA_SUBMITTED = "phishing.data_submitted"
        PHISHING_REPORTED = "phishing.reported"
        
        # Email campaign events
        EMAIL_CAMPAIGN_CREATED = "email.campaign_created"
        EMAIL_CAMPAIGN_SENT = "email.campaign_sent"
        EMAIL_OPENED = "email.opened"
        EMAIL_CLICKED = "email.clicked"
        EMAIL_UNSUBSCRIBED = "email.unsubscribed"
        
        # Company events
        COMPANY_CREATED = "company.created"
        COMPANY_UPDATED = "company.updated"
        COMPANY_SUBSCRIPTION_CHANGED = "company.subscription_changed"
        USER_INVITED = "company.user_invited"
        USER_REMOVED = "company.user_removed"
        
        # Payment events
        PAYMENT_INITIATED = "payment.initiated"
        PAYMENT_SUCCEEDED = "payment.succeeded"
        PAYMENT_FAILED = "payment.failed"
        SUBSCRIPTION_CREATED = "subscription.created"
        SUBSCRIPTION_UPDATED = "subscription.updated"
        SUBSCRIPTION_CANCELLED = "subscription.cancelled"
        
        # System events
        API_REQUEST = "system.api_request"
        ERROR_OCCURRED = "system.error"
        PERFORMANCE_ALERT = "system.performance_alert"
        SECURITY_ALERT = "system.security_alert"
    
    # Event categories
    class EventCategory:
        AUTHENTICATION = "authentication"
        COURSE = "course"
        PHISHING = "phishing"
        EMAIL = "email"
        COMPANY = "company"
        PAYMENT = "payment"
        SYSTEM = "system"
        USER_ACTIVITY = "user_activity"
    
    @classmethod
    def log_event(
        cls,
        event_type: str,
        event_category: str,
        user_id: Optional[int] = None,
        company_id: Optional[int] = None,
        event_data: Optional[dict] = None,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> "AnalyticsEvent":
        """
        Create and return a new analytics event.
        
        Note: This method creates the event instance but doesn't save it to the database.
        The caller is responsible for adding it to the session and committing.
        """
        return cls(
            event_type=event_type,
            event_category=event_category,
            user_id=user_id,
            company_id=company_id,
            event_data=event_data,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @classmethod
    def log_user_login(
        cls,
        user_id: int,
        company_id: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> "AnalyticsEvent":
        """Log a user login event."""
        return cls.log_event(
            event_type=cls.EventType.LOGIN,
            event_category=cls.EventCategory.AUTHENTICATION,
            user_id=user_id,
            company_id=company_id,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id
        )
    
    @classmethod
    def log_course_progress(
        cls,
        user_id: int,
        company_id: int,
        course_id: int,
        progress_percentage: int,
        session_id: Optional[str] = None
    ) -> "AnalyticsEvent":
        """Log course progress event."""
        return cls.log_event(
            event_type=cls.EventType.COURSE_PROGRESS,
            event_category=cls.EventCategory.COURSE,
            user_id=user_id,
            company_id=company_id,
            event_data={
                "course_id": course_id,
                "progress_percentage": progress_percentage
            },
            session_id=session_id
        )
    
    @classmethod
    def log_phishing_interaction(
        cls,
        user_id: int,
        company_id: int,
        campaign_id: int,
        interaction_type: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> "AnalyticsEvent":
        """Log phishing campaign interaction event."""
        event_type_map = {
            "opened": cls.EventType.PHISHING_EMAIL_OPENED,
            "clicked": cls.EventType.PHISHING_LINK_CLICKED,
            "submitted": cls.EventType.PHISHING_DATA_SUBMITTED,
            "reported": cls.EventType.PHISHING_REPORTED
        }
        
        return cls.log_event(
            event_type=event_type_map.get(interaction_type, cls.EventType.PHISHING_EMAIL_OPENED),
            event_category=cls.EventCategory.PHISHING,
            user_id=user_id,
            company_id=company_id,
            event_data={"campaign_id": campaign_id},
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    def __repr__(self) -> str:
        """String representation of AnalyticsEvent."""
        return f"<AnalyticsEvent {self.event_type} ({self.event_category})>"