"""Analytics models for the awareness platform."""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import (
    Column, String, Integer, DateTime, ForeignKey, JSON, Date,
    Numeric, UniqueConstraint, Index, func, text
)
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import relationship

from models.base import Base


class AnalyticsEvent(Base):
    """Track all analytics events in the system."""
    
    __tablename__ = "analytics_events"
    __table_args__ = {"schema": "analytics"}
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    event_type = Column(String(50), nullable=False)  # page_view, course_start, quiz_complete
    event_category = Column(String(50), nullable=False)  # navigation, learning, assessment
    event_action = Column(String(100), nullable=False)  # view, click, submit, complete
    event_label = Column(String(255))  # Additional context
    event_value = Column(Numeric(10, 2))  # Numeric value if applicable
    
    user_id = Column(PostgresUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    company_id = Column(PostgresUUID(as_uuid=True), ForeignKey("companies.id", ondelete="SET NULL"))
    session_id = Column(String(100))
    event_metadata = Column(JSON)  # Additional event data
    
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="analytics_events")
    company = relationship("Company", back_populates="analytics_events")
    
    # Indexes
    __table_args__ = (
        Index("idx_analytics_events_user_created", "user_id", "created_at"),
        Index("idx_analytics_events_company_created", "company_id", "created_at"),
        Index("idx_analytics_events_type_category", "event_type", "event_category"),
        {"schema": "analytics"}
    )


class CourseAnalytics(Base):
    """Aggregated course analytics by day and company."""
    
    __tablename__ = "course_analytics"
    __table_args__ = {"schema": "analytics"}
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    course_id = Column(PostgresUUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    company_id = Column(PostgresUUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"))
    date = Column(Date, nullable=False)
    
    enrollments_count = Column(Integer, default=0)
    completions_count = Column(Integer, default=0)
    avg_progress = Column(Numeric(5, 2), default=0)
    avg_score = Column(Numeric(5, 2), default=0)
    total_time_spent = Column(Integer, default=0)  # in minutes
    unique_users = Column(Integer, default=0)
    
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    course = relationship("Course", back_populates="analytics")
    company = relationship("Company", back_populates="course_analytics")
    
    __table_args__ = (
        UniqueConstraint("course_id", "company_id", "date", name="uq_course_company_date"),
        Index("idx_course_analytics_course_date", "course_id", "date"),
        Index("idx_course_analytics_company_date", "company_id", "date"),
        {"schema": "analytics"}
    )


class UserEngagement(Base):
    """Track user engagement metrics by day."""
    
    __tablename__ = "user_engagement"
    __table_args__ = {"schema": "analytics"}
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    user_id = Column(PostgresUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    company_id = Column(PostgresUUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"))
    date = Column(Date, nullable=False)
    
    login_count = Column(Integer, default=0)
    page_views = Column(Integer, default=0)
    time_spent = Column(Integer, default=0)  # in minutes
    courses_started = Column(Integer, default=0)
    courses_completed = Column(Integer, default=0)
    quizzes_taken = Column(Integer, default=0)
    avg_quiz_score = Column(Numeric(5, 2))
    phishing_attempts = Column(Integer, default=0)
    phishing_reported = Column(Integer, default=0)
    
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="engagement_metrics")
    company = relationship("Company", back_populates="user_engagement")
    
    __table_args__ = (
        UniqueConstraint("user_id", "date", name="uq_user_date"),
        Index("idx_user_engagement_user_date", "user_id", "date"),
        Index("idx_user_engagement_company_date", "company_id", "date"),
        {"schema": "analytics"}
    )


class RevenueAnalytics(Base):
    """Track revenue metrics by company and day."""
    
    __tablename__ = "revenue_analytics"
    __table_args__ = {"schema": "analytics"}
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    company_id = Column(PostgresUUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    
    subscription_revenue = Column(Numeric(10, 2), default=0)
    one_time_revenue = Column(Numeric(10, 2), default=0)
    total_revenue = Column(Numeric(10, 2), default=0)
    new_subscriptions = Column(Integer, default=0)
    cancelled_subscriptions = Column(Integer, default=0)
    active_subscriptions = Column(Integer, default=0)
    mrr = Column(Numeric(10, 2), default=0)  # Monthly Recurring Revenue
    arr = Column(Numeric(10, 2), default=0)  # Annual Recurring Revenue
    currency = Column(String(3), default="EUR")
    
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    company = relationship("Company", back_populates="revenue_analytics")
    
    __table_args__ = (
        UniqueConstraint("company_id", "date", name="uq_company_revenue_date"),
        Index("idx_revenue_analytics_company_date", "company_id", "date"),
        {"schema": "analytics"}
    )


class PhishingAnalytics(Base):
    """Track phishing simulation metrics."""
    
    __tablename__ = "phishing_analytics"
    __table_args__ = {"schema": "analytics"}
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    company_id = Column(PostgresUUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    campaign_id = Column(PostgresUUID(as_uuid=True), ForeignKey("phishing_campaigns.id", ondelete="SET NULL"))
    date = Column(Date, nullable=False)
    
    emails_sent = Column(Integer, default=0)
    emails_opened = Column(Integer, default=0)
    links_clicked = Column(Integer, default=0)
    credentials_entered = Column(Integer, default=0)
    reported_suspicious = Column(Integer, default=0)
    open_rate = Column(Numeric(5, 2), default=0)
    click_rate = Column(Numeric(5, 2), default=0)
    report_rate = Column(Numeric(5, 2), default=0)
    
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    company = relationship("Company", back_populates="phishing_analytics")
    campaign = relationship("PhishingCampaign", back_populates="analytics")
    
    __table_args__ = (
        UniqueConstraint("company_id", "campaign_id", "date", name="uq_company_campaign_date"),
        Index("idx_phishing_analytics_company_date", "company_id", "date"),
        {"schema": "analytics"}
    )


class RealtimeMetric(Base):
    """Store real-time metrics for dashboard display."""
    
    __tablename__ = "realtime_metrics"
    __table_args__ = {"schema": "analytics"}
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Numeric(20, 4), nullable=False)
    metric_type = Column(String(50), nullable=False)  # counter, gauge, percentage
    company_id = Column(PostgresUUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"))
    dimension = Column(String(100))  # e.g., course_id, user_role
    dimension_value = Column(String(255))
    timestamp = Column(DateTime, nullable=False, server_default=func.now())
    ttl = Column(Integer, default=3600)  # Time to live in seconds
    
    # Relationships
    company = relationship("Company", back_populates="realtime_metrics")
    
    __table_args__ = (
        Index("idx_realtime_metrics_name_company", "metric_name", "company_id"),
        Index("idx_realtime_metrics_timestamp", "timestamp"),
        {"schema": "analytics"}
    )