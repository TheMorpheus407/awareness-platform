"""Email campaign, template, and tracking models."""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, ENUM, JSON
import uuid

from .base import BaseUUIDModel

if TYPE_CHECKING:
    from .user import User
    from .company import Company


class EmailTemplateType:
    """Email template type enumeration."""
    
    TRANSACTIONAL = "transactional"
    CAMPAIGN = "campaign"
    NEWSLETTER = "newsletter"
    NOTIFICATION = "notification"
    WELCOME = "welcome"
    COURSE_UPDATE = "course_update"
    PHISHING_ALERT = "phishing_alert"
    SECURITY_ALERT = "security_alert"


class CampaignStatus:
    """Campaign status enumeration."""
    
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    SENDING = "sending"
    SENT = "sent"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class EmailStatus:
    """Email delivery status enumeration."""
    
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    BOUNCED = "bounced"
    FAILED = "failed"
    UNSUBSCRIBED = "unsubscribed"
    MARKED_SPAM = "marked_spam"


class EmailFrequency:
    """Email frequency preference enumeration."""
    
    IMMEDIATELY = "immediately"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    NEVER = "never"


class EmailTemplate(BaseUUIDModel):
    """Email template model for reusable email content."""
    
    __tablename__ = "email_templates"
    
    # Basic Information
    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, unique=True, index=True)
    type = Column(
        ENUM('transactional', 'campaign', 'newsletter', 'notification', 'welcome', 'course_update', 'phishing_alert', 'security_alert', name='emailtemplatetype', create_type=False),
        nullable=False
    )
    
    # Email Content
    subject = Column(String(500), nullable=False)
    html_content = Column(Text, nullable=False)
    text_content = Column(Text, nullable=True)
    preview_text = Column(String(500), nullable=True)
    
    # Template Variables
    variables = Column(JSON, nullable=True)  # List of variable names and descriptions
    
    # Sender Information
    from_name = Column(String(255), nullable=True)
    from_email = Column(String(255), nullable=True)
    reply_to = Column(String(255), nullable=True)
    
    # Status and Settings
    is_active = Column(Boolean, nullable=True, default=True)
    is_default = Column(Boolean, nullable=True, default=False)
    
    # Creator
    created_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Statistics
    total_sent = Column(Integer, nullable=True, default=0)
    total_opened = Column(Integer, nullable=True, default=0)
    total_clicked = Column(Integer, nullable=True, default=0)
    avg_open_rate = Column(Float, nullable=True, default=0.0)
    avg_click_rate = Column(Float, nullable=True, default=0.0)
    
    # Relationships
    created_by: Optional["User"] = relationship("User", back_populates="created_email_templates")
    campaigns: List["EmailCampaign"] = relationship("EmailCampaign", back_populates="template")
    email_logs: List["EmailLog"] = relationship("EmailLog", back_populates="template")
    
    def update_statistics(self) -> None:
        """Update template statistics based on email logs."""
        if not self.email_logs:
            return
        
        total_sent = len([log for log in self.email_logs if log.sent_at])
        total_opened = len([log for log in self.email_logs if log.opened_at])
        total_clicked = len([log for log in self.email_logs if log.clicked_at])
        
        self.total_sent = total_sent
        self.total_opened = total_opened
        self.total_clicked = total_clicked
        
        if total_sent > 0:
            self.avg_open_rate = (total_opened / total_sent) * 100
            self.avg_click_rate = (total_clicked / total_sent) * 100
    
    def __repr__(self) -> str:
        """String representation of EmailTemplate."""
        return f"<EmailTemplate {self.name} ({self.type})>"


