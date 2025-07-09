"""Phishing simulation models."""

from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import relationship

from .base import Base

if TYPE_CHECKING:
    from .user import User
    from .company import Company


class PhishingCampaign(Base):
    """Phishing campaign model."""
    
    __tablename__ = "phishing_campaigns"
    
    # Basic information
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Campaign status
    status = Column(String(50), nullable=False, default="draft", index=True)  # draft, scheduled, running, completed, cancelled
    template_id = Column(Integer, ForeignKey("phishing_templates.id"), nullable=True)
    
    # Targeting
    target_groups = Column(JSON, nullable=True)  # List of departments, roles, or user IDs
    
    # Scheduling
    scheduled_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Configuration
    settings = Column(JSON, nullable=True)  # Campaign-specific settings
    
    # Relationships
    company = relationship("Company", backref="phishing_campaigns")
    created_by = relationship("User", backref="created_campaigns")
    template = relationship("PhishingTemplate", backref="campaigns")
    results = relationship("PhishingResult", back_populates="campaign", cascade="all, delete-orphan")
    analytics = relationship("PhishingAnalytics", back_populates="campaign")
    
    def __repr__(self) -> str:
        return f"<PhishingCampaign {self.name}>"
    
    @property
    def total_recipients(self) -> int:
        """Get total number of recipients."""
        return len(self.results)
    
    @property
    def click_rate(self) -> float:
        """Calculate click rate percentage."""
        if not self.results:
            return 0.0
        clicked = sum(1 for r in self.results if r.link_clicked_at is not None)
        return (clicked / len(self.results)) * 100


class PhishingTemplate(Base):
    """Phishing email template model."""
    
    __tablename__ = "phishing_templates"
    
    # Basic information
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False, index=True)
    difficulty = Column(String(50), nullable=False)  # easy, medium, hard
    
    # Email content
    subject = Column(String(500), nullable=False)
    sender_name = Column(String(255), nullable=False)
    sender_email = Column(String(255), nullable=False)
    html_content = Column(Text, nullable=False)
    text_content = Column(Text, nullable=True)
    
    # Landing page
    landing_page_html = Column(Text, nullable=True)
    
    # Metadata
    language = Column(String(10), nullable=False, default="de")
    is_public = Column(Boolean, nullable=False, default=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=True)
    
    # Relationships
    company = relationship("Company", backref="custom_templates")
    
    def __repr__(self) -> str:
        return f"<PhishingTemplate {self.name}>"


class PhishingResult(Base):
    """Phishing campaign result for individual users."""
    
    __tablename__ = "phishing_results"
    
    # Foreign keys
    campaign_id = Column(Integer, ForeignKey("phishing_campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Tracking data
    email_sent_at = Column(DateTime, nullable=True)
    email_opened_at = Column(DateTime, nullable=True)
    link_clicked_at = Column(DateTime, nullable=True)
    data_submitted_at = Column(DateTime, nullable=True)
    reported_at = Column(DateTime, nullable=True)
    
    # Additional data
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    location_data = Column(JSON, nullable=True)
    
    # Relationships
    campaign = relationship("PhishingCampaign", back_populates="results")
    user = relationship("User", backref="phishing_results")
    
    def __repr__(self) -> str:
        return f"<PhishingResult campaign={self.campaign_id} user={self.user_id}>"
    
    @property
    def was_clicked(self) -> bool:
        """Check if user clicked the phishing link."""
        return self.link_clicked_at is not None
    
    @property
    def was_reported(self) -> bool:
        """Check if user reported the phishing email."""
        return self.reported_at is not None
    
    @property
    def response_time_seconds(self) -> int:
        """Calculate time between email sent and clicked."""
        if not self.email_sent_at or not self.link_clicked_at:
            return None
        return int((self.link_clicked_at - self.email_sent_at).total_seconds())