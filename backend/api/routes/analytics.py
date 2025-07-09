"""Analytics and reporting routes."""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

from api.dependencies.auth import get_current_active_user, require_company_admin
from api.dependencies.common import get_db
from models.user import User, UserRole
from models.analytics import (
    UserActivity,
    CourseAnalytics,
    CompanyAnalytics,
    SecurityMetrics,
)
from models.course import CourseEnrollment, LessonProgress
from models.phishing import PhishingCampaign, PhishingResult
from schemas.analytics import (
    UserActivityReport,
    CourseCompletionReport,
    SecurityAwarenessReport,
    CompanyOverviewReport,
    PhishingCampaignReport,
    TimeRangeFilter,
)

router = APIRouter()


@router.get("/overview", response_model=CompanyOverviewReport)
async def get_company_overview(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_company_admin),
    time_range: TimeRangeFilter = Query(TimeRangeFilter.LAST_30_DAYS),
) -> CompanyOverviewReport:
    """
    Get company overview analytics.
    
    Args:
        db: Database session
        current_user: Current authenticated user (must be company admin)
        time_range: Time range filter
        
    Returns:
        Company overview report
    """
    # Calculate date range
    end_date = datetime.utcnow()
    if time_range == TimeRangeFilter.LAST_7_DAYS:
        start_date = end_date - timedelta(days=7)
    elif time_range == TimeRangeFilter.LAST_30_DAYS:
        start_date = end_date - timedelta(days=30)
    elif time_range == TimeRangeFilter.LAST_90_DAYS:
        start_date = end_date - timedelta(days=90)
    else:
        start_date = end_date - timedelta(days=365)
    
    # Get total users
    total_users_result = await db.execute(
        select(func.count(User.id)).where(
            and_(
                User.company_id == current_user.company_id,
                User.is_active == True,
            )
        )
    )
    total_users = total_users_result.scalar()
    
    # Get active users (logged in within time range)
    active_users_result = await db.execute(
        select(func.count(func.distinct(User.id))).where(
            and_(
                User.company_id == current_user.company_id,
                User.last_login >= start_date,
                User.is_active == True,
            )
        )
    )
    active_users = active_users_result.scalar()
    
    # Get total enrollments
    total_enrollments_result = await db.execute(
        select(func.count(CourseEnrollment.id))
        .join(User)
        .where(
            and_(
                User.company_id == current_user.company_id,
                CourseEnrollment.enrolled_at >= start_date,
            )
        )
    )
    total_enrollments = total_enrollments_result.scalar()
    
    # Get completed courses
    completed_courses_result = await db.execute(
        select(func.count(CourseEnrollment.id))
        .join(User)
        .where(
            and_(
                User.company_id == current_user.company_id,
                CourseEnrollment.completed_at.isnot(None),
                CourseEnrollment.completed_at >= start_date,
            )
        )
    )
    completed_courses = completed_courses_result.scalar()
    
    # Get phishing campaign results
    phishing_stats_result = await db.execute(
        select(
            func.count(PhishingResult.id).label("total"),
            func.sum(func.cast(PhishingResult.action == "clicked", int)).label("clicked"),
            func.sum(func.cast(PhishingResult.action == "reported", int)).label("reported"),
        )
        .join(PhishingCampaign)
        .where(
            and_(
                PhishingCampaign.company_id == current_user.company_id,
                PhishingResult.timestamp >= start_date,
            )
        )
    )
    phishing_stats = phishing_stats_result.first()
    
    # Calculate metrics
    engagement_rate = (active_users / total_users * 100) if total_users > 0 else 0
    completion_rate = (completed_courses / total_enrollments * 100) if total_enrollments > 0 else 0
    phishing_click_rate = (
        (phishing_stats.clicked / phishing_stats.total * 100)
        if phishing_stats and phishing_stats.total > 0
        else 0
    )
    phishing_report_rate = (
        (phishing_stats.reported / phishing_stats.total * 100)
        if phishing_stats and phishing_stats.total > 0
        else 0
    )
    
    return CompanyOverviewReport(
        total_users=total_users,
        active_users=active_users,
        engagement_rate=engagement_rate,
        total_enrollments=total_enrollments,
        completed_courses=completed_courses,
        completion_rate=completion_rate,
        phishing_emails_sent=phishing_stats.total if phishing_stats else 0,
        phishing_click_rate=phishing_click_rate,
        phishing_report_rate=phishing_report_rate,
        time_range=time_range,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/users", response_model=List[UserActivityReport])
async def get_user_activity_report(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_company_admin),
    user_id: Optional[UUID] = Query(None, description="Filter by specific user"),
    time_range: TimeRangeFilter = Query(TimeRangeFilter.LAST_30_DAYS),
) -> List[UserActivityReport]:
    """
    Get user activity analytics.
    
    Args:
        db: Database session
        current_user: Current authenticated user (must be company admin)
        user_id: Optional user ID filter
        time_range: Time range filter
        
    Returns:
        List of user activity reports
    """
    # Calculate date range
    end_date = datetime.utcnow()
    if time_range == TimeRangeFilter.LAST_7_DAYS:
        start_date = end_date - timedelta(days=7)
    elif time_range == TimeRangeFilter.LAST_30_DAYS:
        start_date = end_date - timedelta(days=30)
    elif time_range == TimeRangeFilter.LAST_90_DAYS:
        start_date = end_date - timedelta(days=90)
    else:
        start_date = end_date - timedelta(days=365)
    
    # Base query
    query = select(
        User.id,
        User.email,
        User.first_name,
        User.last_name,
        User.last_login,
        func.count(func.distinct(CourseEnrollment.id)).label("courses_enrolled"),
        func.count(func.distinct(CourseEnrollment.id)).filter(
            CourseEnrollment.completed_at.isnot(None)
        ).label("courses_completed"),
        func.avg(LessonProgress.time_spent).label("avg_time_per_lesson"),
    ).select_from(User).outerjoin(CourseEnrollment).outerjoin(
        LessonProgress, LessonProgress.user_id == User.id
    ).where(
        and_(
            User.company_id == current_user.company_id,
            User.is_active == True,
        )
    ).group_by(User.id)
    
    # Apply user filter if provided
    if user_id:
        query = query.where(User.id == user_id)
    
    # Execute query
    result = await db.execute(query)
    user_activities = result.all()
    
    # Build response
    reports = []
    for activity in user_activities:
        reports.append(UserActivityReport(
            user_id=activity.id,
            email=activity.email,
            name=f"{activity.first_name} {activity.last_name}",
            last_login=activity.last_login,
            courses_enrolled=activity.courses_enrolled or 0,
            courses_completed=activity.courses_completed or 0,
            avg_time_per_lesson=activity.avg_time_per_lesson or 0,
            is_active=activity.last_login >= start_date if activity.last_login else False,
        ))
    
    return reports


