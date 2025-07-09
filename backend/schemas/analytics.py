"""
Analytics and reporting schemas for the application.
"""

from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import Field, field_validator

from .base import BaseSchema


class ComplianceStatus(str, Enum):
    """Compliance status levels."""

    COMPLIANT = "compliant"
    NON_COMPLIANT = "non-compliant"
    PARTIALLY_COMPLIANT = "partially-compliant"


class ComplianceStandard(str, Enum):
    """Supported compliance standards."""

    NIS2 = "nis2"
    DSGVO = "dsgvo"
    ISO27001 = "iso27001"
    TISAX = "tisax"
    BAIT = "bait"


class ReportFormat(str, Enum):
    """Available report formats."""

    JSON = "json"
    PDF = "pdf"
    CSV = "csv"
    XLSX = "xlsx"


class TrendDirection(str, Enum):
    """Trend direction indicators."""

    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"


class TimeFrame(str, Enum):
    """Time frame options for analytics."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class ComplianceReport(BaseSchema):
    """Compliance report response."""

    report_type: ComplianceStandard
    company_id: UUID
    period: Dict[str, date] = Field(
        ..., description="Reporting period with 'start' and 'end' dates"
    )
    compliance_status: ComplianceStatus
    compliance_score: float = Field(..., ge=0, le=100)
    details: Dict[str, Any] = Field(
        ..., description="Detailed compliance information"
    )
    requirements_met: List[str] = Field(
        default_factory=list, description="List of met requirements"
    )
    requirements_pending: List[str] = Field(
        default_factory=list, description="List of pending requirements"
    )
    recommendations: List[str] = Field(
        default_factory=list, description="Improvement recommendations"
    )
    generated_at: datetime
    next_review_date: Optional[date] = None
    auditor_notes: Optional[str] = None

    @field_validator("period")
    @classmethod
    def validate_period(cls, v: Dict[str, date]) -> Dict[str, date]:
        """Ensure period has valid start and end dates."""
        if "start" not in v or "end" not in v:
            raise ValueError("Period must have 'start' and 'end' dates")
        if v["start"] > v["end"]:
            raise ValueError("Start date must be before end date")
        return v


class CompanyMetrics(BaseSchema):
    """Company-level metrics."""

    total_users: int = Field(0, ge=0)
    active_users: int = Field(0, ge=0)
    inactive_users: int = Field(0, ge=0)
    average_risk_score: float = Field(50.0, ge=0, le=100)
    high_risk_users: int = Field(0, ge=0)
    medium_risk_users: int = Field(0, ge=0)
    low_risk_users: int = Field(0, ge=0)
    users_with_2fa: int = Field(0, ge=0)
    password_policy_compliant: int = Field(0, ge=0)

    @field_validator("average_risk_score")
    @classmethod
    def round_risk_score(cls, v: float) -> float:
        """Round risk score to 2 decimal places."""
        return round(v, 2)


class TrainingMetrics(BaseSchema):
    """Training-related metrics."""

    courses_completed_this_month: int = Field(0, ge=0)
    courses_in_progress: int = Field(0, ge=0)
    average_completion_rate: float = Field(0.0, ge=0, le=100)
    average_quiz_score: float = Field(0.0, ge=0, le=100)
    overdue_trainings: int = Field(0, ge=0)
    trainings_due_this_week: int = Field(0, ge=0)
    most_completed_course: Optional[str] = None
    least_completed_course: Optional[str] = None
    average_time_to_complete_hours: float = Field(0.0, ge=0)
    certificates_issued_this_month: int = Field(0, ge=0)

    @field_validator("average_completion_rate", "average_quiz_score")
    @classmethod
    def round_percentages(cls, v: float) -> float:
        """Round percentages to 2 decimal places."""
        return round(v, 2)


class PhishingMetrics(BaseSchema):
    """Phishing campaign metrics."""

    campaigns_this_quarter: int = Field(0, ge=0)
    campaigns_total: int = Field(0, ge=0)
    average_click_rate: float = Field(0.0, ge=0, le=100)
    average_report_rate: float = Field(0.0, ge=0, le=100)
    improvement_rate: float = Field(
        0.0, description="Percentage improvement from baseline"
    )
    users_never_clicked: int = Field(0, ge=0)
    repeat_clickers: int = Field(0, ge=0)
    time_to_click_median_minutes: Optional[float] = None
    most_effective_template: Optional[str] = None
    department_most_vulnerable: Optional[str] = None

    @field_validator("average_click_rate", "average_report_rate", "improvement_rate")
    @classmethod
    def round_percentages(cls, v: float) -> float:
        """Round percentages to 2 decimal places."""
        return round(v, 2)


class ComplianceOverview(BaseSchema):
    """Single compliance standard overview."""

    standard: ComplianceStandard
    status: ComplianceStatus
    score: float = Field(0.0, ge=0, le=100)
    last_assessment: Optional[date] = None
    next_assessment: Optional[date] = None
    critical_findings: int = Field(0, ge=0)
    action_items: int = Field(0, ge=0)


class ExecutiveDashboard(BaseSchema):
    """Executive dashboard data."""

    company_metrics: CompanyMetrics
    training_metrics: TrainingMetrics
    phishing_metrics: PhishingMetrics
    compliance_overview: List[ComplianceOverview]
    security_score: float = Field(
        50.0, ge=0, le=100, description="Overall security posture score"
    )
    month_over_month_improvement: float = Field(
        0.0, description="Percentage change from last month"
    )
    top_risks: List[str] = Field(
        default_factory=list, max_length=5, description="Top 5 risk areas"
    )
    upcoming_deadlines: List[Dict[str, Any]] = Field(
        default_factory=list, description="Upcoming compliance deadlines"
    )
    generated_at: datetime

    @field_validator("security_score", "month_over_month_improvement")
    @classmethod
    def round_scores(cls, v: float) -> float:
        """Round scores to 2 decimal places."""
        return round(v, 2)


class RiskTrend(BaseSchema):
    """Risk score trend data point."""

    date: date
    average_risk_score: float = Field(..., ge=0, le=100)
    high_risk_count: int = Field(..., ge=0)
    medium_risk_count: int = Field(..., ge=0)
    low_risk_count: int = Field(..., ge=0)
    total_users: int = Field(..., ge=0)
    events: List[str] = Field(
        default_factory=list, description="Notable events on this date"
    )


class DepartmentTrend(BaseSchema):
    """Department risk trend information."""

    department: str
    trend: TrendDirection
    current_score: float = Field(..., ge=0, le=100)
    previous_score: float = Field(..., ge=0, le=100)
    change_percentage: float
    high_risk_users: int = Field(0, ge=0)
    training_completion_rate: float = Field(0.0, ge=0, le=100)

    @field_validator("current_score", "previous_score", "change_percentage", "training_completion_rate")
    @classmethod
    def round_values(cls, v: float) -> float:
        """Round values to 2 decimal places."""
        return round(v, 2)


class RiskTrends(BaseSchema):
    """Risk trend analysis response."""

    timeframe: TimeFrame
    data_points: List[RiskTrend]
    departments: List[DepartmentTrend]
    overall_trend: TrendDirection
    predicted_next_month: float = Field(
        50.0, ge=0, le=100, description="ML-predicted risk score for next month"
    )
    risk_factors: List[str] = Field(
        default_factory=list, description="Key risk factors identified"
    )
    recommendations: List[str] = Field(
        default_factory=list, description="Recommended actions"
    )


class UserRiskProfile(BaseSchema):
    """Individual user risk profile."""

    user_id: UUID
    current_risk_score: float = Field(..., ge=0, le=100)
    risk_factors: List[Dict[str, Any]] = Field(
        ..., description="Individual risk factors and their weights"
    )
    training_status: str
    phishing_susceptibility: str = Field(
        ..., description="Low, Medium, or High"
    )
    last_incident: Optional[datetime] = None
    recommendations: List[str]


class SecurityMetrics(BaseSchema):
    """Overall security metrics."""

    mfa_adoption_rate: float = Field(0.0, ge=0, le=100)
    password_strength_average: float = Field(0.0, ge=0, le=100)
    incident_response_time_hours: float = Field(0.0, ge=0)
    vulnerabilities_found: int = Field(0, ge=0)
    vulnerabilities_patched: int = Field(0, ge=0)
    security_training_coverage: float = Field(0.0, ge=0, le=100)
    last_security_audit: Optional[date] = None
    security_maturity_level: int = Field(1, ge=1, le=5)


class ReportRequest(BaseSchema):
    """Generic report request parameters."""

    start_date: date
    end_date: date
    format: ReportFormat = Field(ReportFormat.JSON)
    include_details: bool = Field(True)
    departments: Optional[List[str]] = None
    compliance_standards: Optional[List[ComplianceStandard]] = None

    @field_validator("end_date")
    @classmethod
    def validate_date_range(cls, v: date, info) -> date:
        """Ensure end date is after start date."""
        if "start_date" in info.data and v < info.data["start_date"]:
            raise ValueError("End date must be after start date")
        return v