"""Simplified analytics for MVP."""
from typing import List, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID
import random

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/analytics", tags=["analytics"])


class DashboardStats(BaseModel):
    """Main dashboard statistics."""
    total_users: int
    active_users: int
    courses_completed: int
    avg_quiz_score: float
    phishing_click_rate: float
    compliance_rate: float


class CourseStats(BaseModel):
    """Course completion statistics."""
    course_id: UUID
    course_name: str
    total_enrolled: int
    total_completed: int
    completion_rate: float
    avg_score: float


class PhishingStats(BaseModel):
    """Phishing campaign statistics."""
    total_campaigns: int
    avg_click_rate: float
    improvement_rate: float
    most_clicked_template: str
    users_never_clicked: int


class UserProgress(BaseModel):
    """Individual user progress."""
    user_id: str
    courses_completed: int
    courses_in_progress: int
    avg_quiz_score: float
    phishing_resistance_score: float
    last_activity: datetime


@router.get("/dashboard", response_model=DashboardStats)
def get_dashboard_stats():
    """Get main dashboard statistics."""
    # Mock data for MVP
    return DashboardStats(
        total_users=150,
        active_users=89,
        courses_completed=234,
        avg_quiz_score=82.5,
        phishing_click_rate=15.3,
        compliance_rate=94.2
    )


@router.get("/courses", response_model=List[CourseStats])
def get_course_analytics():
    """Get course completion analytics."""
    # Mock data for MVP
    courses = [
        CourseStats(
            course_id=UUID("12345678-1234-5678-1234-567812345678"),
            course_name="Cybersecurity Basics",
            total_enrolled=150,
            total_completed=120,
            completion_rate=80.0,
            avg_score=85.5
        ),
        CourseStats(
            course_id=UUID("87654321-4321-8765-4321-876543218765"),
            course_name="Phishing Awareness",
            total_enrolled=150,
            total_completed=98,
            completion_rate=65.3,
            avg_score=78.2
        ),
        CourseStats(
            course_id=UUID("11111111-2222-3333-4444-555555555555"),
            course_name="Password Security",
            total_enrolled=150,
            total_completed=145,
            completion_rate=96.7,
            avg_score=92.1
        )
    ]
    return courses


@router.get("/phishing", response_model=PhishingStats)
def get_phishing_analytics():
    """Get phishing simulation analytics."""
    return PhishingStats(
        total_campaigns=12,
        avg_click_rate=15.3,
        improvement_rate=45.2,
        most_clicked_template="IT Support Password Reset",
        users_never_clicked=67
    )


@router.get("/users/{user_id}", response_model=UserProgress)
def get_user_analytics(user_id: str):
    """Get individual user analytics."""
    return UserProgress(
        user_id=user_id,
        courses_completed=3,
        courses_in_progress=1,
        avg_quiz_score=87.5,
        phishing_resistance_score=92.0,
        last_activity=datetime.utcnow() - timedelta(hours=2)
    )


@router.get("/trends")
def get_trend_data(metric: str = "completion_rate", days: int = 30):
    """Get trend data for various metrics."""
    # Generate mock trend data
    data_points = []
    base_value = 70.0
    
    for i in range(days):
        date = datetime.utcnow() - timedelta(days=days-i)
        value = base_value + random.uniform(-5, 10) + (i * 0.3)  # Upward trend
        data_points.append({
            "date": date.date().isoformat(),
            "value": round(value, 2)
        })
    
    return {
        "metric": metric,
        "period": f"{days} days",
        "data": data_points
    }


@router.get("/compliance")
def get_compliance_report(company_id: Optional[UUID] = None):
    """Get compliance report."""
    return {
        "company_id": company_id,
        "compliance_standards": {
            "NIS-2": {
                "status": "compliant",
                "score": 95.5,
                "requirements_met": 19,
                "requirements_total": 20
            },
            "ISO-27001": {
                "status": "compliant",
                "score": 92.0,
                "requirements_met": 46,
                "requirements_total": 50
            },
            "GDPR": {
                "status": "compliant",
                "score": 98.0,
                "requirements_met": 49,
                "requirements_total": 50
            }
        },
        "next_audit_date": (datetime.utcnow() + timedelta(days=90)).date().isoformat(),
        "recommendations": [
            "Complete remaining security awareness modules",
            "Increase phishing simulation frequency",
            "Update incident response procedures"
        ]
    }


@router.get("/export")
def export_analytics(format: str = "csv", report_type: str = "summary"):
    """Export analytics data."""
    # In a real implementation, this would generate actual files
    return {
        "message": f"Report generated successfully",
        "format": format,
        "type": report_type,
        "download_url": f"/api/v1/downloads/analytics-{datetime.utcnow().date()}.{format}"
    }