class EmailCampaign(BaseUUIDModel):
    """Email campaign model for marketing and communication campaigns."""
    
    __tablename__ = "email_campaigns"
    
    # Basic Information
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Foreign Keys
    template_id = Column(UUID(as_uuid=True), ForeignKey('email_templates.id'), nullable=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=True)
    created_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Campaign Status
    status = Column(
        ENUM('draft', 'scheduled', 'sending', 'sent', 'paused', 'cancelled', 'completed', name='campaignstatus', create_type=False),
        nullable=True,
        default='draft'
    )
    
    # Scheduling
    scheduled_at = Column(DateTime(timezone=True), nullable=True, index=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Targeting
    target_all_users = Column(Boolean, nullable=True, default=False)
    target_user_roles = Column(JSON, nullable=True)  # List of user roles
    target_user_ids = Column(JSON, nullable=True)  # List of specific user IDs
    target_segments = Column(JSON, nullable=True)  # Custom segments/filters
    exclude_unsubscribed = Column(Boolean, nullable=True, default=True)
    
    # Custom Content
    custom_subject = Column(String(500), nullable=True)
    custom_preview_text = Column(String(500), nullable=True)
    custom_variables = Column(JSON, nullable=True)  # Variable values for template
    
    # Statistics
    total_recipients = Column(Integer, nullable=True, default=0)
    total_sent = Column(Integer, nullable=True, default=0)
    total_delivered = Column(Integer, nullable=True, default=0)
    total_opened = Column(Integer, nullable=True, default=0)
    total_clicked = Column(Integer, nullable=True, default=0)
    total_bounced = Column(Integer, nullable=True, default=0)
    total_unsubscribed = Column(Integer, nullable=True, default=0)
    
    # Rates
    delivery_rate = Column(Float, nullable=True, default=0.0)
    open_rate = Column(Float, nullable=True, default=0.0)
    click_rate = Column(Float, nullable=True, default=0.0)
    bounce_rate = Column(Float, nullable=True, default=0.0)
    unsubscribe_rate = Column(Float, nullable=True, default=0.0)
    
    # Relationships
    template: Optional["EmailTemplate"] = relationship("EmailTemplate", back_populates="campaigns")
    company: Optional["Company"] = relationship("Company", back_populates="email_campaigns")
    created_by: Optional["User"] = relationship("User", back_populates="created_email_campaigns")
    email_logs: List["EmailLog"] = relationship(
        "EmailLog",
        back_populates="campaign",
        cascade="all, delete-orphan"
    )
    
    @property
    def is_draft(self) -> bool:
        """Check if campaign is in draft status."""
        return self.status == CampaignStatus.DRAFT
    
    @property
    def is_scheduled(self) -> bool:
        """Check if campaign is scheduled."""
        return self.status == CampaignStatus.SCHEDULED
    
    @property
    def is_active(self) -> bool:
        """Check if campaign is currently active."""
        return self.status in [CampaignStatus.SENDING, CampaignStatus.SENT]
    
    @property
    def is_completed(self) -> bool:
        """Check if campaign is completed."""
        return self.status == CampaignStatus.COMPLETED
    
    def update_statistics(self) -> None:
        """Update campaign statistics based on email logs."""
        if not self.email_logs:
            return
        
        self.total_recipients = len(self.email_logs)
        self.total_sent = len([log for log in self.email_logs if log.sent_at])
        self.total_delivered = len([log for log in self.email_logs if log.delivered_at])
        self.total_opened = len([log for log in self.email_logs if log.opened_at])
        self.total_clicked = len([log for log in self.email_logs if log.clicked_at])
        self.total_bounced = len([log for log in self.email_logs if log.bounced_at])
        self.total_unsubscribed = len([log for log in self.email_logs if log.unsubscribed_at])
        
        if self.total_sent > 0:
            self.delivery_rate = (self.total_delivered / self.total_sent) * 100
            self.open_rate = (self.total_opened / self.total_sent) * 100
            self.click_rate = (self.total_clicked / self.total_sent) * 100
            self.bounce_rate = (self.total_bounced / self.total_sent) * 100
            self.unsubscribe_rate = (self.total_unsubscribed / self.total_sent) * 100
    
    def __repr__(self) -> str:
        """String representation of EmailCampaign."""
        return f"<EmailCampaign {self.name} ({self.status})>"


class EmailLog(BaseUUIDModel):
    """Email log model for tracking individual email deliveries."""
    
    __tablename__ = "email_logs"
    
    # Foreign Keys
    campaign_id = Column(UUID(as_uuid=True), ForeignKey('email_campaigns.id'), nullable=True)
    template_id = Column(UUID(as_uuid=True), ForeignKey('email_templates.id'), nullable=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True, index=True)
    
    # Email Information
    to_email = Column(String(255), nullable=False)
    from_email = Column(String(255), nullable=False)
    subject = Column(String(500), nullable=False)
    
    # Delivery Status
    status = Column(
        ENUM('pending', 'sent', 'delivered', 'opened', 'clicked', 'bounced', 'failed', 'unsubscribed', 'marked_spam', name='emailstatus', create_type=False),
        nullable=True,
        default='pending'
    )
    
    # Timestamps
    sent_at = Column(DateTime(timezone=True), nullable=True, index=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    opened_at = Column(DateTime(timezone=True), nullable=True)
    first_opened_at = Column(DateTime(timezone=True), nullable=True)
    clicked_at = Column(DateTime(timezone=True), nullable=True)
    first_clicked_at = Column(DateTime(timezone=True), nullable=True)
    bounced_at = Column(DateTime(timezone=True), nullable=True)
    unsubscribed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Interaction Counts
    open_count = Column(Integer, nullable=True, default=0)
    click_count = Column(Integer, nullable=True, default=0)
    clicked_links = Column(JSON, nullable=True)  # List of clicked URLs
    
    # Error Information
    error_message = Column(Text, nullable=True)
    bounce_type = Column(String(50), nullable=True)  # hard, soft, etc.
    
    # Provider Information
    provider = Column(String(50), nullable=True)  # sendgrid, ses, etc.
    message_id = Column(String(255), nullable=True, index=True)
    
    # Relationships
    campaign: Optional["EmailCampaign"] = relationship("EmailCampaign", back_populates="email_logs")
    template: Optional["EmailTemplate"] = relationship("EmailTemplate", back_populates="email_logs")
    user: Optional["User"] = relationship("User", back_populates="email_logs")
    events: List["EmailEvent"] = relationship(
        "EmailEvent",
        back_populates="email_log",
        cascade="all, delete-orphan"
    )
    
    @property
    def was_delivered(self) -> bool:
        """Check if email was delivered."""
        return self.delivered_at is not None
    
    @property
    def was_opened(self) -> bool:
        """Check if email was opened."""
        return self.opened_at is not None
    
    @property
    def was_clicked(self) -> bool:
        """Check if email was clicked."""
        return self.clicked_at is not None
    
    @property
    def was_bounced(self) -> bool:
        """Check if email bounced."""
        return self.bounced_at is not None
    
    def record_open(self, timestamp: Optional[datetime] = None) -> None:
        """Record an email open event."""
        timestamp = timestamp or datetime.utcnow()
        self.open_count += 1
        self.opened_at = timestamp
        if not self.first_opened_at:
            self.first_opened_at = timestamp
        self.status = EmailStatus.OPENED
    
    def record_click(self, url: str, timestamp: Optional[datetime] = None) -> None:
        """Record an email click event."""
        timestamp = timestamp or datetime.utcnow()
        self.click_count += 1
        self.clicked_at = timestamp
        if not self.first_clicked_at:
            self.first_clicked_at = timestamp
        
        if not self.clicked_links:
            self.clicked_links = []
        if url not in self.clicked_links:
            self.clicked_links.append(url)
        
        self.status = EmailStatus.CLICKED
    
    def __repr__(self) -> str:
        """String representation of EmailLog."""
        return f"<EmailLog {self.to_email} ({self.status})>"


class EmailEvent(BaseUUIDModel):
    """Email event model for tracking detailed email interactions."""
    
    __tablename__ = "email_events"
    
    # Foreign Keys
    email_log_id = Column(UUID(as_uuid=True), ForeignKey('email_logs.id'), nullable=False, index=True)
    
    # Event Information
    event_type = Column(String(50), nullable=False)  # open, click, bounce, etc.
    timestamp = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # Client Information
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    location = Column(JSON, nullable=True)  # GeoIP data
    
    # Device Information
    device_type = Column(String(50), nullable=True)  # desktop, mobile, tablet
    os = Column(String(50), nullable=True)
    browser = Column(String(50), nullable=True)
    
    # Click Information
    clicked_url = Column(Text, nullable=True)
    click_position = Column(Integer, nullable=True)  # Position of link in email
    
    # Bounce Information
    bounce_reason = Column(Text, nullable=True)
    
    # Relationships
    email_log: "EmailLog" = relationship("EmailLog", back_populates="events")
    
    def __repr__(self) -> str:
        """String representation of EmailEvent."""
        return f"<EmailEvent {self.event_type} ({self.timestamp})>"


class EmailPreferences(BaseUUIDModel):
    """Email preferences model for user subscription settings."""
    
    __tablename__ = "email_preferences"
    __table_args__ = (
        UniqueConstraint('user_id', name='uq_email_preferences_user'),
        UniqueConstraint('unsubscribe_token', name='uq_email_preferences_token'),
    )
    
    # Foreign Keys
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # Global Subscription
    is_subscribed = Column(Boolean, nullable=True, default=True)
    unsubscribed_at = Column(DateTime(timezone=True), nullable=True)
    unsubscribe_token = Column(String(255), nullable=True, index=True)
    
    # Email Categories
    marketing_emails = Column(Boolean, nullable=True, default=True)
    course_updates = Column(Boolean, nullable=True, default=True)
    security_alerts = Column(Boolean, nullable=True, default=True)
    newsletter = Column(Boolean, nullable=True, default=True)
    promotional = Column(Boolean, nullable=True, default=True)
    
    # Frequency Settings
    email_frequency = Column(
        ENUM('immediately', 'daily', 'weekly', 'monthly', 'never', name='emailfrequency', create_type=False),
        nullable=True,
        default='immediately'
    )
    digest_day = Column(Integer, nullable=True)  # 0-6 (Monday-Sunday)
    digest_hour = Column(Integer, nullable=True, default=9)  # 0-23
    
    # Relationships
    user: "User" = relationship("User", back_populates="email_preferences", uselist=False)
    
    def unsubscribe_all(self) -> None:
        """Unsubscribe from all email communications."""
        self.is_subscribed = False
        self.unsubscribed_at = datetime.utcnow()
        self.marketing_emails = False
        self.course_updates = False
        self.security_alerts = False
        self.newsletter = False
        self.promotional = False
    
    def can_receive_email(self, email_type: EmailTemplateType) -> bool:
        """Check if user can receive a specific type of email."""
        if not self.is_subscribed:
            return False
        
        # Security alerts always go through if user is subscribed
        if email_type == EmailTemplateType.SECURITY_ALERT:
            return self.security_alerts
        
        # Map email types to preferences
        type_map = {
            EmailTemplateType.CAMPAIGN: self.marketing_emails,
            EmailTemplateType.NEWSLETTER: self.newsletter,
            EmailTemplateType.COURSE_UPDATE: self.course_updates,
            EmailTemplateType.PHISHING_ALERT: self.security_alerts,
            EmailTemplateType.NOTIFICATION: True,  # Always allow notifications
            EmailTemplateType.TRANSACTIONAL: True,  # Always allow transactional
            EmailTemplateType.WELCOME: True,  # Always allow welcome emails
        }
        
        return type_map.get(email_type, True)
    
    def __repr__(self) -> str:
        """String representation of EmailPreferences."""
        return f"<EmailPreferences User:{self.user_id} (Subscribed: {self.is_subscribed})>"


class EmailBounce(BaseUUIDModel):
    """Email bounce tracking model for managing suppression list."""
    
    __tablename__ = "email_bounces"
    __table_args__ = (
        UniqueConstraint('email', name='uq_email_bounce_email'),
    )
    
    # Email Information
    email = Column(String(255), nullable=False, index=True)
    bounce_type = Column(String(50), nullable=False)  # hard, soft, complaint
    
    # Bounce Tracking
    bounce_count = Column(Integer, nullable=True, default=1)
    last_bounce_at = Column(DateTime(timezone=True), nullable=True)
    
    # Suppression
    is_suppressed = Column(Boolean, nullable=True, default=False, index=True)
    suppressed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Additional Information
    reason = Column(Text, nullable=True)
    diagnostic_code = Column(Text, nullable=True)
    
    @property
    def should_suppress(self) -> bool:
        """Check if email should be suppressed based on bounce history."""
        if self.is_suppressed:
            return True
        
        # Hard bounces = immediate suppression
        if self.bounce_type == 'hard':
            return True
        
        # Soft bounces = suppress after 3 attempts
        if self.bounce_type == 'soft' and self.bounce_count >= 3:
            return True
        
        # Complaints = immediate suppression
        if self.bounce_type == 'complaint':
            return True
        
        return False
    
    def record_bounce(self, bounce_type: Optional[str] = None) -> None:
        """Record a new bounce event."""
        self.bounce_count += 1
        self.last_bounce_at = datetime.utcnow()
        if bounce_type:
            self.bounce_type = bounce_type
        
        if self.should_suppress:
            self.is_suppressed = True
            self.suppressed_at = datetime.utcnow()
    
    def __repr__(self) -> str:
        """String representation of EmailBounce."""
        return f"<EmailBounce {self.email} ({self.bounce_type})>"