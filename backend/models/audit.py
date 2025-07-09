"""Audit and analytics models."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import relationship

from .base import Base

if TYPE_CHECKING:
    from .user import User
    from .company import Company


class AuditLog(Base):
    """Audit log for tracking all system actions."""
    
    __tablename__ = "audit_logs"
    
    # Basic information
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Action details
    action = Column(String(100), nullable=False, index=True)  # create, update, delete, login, logout, etc.
    resource_type = Column(String(100), nullable=False)  # user, company, course, campaign, etc.
    resource_id = Column(Integer, nullable=True)
    
    # Change tracking
    changes = Column(JSON, nullable=True)  # JSON diff of changes
    
    # Request metadata
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", backref="audit_logs")
    company = relationship("Company", backref="audit_logs")
    
    def __repr__(self) -> str:
        return f"<AuditLog {self.action} {self.resource_type}:{self.resource_id}>"


class AuditAnalyticsEvent(Base):
    """Analytics event for tracking user behavior."""
    
    __tablename__ = "audit_analytics_events"
    
    # Basic information
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Event details
    event_type = Column(String(100), nullable=False, index=True)  # page_view, button_click, video_play, etc.
    event_category = Column(String(100), nullable=False)  # navigation, learning, assessment, etc.
    event_data = Column(JSON, nullable=True)  # Additional event-specific data
    
    # Session tracking
    session_id = Column(String(255), nullable=True)
    
    # Request metadata
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", backref="analytics_events")
    company = relationship("Company", backref="analytics_events")
    
    def __repr__(self) -> str:
        return f"<AnalyticsEvent {self.event_type} {self.event_category}>"