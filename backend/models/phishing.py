"""Phishing campaign and template models."""

from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSON

from .base import BaseModel

if TYPE_CHECKING:
    from .user import User
    from .company import Company


class PhishingCampaign(BaseModel):
    """Phishing campaign model for security awareness testing."""
    
    __tablename__ = "phishing_campaigns"
    
    # Foreign Keys
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'), nullable=False, index=True)
    created_by_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=False)
    template_id = Column(Integer, ForeignKey('phishing_templates.id'), nullable=True)
    
    # Campaign Information
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, server_default='draft', index=True)  # draft, scheduled, running, completed, cancelled
    
    # Targeting
    target_groups = Column(JSON, nullable=True)  # List of user groups/departments
    target_user_ids = Column(JSON, nullable=True)  # Specific user IDs
    
    # Scheduling
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Settings
    settings = Column(JSON, nullable=True)  # Additional campaign settings
    
    # Relationships
    company: "Company" = relationship("Company", back_populates="phishing_campaigns")
    created_by: "User" = relationship("User", back_populates="created_phishing_campaigns")
    template: Optional["PhishingTemplate"] = relationship("PhishingTemplate", back_populates="campaigns")
    results: List["PhishingResult"] = relationship(
        "PhishingResult",
        back_populates="campaign",
        cascade="all, delete-orphan"
    )
    
    @property
    def is_draft(self) -> bool:
        """Check if campaign is in draft status."""
        return self.status == 'draft'
    
    @property
    def is_scheduled(self) -> bool:
        """Check if campaign is scheduled."""
        return self.status == 'scheduled'
    
    @property
    def is_running(self) -> bool:
        """Check if campaign is currently running."""
        return self.status == 'running'
    
    @property
    def is_completed(self) -> bool:
        """Check if campaign is completed."""
        return self.status == 'completed'
    
    @property
    def is_cancelled(self) -> bool:
        """Check if campaign is cancelled."""
        return self.status == 'cancelled'
    
    @property
    def total_targets(self) -> int:
        """Get total number of targeted users."""
        return len(self.results)
    
    @property
    def total_sent(self) -> int:
        """Get number of emails sent."""
        return len([r for r in self.results if r.email_sent_at is not None])
    
    @property
    def total_opened(self) -> int:
        """Get number of emails opened."""
        return len([r for r in self.results if r.email_opened_at is not None])
    
    @property
    def total_clicked(self) -> int:
        """Get number of links clicked."""
        return len([r for r in self.results if r.link_clicked_at is not None])
    
    @property
    def total_submitted(self) -> int:
        """Get number of data submissions."""
        return len([r for r in self.results if r.data_submitted_at is not None])
    
    @property
    def total_reported(self) -> int:
        """Get number of phishing reports."""
        return len([r for r in self.results if r.reported_at is not None])
    
    def get_statistics(self) -> dict:
        """Get campaign statistics."""
        total = self.total_targets
        if total == 0:
            return {
                "total_targets": 0,
                "sent_rate": 0.0,
                "open_rate": 0.0,
                "click_rate": 0.0,
                "submit_rate": 0.0,
                "report_rate": 0.0
            }
        
        return {
            "total_targets": total,
            "sent_rate": (self.total_sent / total) * 100,
            "open_rate": (self.total_opened / total) * 100,
            "click_rate": (self.total_clicked / total) * 100,
            "submit_rate": (self.total_submitted / total) * 100,
            "report_rate": (self.total_reported / total) * 100
        }
    
    def __repr__(self) -> str:
        """String representation of PhishingCampaign."""
        return f"<PhishingCampaign {self.name} ({self.status})>"


class PhishingTemplate(BaseModel):
    """Phishing email template model."""
    
    __tablename__ = "phishing_templates"
    
    # Foreign Keys
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'), nullable=True)  # NULL for system templates
    
    # Template Information
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False, index=True)
    difficulty = Column(String(50), nullable=False)  # easy, medium, hard
    
    # Email Content
    subject = Column(String(500), nullable=False)
    sender_name = Column(String(255), nullable=False)
    sender_email = Column(String(255), nullable=False)
    html_content = Column(Text, nullable=False)
    text_content = Column(Text, nullable=True)
    
    # Landing Page
    landing_page_html = Column(Text, nullable=True)
    
    # Settings
    language = Column(String(10), nullable=False, server_default='de')
    is_public = Column(Boolean, nullable=False, server_default=text('true'), index=True)
    
    # Relationships
    company: Optional["Company"] = relationship("Company", back_populates="phishing_templates")
    campaigns: List["PhishingCampaign"] = relationship("PhishingCampaign", back_populates="template")
    
    @property
    def is_system_template(self) -> bool:
        """Check if this is a system template."""
        return self.company_id is None
    
    @property
    def is_custom_template(self) -> bool:
        """Check if this is a custom company template."""
        return self.company_id is not None
    
    def __repr__(self) -> str:
        """String representation of PhishingTemplate."""
        return f"<PhishingTemplate {self.name} ({self.category})>"


class PhishingResult(BaseModel):
    """Phishing campaign result model for tracking user interactions."""
    
    __tablename__ = "phishing_results"
    
    # Foreign Keys
    campaign_id = Column(Integer, ForeignKey('phishing_campaigns.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Email Tracking
    email_sent_at = Column(DateTime(timezone=True), nullable=True)
    email_opened_at = Column(DateTime(timezone=True), nullable=True)
    
    # Interaction Tracking
    link_clicked_at = Column(DateTime(timezone=True), nullable=True)
    data_submitted_at = Column(DateTime(timezone=True), nullable=True)
    reported_at = Column(DateTime(timezone=True), nullable=True)
    
    # Additional Data
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    location_data = Column(JSON, nullable=True)
    
    # Relationships
    campaign: "PhishingCampaign" = relationship("PhishingCampaign", back_populates="results")
    user: "User" = relationship("User", back_populates="phishing_results")
    
    @property
    def was_sent(self) -> bool:
        """Check if email was sent."""
        return self.email_sent_at is not None
    
    @property
    def was_opened(self) -> bool:
        """Check if email was opened."""
        return self.email_opened_at is not None
    
    @property
    def was_clicked(self) -> bool:
        """Check if link was clicked."""
        return self.link_clicked_at is not None
    
    @property
    def data_was_submitted(self) -> bool:
        """Check if data was submitted."""
        return self.data_submitted_at is not None
    
    @property
    def was_reported(self) -> bool:
        """Check if phishing was reported."""
        return self.reported_at is not None
    
    @property
    def risk_score(self) -> int:
        """
        Calculate risk score based on user behavior.
        Higher score = higher risk.
        """
        score = 0
        if self.was_opened:
            score += 1
        if self.was_clicked:
            score += 3
        if self.data_was_submitted:
            score += 5
        if self.was_reported:
            score -= 2  # Reduce score for good behavior
        return max(0, score)
    
    def __repr__(self) -> str:
        """String representation of PhishingResult."""
        return f"<PhishingResult Campaign:{self.campaign_id} User:{self.user_id}>"