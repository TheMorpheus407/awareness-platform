"""Analytics schemas."""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class AnalyticsDateRange(str, Enum):
    """Date range options for analytics."""
    TODAY = "today"
    LAST_7_DAYS = "last_7_days"
    LAST_30_DAYS = "last_30_days"
    LAST_90_DAYS = "last_90_days"
    LAST_YEAR = "last_year"
    CUSTOM = "custom"


class ExportFormat(str, Enum):
    """Export format options."""
    CSV = "csv"
    EXCEL = "excel"
    PDF = "pdf"
    JSON = "json"


class AnalyticsDataType(str, Enum):
    """Types of analytics data."""
    DASHBOARD = "dashboard"
    COURSES = "courses"
    USERS = "users"
    REVENUE = "revenue"
    PHISHING = "phishing"
    ENGAGEMENT = "engagement"


# Analytics Event Schemas
class AnalyticsEventCreate(BaseModel):
    """Schema for creating analytics events."""
    event_type: str = Field(..., max_length=50)
    event_category: str = Field(..., max_length=50)
    event_action: str = Field(..., max_length=100)
    event_label: Optional[str] = Field(None, max_length=255)
    event_value: Optional[Decimal] = None
    session_id: Optional[str] = Field(None, max_length=100)
    metadata: Optional[Dict[str, Any]] = None


class AnalyticsEventResponse(BaseModel):
    """Response schema for analytics events."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    event_type: str
    event_category: str
    event_action: str
    event_label: Optional[str]
    event_value: Optional[Decimal]
    user_id: Optional[UUID]
    company_id: Optional[UUID]
    session_id: Optional[str]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime


# Dashboard Metrics
class UserMetrics(BaseModel):
    """User-related metrics."""
    total: int
    active: int
    new_this_period: int


class CourseMetrics(BaseModel):
    """Course-related metrics."""
    total: int
    enrollments: int
    completions: int
    completion_rate: float
    avg_progress: float


class EngagementMetrics(BaseModel):
    """User engagement metrics."""
    avg_time_spent_minutes: float
    avg_courses_per_user: float
    daily_active_users: int


class RevenueMetrics(BaseModel):
    """Revenue metrics (admin only)."""
    total_revenue: float
    active_subscriptions: int
    mrr: float  # Monthly Recurring Revenue


class DashboardMetrics(BaseModel):
    """Comprehensive dashboard metrics."""
    date_range: AnalyticsDateRange
    start_date: date
    end_date: date
    users: UserMetrics
    courses: CourseMetrics
    engagement: EngagementMetrics
    revenue: Optional[RevenueMetrics] = None


# Course Analytics
class CourseAnalyticsResponse(BaseModel):
    """Course analytics response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    course_id: UUID
    company_id: Optional[UUID]
    date: date
    enrollments_count: int
    completions_count: int
    avg_progress: Decimal
    avg_score: Decimal
    total_time_spent: int
    unique_users: int
    created_at: datetime
    updated_at: datetime


# User Engagement
class UserEngagementResponse(BaseModel):
    """User engagement response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    user_id: UUID
    company_id: Optional[UUID]
    date: date
    login_count: int
    page_views: int
    time_spent: int
    courses_started: int
    courses_completed: int
    quizzes_taken: int
    avg_quiz_score: Optional[Decimal]
    phishing_attempts: int
    phishing_reported: int
    created_at: datetime
    updated_at: datetime


# Revenue Analytics
class RevenueAnalyticsResponse(BaseModel):
    """Revenue analytics response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    company_id: UUID
    date: date
    subscription_revenue: Decimal
    one_time_revenue: Decimal
    total_revenue: Decimal
    new_subscriptions: int
    cancelled_subscriptions: int
    active_subscriptions: int
    mrr: Decimal
    arr: Decimal
    currency: str
    created_at: datetime
    updated_at: datetime


# Phishing Analytics
class PhishingAnalyticsResponse(BaseModel):
    """Phishing analytics response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    company_id: UUID
    campaign_id: Optional[UUID]
    date: date
    emails_sent: int
    emails_opened: int
    links_clicked: int
    credentials_entered: int
    reported_suspicious: int
    open_rate: Decimal
    click_rate: Decimal
    report_rate: Decimal
    created_at: datetime
    updated_at: datetime


# Realtime Metrics
class RealtimeMetricResponse(BaseModel):
    """Realtime metric response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    metric_name: str
    metric_value: Decimal
    metric_type: str
    company_id: Optional[UUID]
    dimension: Optional[str]
    dimension_value: Optional[str]
    timestamp: datetime
    ttl: int


# Export Request
class AnalyticsExportRequest(BaseModel):
    """Request for exporting analytics data."""
    format: ExportFormat
    data_types: List[AnalyticsDataType]
    date_range: AnalyticsDateRange
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    filters: Optional[Dict[str, Any]] = None