@router.get("/courses", response_model=List[CourseCompletionReport])
async def get_course_completion_report(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_company_admin),
    course_id: Optional[UUID] = Query(None, description="Filter by specific course"),
) -> List[CourseCompletionReport]:
    """
    Get course completion analytics.
    
    Args:
        db: Database session
        current_user: Current authenticated user (must be company admin)
        course_id: Optional course ID filter
        
    Returns:
        List of course completion reports
    """
    # Query for course statistics
    from models.course import Course
    
    query = select(
        Course.id,
        Course.title,
        func.count(func.distinct(CourseEnrollment.user_id)).label("total_enrolled"),
        func.count(func.distinct(CourseEnrollment.user_id)).filter(
            CourseEnrollment.completed_at.isnot(None)
        ).label("total_completed"),
        func.avg(
            func.extract(
                "epoch",
                CourseEnrollment.completed_at - CourseEnrollment.enrolled_at
            ) / 86400  # Convert to days
        ).filter(
            CourseEnrollment.completed_at.isnot(None)
        ).label("avg_completion_days"),
    ).select_from(Course).outerjoin(CourseEnrollment).join(
        User, CourseEnrollment.user_id == User.id
    ).where(
        User.company_id == current_user.company_id
    ).group_by(Course.id)
    
    # Apply course filter if provided
    if course_id:
        query = query.where(Course.id == course_id)
    
    # Execute query
    result = await db.execute(query)
    course_stats = result.all()
    
    # Build response
    reports = []
    for stat in course_stats:
        completion_rate = (
            (stat.total_completed / stat.total_enrolled * 100)
            if stat.total_enrolled > 0
            else 0
        )
        
        reports.append(CourseCompletionReport(
            course_id=stat.id,
            course_title=stat.title,
            total_enrolled=stat.total_enrolled or 0,
            total_completed=stat.total_completed or 0,
            completion_rate=completion_rate,
            avg_completion_days=stat.avg_completion_days or 0,
        ))
    
    return reports


