"""Email campaign models."""

from __future__ import annotations
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import uuid

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, JSON,
    ForeignKey, UniqueConstraint, Index, Float, Enum as SQLEnum
)
from sqlalchemy.orm import relationship, backref
from sqlalchemy.dialects.postgresql import UUID

from db.base_class import Base


class EmailTemplateType(str, Enum):
    """Email template types."""
    TRANSACTIONAL = "transactional"
    CAMPAIGN = "campaign"
    NEWSLETTER = "newsletter"
    NOTIFICATION = "notification"
    WELCOME = "welcome"
    COURSE_UPDATE = "course_update"
    PHISHING_ALERT = "phishing_alert"
    SECURITY_ALERT = "security_alert"


class EmailStatus(str, Enum):
    """Email send status."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    BOUNCED = "bounced"
    FAILED = "failed"
    UNSUBSCRIBED = "unsubscribed"
    MARKED_SPAM = "marked_spam"


class CampaignStatus(str, Enum):
    """Campaign status."""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    SENDING = "sending"
    SENT = "sent"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class EmailFrequency(str, Enum):
    """Email frequency preferences."""
    IMMEDIATELY = "immediately"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    NEVER = "never"


class EmailTemplate(Base):
    """Email template model."""
    __tablename__ = "email_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False)
    type = Column(SQLEnum(EmailTemplateType), nullable=False)
    subject = Column(String(500), nullable=False)
    html_content = Column(Text, nullable=False)
    text_content = Column(Text)
    variables = Column(JSON, default=dict)  # List of template variables
    preview_text = Column(String(500))
    from_name = Column(String(255))
    from_email = Column(String(255))
    reply_to = Column(String(255))
    
    # Metadata
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Performance tracking
    total_sent = Column(Integer, default=0)
    total_opened = Column(Integer, default=0)
    total_clicked = Column(Integer, default=0)
    avg_open_rate = Column(Float, default=0.0)
    avg_click_rate = Column(Float, default=0.0)
    
    # Relationships
    created_by = relationship("User", backref="created_email_templates")
    campaigns = relationship("EmailCampaign", back_populates="template")
    
    # Indexes
    __table_args__ = (
        Index("idx_email_template_type_active", "type", "is_active"),
        Index("idx_email_template_slug", "slug"),
    )


class EmailCampaign(Base):
    """Email campaign model."""
    __tablename__ = "email_campaigns"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    template_id = Column(UUID(as_uuid=True), ForeignKey("email_templates.id"))
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"))
    
    # Campaign settings
    status = Column(SQLEnum(CampaignStatus), default=CampaignStatus.DRAFT)
    scheduled_at = Column(DateTime)
    sent_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Targeting
    target_all_users = Column(Boolean, default=False)
    target_user_roles = Column(JSON, default=list)  # List of roles
    target_user_ids = Column(JSON, default=list)  # Specific user IDs
    target_segments = Column(JSON, default=dict)  # Custom segments
    exclude_unsubscribed = Column(Boolean, default=True)
    
    # Content customization
    custom_subject = Column(String(500))
    custom_preview_text = Column(String(500))
    custom_variables = Column(JSON, default=dict)
    
    # Performance tracking
    total_recipients = Column(Integer, default=0)
    total_sent = Column(Integer, default=0)
    total_delivered = Column(Integer, default=0)
    total_opened = Column(Integer, default=0)
    total_clicked = Column(Integer, default=0)
    total_bounced = Column(Integer, default=0)
    total_unsubscribed = Column(Integer, default=0)
    
    # Rates
    delivery_rate = Column(Float, default=0.0)
    open_rate = Column(Float, default=0.0)
    click_rate = Column(Float, default=0.0)
    bounce_rate = Column(Float, default=0.0)
    unsubscribe_rate = Column(Float, default=0.0)
    
    # Metadata
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    template = relationship("EmailTemplate", back_populates="campaigns")
    company = relationship("Company", backref="email_campaigns")
    created_by = relationship("User", backref="created_campaigns")
    emails = relationship("EmailLog", back_populates="campaign", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_campaign_status_company", "status", "company_id"),
        Index("idx_campaign_scheduled", "scheduled_at", "status"),
    )


class EmailLog(Base):
    """Email send log."""
    __tablename__ = "email_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("email_campaigns.id"))
    template_id = Column(UUID(as_uuid=True), ForeignKey("email_templates.id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Email details
    to_email = Column(String(255), nullable=False)
    from_email = Column(String(255), nullable=False)
    subject = Column(String(500), nullable=False)
    status = Column(SQLEnum(EmailStatus), default=EmailStatus.PENDING)
    
    # Tracking
    sent_at = Column(DateTime)
    delivered_at = Column(DateTime)
    opened_at = Column(DateTime)
    first_opened_at = Column(DateTime)
    clicked_at = Column(DateTime)
    first_clicked_at = Column(DateTime)
    bounced_at = Column(DateTime)
    unsubscribed_at = Column(DateTime)
    
    # Tracking details
    open_count = Column(Integer, default=0)
    click_count = Column(Integer, default=0)
    clicked_links = Column(JSON, default=list)  # List of clicked link URLs
    
    # Error handling
    error_message = Column(Text)
    bounce_type = Column(String(50))  # hard, soft, etc.
    
    # Email provider details
    provider = Column(String(50))  # smtp, sendgrid, ses, etc.
    message_id = Column(String(255))  # Provider's message ID
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    campaign = relationship("EmailCampaign", back_populates="emails")
    template = relationship("EmailTemplate")
    user = relationship("User", backref="email_logs")
    events = relationship("EmailEvent", back_populates="email_log", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_email_log_user_status", "user_id", "status"),
        Index("idx_email_log_campaign_status", "campaign_id", "status"),
        Index("idx_email_log_sent_at", "sent_at"),
        Index("idx_email_log_message_id", "message_id"),
    )


class EmailEvent(Base):
    """Email event tracking."""
    __tablename__ = "email_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email_log_id = Column(UUID(as_uuid=True), ForeignKey("email_logs.id"), nullable=False)
    event_type = Column(String(50), nullable=False)  # open, click, bounce, etc.
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Event details
    ip_address = Column(String(45))
    user_agent = Column(Text)
    location = Column(JSON)  # GeoIP data
    device_type = Column(String(50))  # desktop, mobile, tablet
    os = Column(String(50))
    browser = Column(String(50))
    
    # Click specific
    clicked_url = Column(Text)
    click_position = Column(Integer)  # Position of link in email
    
    # Bounce specific
    bounce_reason = Column(Text)
    
    # Relationships
    email_log = relationship("EmailLog", back_populates="events")
    
    # Indexes
    __table_args__ = (
        Index("idx_email_event_log_type", "email_log_id", "event_type"),
        Index("idx_email_event_timestamp", "timestamp"),
    )


class EmailPreference(Base):
    """User email preferences."""
    __tablename__ = "email_preferences"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    
    # Global preferences
    is_subscribed = Column(Boolean, default=True)
    unsubscribed_at = Column(DateTime)
    unsubscribe_token = Column(String(255), unique=True)
    
    # Category preferences
    marketing_emails = Column(Boolean, default=True)
    course_updates = Column(Boolean, default=True)
    security_alerts = Column(Boolean, default=True)
    newsletter = Column(Boolean, default=True)
    promotional = Column(Boolean, default=True)
    
    # Frequency preferences
    email_frequency = Column(SQLEnum(EmailFrequency), default=EmailFrequency.IMMEDIATELY)
    digest_day = Column(Integer)  # 0-6 for weekly digest
    digest_hour = Column(Integer, default=9)  # Hour of day for digest
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", backref=backref("email_preference", uselist=False))
    
    # Indexes
    __table_args__ = (
        Index("idx_email_pref_user", "user_id"),
        Index("idx_email_pref_token", "unsubscribe_token"),
    )


class EmailBounce(Base):
    """Email bounce tracking."""
    __tablename__ = "email_bounces"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False)
    bounce_type = Column(String(50), nullable=False)  # hard, soft, complaint
    bounce_count = Column(Integer, default=1)
    last_bounce_at = Column(DateTime, default=datetime.utcnow)
    is_suppressed = Column(Boolean, default=False)
    suppressed_at = Column(DateTime)
    
    # Bounce details
    reason = Column(Text)
    diagnostic_code = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index("idx_email_bounce_email", "email"),
        Index("idx_email_bounce_suppressed", "is_suppressed"),
        UniqueConstraint("email", name="uq_email_bounce_email"),
    )