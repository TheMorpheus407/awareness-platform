"""Analytics API routes."""

from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, and_, or_, distinct
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from api.dependencies.auth import get_current_user, require_admin
from core.logging import logger
from db.session import get_db
from models import (
    User, Company, Course, CourseEnrollment,
    CourseAnalytics, UserEngagement, RevenueAnalytics,
    PhishingAnalytics, RealtimeMetric, AnalyticsEvent,
    Subscription, Payment, UserRole
)
from schemas.analytics import (
    AnalyticsEventCreate, AnalyticsEventResponse,
    DashboardMetrics, CourseAnalyticsResponse,
    UserEngagementResponse, RevenueAnalyticsResponse,
    PhishingAnalyticsResponse, RealtimeMetricResponse,
    AnalyticsExportRequest, AnalyticsDateRange
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.post("/events", response_model=AnalyticsEventResponse)
async def track_analytics_event(
    event: AnalyticsEventCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Track an analytics event."""
    try:
        analytics_event = AnalyticsEvent(
            event_type=event.event_type,
            event_category=event.event_category,
            event_action=event.event_action,
            event_label=event.event_label,
            event_value=event.event_value,
            user_id=current_user.id,
            company_id=current_user.company_id,
            session_id=event.session_id,
            metadata=event.metadata
        )
        
        db.add(analytics_event)
        db.commit()
        db.refresh(analytics_event)
        
        logger.info(f"Analytics event tracked: {event.event_type} - {event.event_action}")
        return analytics_event
        
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error tracking analytics event: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to track event")


@router.get("/dashboard", response_model=DashboardMetrics)
async def get_dashboard_metrics(
    date_range: AnalyticsDateRange = Query(AnalyticsDateRange.LAST_30_DAYS),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive dashboard metrics."""
    try:
        # Calculate date range
        end_date = datetime.utcnow().date()
        if date_range == AnalyticsDateRange.TODAY:
            start_date = end_date
        elif date_range == AnalyticsDateRange.LAST_7_DAYS:
            start_date = end_date - timedelta(days=7)
        elif date_range == AnalyticsDateRange.LAST_30_DAYS:
            start_date = end_date - timedelta(days=30)
        elif date_range == AnalyticsDateRange.LAST_90_DAYS:
            start_date = end_date - timedelta(days=90)
        elif date_range == AnalyticsDateRange.LAST_YEAR:
            start_date = end_date - timedelta(days=365)
        else:
            start_date = end_date - timedelta(days=30)
        
        # Base query filters
        if current_user.role == UserRole.SUPER_ADMIN:
            company_filter = True  # No filter for super admin
        else:
            company_filter = Company.id == current_user.company_id
        
        # Get key metrics
        metrics = {}
        
        # User metrics
        total_users = db.query(func.count(User.id)).filter(
            User.company_id == current_user.company_id if not current_user.role == UserRole.SUPER_ADMIN else True
        ).scalar()
        
        active_users = db.query(func.count(User.id)).filter(
            User.company_id == current_user.company_id if not current_user.role == UserRole.SUPER_ADMIN else True,
            User.last_login_at >= datetime.utcnow() - timedelta(days=30)
        ).scalar()
        
        # Course metrics
        total_courses = db.query(func.count(Course.id)).filter(
            Course.status == 'published'
        ).scalar()
        
        # Enrollment metrics
        enrollment_query = db.query(CourseEnrollment).join(User).filter(
            User.company_id == current_user.company_id if not current_user.role == UserRole.SUPER_ADMIN else True
        )
        
        total_enrollments = enrollment_query.count()
        completed_enrollments = enrollment_query.filter(
            CourseEnrollment.completed_at.isnot(None)
        ).count()
        
        # Calculate completion rate
        completion_rate = (completed_enrollments / total_enrollments * 100) if total_enrollments > 0 else 0
        
        # Revenue metrics (for admins only)
        revenue_metrics = {}
        if current_user.role in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
            # Get revenue data
            revenue_data = db.query(
                func.sum(Payment.amount).label('total_revenue'),
                func.count(distinct(Subscription.id)).label('active_subscriptions')
            ).join(Subscription).filter(
                Payment.company_id == current_user.company_id if not current_user.role == UserRole.SUPER_ADMIN else True,
                Payment.created_at >= start_date,
                Subscription.status == 'active'
            ).first()
            
            revenue_metrics = {
                'total_revenue': float(revenue_data.total_revenue or 0),
                'active_subscriptions': revenue_data.active_subscriptions or 0,
                'mrr': float(revenue_data.total_revenue or 0) / max(1, (end_date - start_date).days / 30)
            }
        
        # Engagement metrics
        engagement_data = db.query(
            func.avg(UserEngagement.time_spent).label('avg_time_spent'),
            func.avg(UserEngagement.courses_completed).label('avg_courses_completed')
        ).filter(
            UserEngagement.company_id == current_user.company_id if not current_user.role == UserRole.SUPER_ADMIN else True,
            UserEngagement.date >= start_date
        ).first()
        
        # Build response
        return DashboardMetrics(
            date_range=date_range,
            start_date=start_date,
            end_date=end_date,
            users={
                'total': total_users,
                'active': active_users,
                'new_this_period': db.query(func.count(User.id)).filter(
                    User.company_id == current_user.company_id if not current_user.role == UserRole.SUPER_ADMIN else True,
                    User.created_at >= start_date
                ).scalar()
            },
            courses={
                'total': total_courses,
                'enrollments': total_enrollments,
                'completions': completed_enrollments,
                'completion_rate': completion_rate,
                'avg_progress': db.query(func.avg(CourseEnrollment.progress)).filter(
                    CourseEnrollment.user_id.in_(
                        db.query(User.id).filter(
                            User.company_id == current_user.company_id if not current_user.role == UserRole.SUPER_ADMIN else True
                        )
                    )
                ).scalar() or 0
            },
            engagement={
                'avg_time_spent_minutes': float(engagement_data.avg_time_spent or 0) if engagement_data else 0,
                'avg_courses_per_user': float(engagement_data.avg_courses_completed or 0) if engagement_data else 0,
                'daily_active_users': db.query(func.count(distinct(User.id))).filter(
                    User.company_id == current_user.company_id if not current_user.role == UserRole.SUPER_ADMIN else True,
                    User.last_login_at >= datetime.utcnow() - timedelta(days=1)
                ).scalar()
            },
            **({'revenue': revenue_metrics} if revenue_metrics else {})
        )
        
    except SQLAlchemyError as e:
        logger.error(f"Error fetching dashboard metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch metrics")


@router.get("/courses", response_model=List[CourseAnalyticsResponse])
async def get_course_analytics(
    course_id: Optional[UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get course analytics data."""
    try:
        query = db.query(CourseAnalytics)
        
        # Apply filters
        if current_user.role != UserRole.SUPER_ADMIN:
            query = query.filter(CourseAnalytics.company_id == current_user.company_id)
        
        if course_id:
            query = query.filter(CourseAnalytics.course_id == course_id)
        
        if start_date:
            query = query.filter(CourseAnalytics.date >= start_date)
        
        if end_date:
            query = query.filter(CourseAnalytics.date <= end_date)
        
        # Order by date descending
        analytics = query.order_by(CourseAnalytics.date.desc()).limit(100).all()
        
        return analytics
        
    except SQLAlchemyError as e:
        logger.error(f"Error fetching course analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch analytics")


@router.get("/engagement", response_model=List[UserEngagementResponse])
async def get_user_engagement(
    user_id: Optional[UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user engagement analytics."""
    try:
        query = db.query(UserEngagement)
        
        # Apply filters
        if current_user.role == UserRole.EMPLOYEE:
            # Employees can only see their own data
            query = query.filter(UserEngagement.user_id == current_user.id)
        elif current_user.role != UserRole.SUPER_ADMIN:
            query = query.filter(UserEngagement.company_id == current_user.company_id)
        
        if user_id and current_user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
            query = query.filter(UserEngagement.user_id == user_id)
        
        if start_date:
            query = query.filter(UserEngagement.date >= start_date)
        
        if end_date:
            query = query.filter(UserEngagement.date <= end_date)
        
        # Order by date descending
        engagement = query.order_by(UserEngagement.date.desc()).limit(100).all()
        
        return engagement
        
    except SQLAlchemyError as e:
        logger.error(f"Error fetching user engagement: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch engagement data")


@router.get("/revenue", response_model=List[RevenueAnalyticsResponse])
@require_admin
async def get_revenue_analytics(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get revenue analytics (admin only)."""
    try:
        query = db.query(RevenueAnalytics)
        
        # Apply filters
        if current_user.role != UserRole.SUPER_ADMIN:
            query = query.filter(RevenueAnalytics.company_id == current_user.company_id)
        
        if start_date:
            query = query.filter(RevenueAnalytics.date >= start_date)
        
        if end_date:
            query = query.filter(RevenueAnalytics.date <= end_date)
        
        # Order by date descending
        revenue = query.order_by(RevenueAnalytics.date.desc()).limit(100).all()
        
        return revenue
        
    except SQLAlchemyError as e:
        logger.error(f"Error fetching revenue analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch revenue data")


@router.get("/phishing", response_model=List[PhishingAnalyticsResponse])
async def get_phishing_analytics(
    campaign_id: Optional[UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get phishing simulation analytics."""
    try:
        query = db.query(PhishingAnalytics)
        
        # Apply filters
        if current_user.role != UserRole.SUPER_ADMIN:
            query = query.filter(PhishingAnalytics.company_id == current_user.company_id)
        
        if campaign_id:
            query = query.filter(PhishingAnalytics.campaign_id == campaign_id)
        
        if start_date:
            query = query.filter(PhishingAnalytics.date >= start_date)
        
        if end_date:
            query = query.filter(PhishingAnalytics.date <= end_date)
        
        # Order by date descending
        phishing = query.order_by(PhishingAnalytics.date.desc()).limit(100).all()
        
        return phishing
        
    except SQLAlchemyError as e:
        logger.error(f"Error fetching phishing analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch phishing data")


@router.get("/realtime", response_model=List[RealtimeMetricResponse])
async def get_realtime_metrics(
    metric_name: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get real-time metrics."""
    try:
        query = db.query(RealtimeMetric)
        
        # Apply filters
        if current_user.role != UserRole.SUPER_ADMIN:
            query = query.filter(
                or_(
                    RealtimeMetric.company_id == current_user.company_id,
                    RealtimeMetric.company_id.is_(None)
                )
            )
        
        if metric_name:
            query = query.filter(RealtimeMetric.metric_name == metric_name)
        
        # Only get recent metrics (within TTL)
        query = query.filter(
            RealtimeMetric.timestamp >= datetime.utcnow() - timedelta(seconds=3600)
        )
        
        # Order by timestamp descending
        metrics = query.order_by(RealtimeMetric.timestamp.desc()).limit(50).all()
        
        return metrics
        
    except SQLAlchemyError as e:
        logger.error(f"Error fetching realtime metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch metrics")


@router.post("/export")
@require_admin
async def export_analytics(
    export_request: AnalyticsExportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export analytics data to various formats."""
    try:
        # TODO: Implement export functionality
        # This would generate Excel/PDF reports based on the request
        return {
            "message": "Export functionality coming soon",
            "format": export_request.format,
            "data_types": export_request.data_types
        }
        
    except Exception as e:
        logger.error(f"Error exporting analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to export data")


@router.post("/refresh-materialized-views")
@require_admin
async def refresh_materialized_views(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Refresh analytics materialized views (admin only)."""
    try:
        # Refresh the company overview materialized view
        db.execute("SELECT analytics.refresh_company_overview()")
        db.commit()
        
        logger.info("Analytics materialized views refreshed")
        return {"message": "Materialized views refreshed successfully"}
        
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error refreshing materialized views: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to refresh views")