@router.get("/security", response_model=SecurityAwarenessReport)
async def get_security_awareness_report(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_company_admin),
    time_range: TimeRangeFilter = Query(TimeRangeFilter.LAST_30_DAYS),
) -> SecurityAwarenessReport:
    """
    Get security awareness metrics.
    
    Args:
        db: Database session
        current_user: Current authenticated user (must be company admin)
        time_range: Time range filter
        
    Returns:
        Security awareness report
    """
    # Calculate date range
    end_date = datetime.utcnow()
    if time_range == TimeRangeFilter.LAST_7_DAYS:
        start_date = end_date - timedelta(days=7)
    elif time_range == TimeRangeFilter.LAST_30_DAYS:
        start_date = end_date - timedelta(days=30)
    elif time_range == TimeRangeFilter.LAST_90_DAYS:
        start_date = end_date - timedelta(days=90)
    else:
        start_date = end_date - timedelta(days=365)
    
    # Get phishing simulation results
    phishing_results = await db.execute(
        select(
            func.count(PhishingResult.id).label("total"),
            func.sum(func.cast(PhishingResult.action == "clicked", int)).label("clicked"),
            func.sum(func.cast(PhishingResult.action == "reported", int)).label("reported"),
        )
        .join(PhishingCampaign)
        .where(
            and_(
                PhishingCampaign.company_id == current_user.company_id,
                PhishingResult.timestamp >= start_date,
            )
        )
    )
    phishing_stats = phishing_results.first()
    
    # Get users with 2FA enabled
    twofa_result = await db.execute(
        select(func.count(User.id)).where(
            and_(
                User.company_id == current_user.company_id,
                User.two_factor_enabled == True,
                User.is_active == True,
            )
        )
    )
    users_with_2fa = twofa_result.scalar()
    
    # Get total active users
    total_users_result = await db.execute(
        select(func.count(User.id)).where(
            and_(
                User.company_id == current_user.company_id,
                User.is_active == True,
            )
        )
    )
    total_users = total_users_result.scalar()
    
    # Get security training completion
    from models.course import Course
    security_training_result = await db.execute(
        select(
            func.count(func.distinct(CourseEnrollment.user_id)).label("completed")
        )
        .join(Course)
        .join(User)
        .where(
            and_(
                User.company_id == current_user.company_id,
                Course.category == "security",
                CourseEnrollment.completed_at.isnot(None),
                CourseEnrollment.completed_at >= start_date,
            )
        )
    )
    security_training_completed = security_training_result.scalar()
    
    # Calculate metrics
    phishing_resilience_score = 100
    if phishing_stats and phishing_stats.total > 0:
        click_penalty = (phishing_stats.clicked / phishing_stats.total) * 50
        report_bonus = (phishing_stats.reported / phishing_stats.total) * 20
        phishing_resilience_score = max(0, 100 - click_penalty + report_bonus)
    
    two_fa_adoption_rate = (
        (users_with_2fa / total_users * 100) if total_users > 0 else 0
    )
    
    security_training_rate = (
        (security_training_completed / total_users * 100) if total_users > 0 else 0
    )
    
    # Overall security score (weighted average)
    overall_score = (
        phishing_resilience_score * 0.4 +
        two_fa_adoption_rate * 0.3 +
        security_training_rate * 0.3
    )
    
    return SecurityAwarenessReport(
        overall_score=overall_score,
        phishing_resilience_score=phishing_resilience_score,
        phishing_emails_sent=phishing_stats.total if phishing_stats else 0,
        phishing_clicks=phishing_stats.clicked if phishing_stats else 0,
        phishing_reports=phishing_stats.reported if phishing_stats else 0,
        two_fa_adoption_rate=two_fa_adoption_rate,
        users_with_2fa=users_with_2fa,
        security_training_completion_rate=security_training_rate,
        time_range=time_range,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/export/{report_type}")
async def export_report(
    report_type: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_company_admin),
    format: str = Query("csv", regex="^(csv|json|pdf)$"),
) -> Dict[str, Any]:
    """
    Export analytics report.
    
    Args:
        report_type: Type of report to export
        db: Database session
        current_user: Current authenticated user (must be company admin)
        format: Export format (csv, json, pdf)
        
    Returns:
        Export download information
    """
    # TODO: Implement report export functionality
    return {
        "message": "Report export not yet implemented",
        "report_type": report_type,
        "format": format,
    }