"""Analytics routes."""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from api.dependencies.auth import get_current_active_user, require_company_admin
from models.user import User
from services.analytics_service import AnalyticsService

router = APIRouter()


@router.get("/overview")
async def get_analytics_overview(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    days: int = Query(30, ge=1, le=365, description="Number of days to include"),
):
    """
    Get analytics overview for the current user's company.
    
    Args:
        db: Database session
        current_user: Current authenticated user
        days: Number of days to include in the analysis
        
    Returns:
        Analytics overview data
    """
    analytics_service = AnalyticsService(db)
    
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Get dashboard metrics
    metrics = await analytics_service.get_dashboard_metrics(
        company_id=current_user.company_id,
        date_range=(start_date, end_date)
    )
    
    return {
        "status": "success",
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "days": days
        },
        "data": metrics
    }


@router.get("/dashboard")
async def get_dashboard_data(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    start_date: Optional[datetime] = Query(None, description="Start date for analysis"),
    end_date: Optional[datetime] = Query(None, description="End date for analysis"),
):
    """
    Get comprehensive dashboard data.
    
    Args:
        db: Database session
        current_user: Current authenticated user
        start_date: Optional start date
        end_date: Optional end date
        
    Returns:
        Dashboard analytics data
    """
    analytics_service = AnalyticsService(db)
    
    # Set default date range if not provided
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=30)
        
    # Validate date range
    if start_date >= end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date must be before end date"
        )
        
    # Get dashboard metrics
    metrics = await analytics_service.get_dashboard_metrics(
        company_id=current_user.company_id,
        date_range=(start_date, end_date)
    )
    
    return metrics


@router.get("/user-activity")
async def get_user_activity(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    days: int = Query(30, ge=1, le=365, description="Number of days to include"),
):
    """
    Get user activity analytics.
    
    Args:
        db: Database session
        current_user: Current authenticated user
        days: Number of days to include
        
    Returns:
        User activity data
    """
    analytics_service = AnalyticsService(db)
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    metrics = await analytics_service._get_user_activity_metrics(
        company_id=current_user.company_id,
        date_range=(start_date, end_date)
    )
    
    return metrics


@router.get("/course-performance")
async def get_course_performance(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    days: int = Query(30, ge=1, le=365, description="Number of days to include"),
):
    """
    Get course performance analytics.
    
    Args:
        db: Database session
        current_user: Current authenticated user
        days: Number of days to include
        
    Returns:
        Course performance data
    """
    analytics_service = AnalyticsService(db)
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    metrics = await analytics_service._get_course_performance_metrics(
        company_id=current_user.company_id,
        date_range=(start_date, end_date)
    )
    
    return metrics


@router.get("/phishing-stats")
async def get_phishing_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    days: int = Query(30, ge=1, le=365, description="Number of days to include"),
):
    """
    Get phishing simulation statistics.
    
    Args:
        db: Database session
        current_user: Current authenticated user
        days: Number of days to include
        
    Returns:
        Phishing statistics
    """
    analytics_service = AnalyticsService(db)
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    stats = await analytics_service._get_phishing_stats(
        company_id=current_user.company_id,
        date_range=(start_date, end_date)
    )
    
    return stats


@router.get("/security-score")
async def get_security_score(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get company security score.
    
    Args:
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Security score and breakdown
    """
    analytics_service = AnalyticsService(db)
    
    score_data = await analytics_service._calculate_security_score(
        company_id=current_user.company_id
    )
    
    return score_data


@router.get("/risk-assessment")
async def get_risk_assessment(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get risk assessment for the company.
    
    Args:
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Risk assessment data
    """
    analytics_service = AnalyticsService(db)
    
    risk_data = await analytics_service._get_risk_assessment(
        company_id=current_user.company_id
    )
    
    return risk_data


@router.get("/compliance-report")
async def generate_compliance_report(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_company_admin),
    report_type: str = Query("monthly", regex="^(monthly|quarterly|annual)$", description="Report type"),
):
    """
    Generate compliance report (admin only).
    
    Args:
        db: Database session
        current_user: Current authenticated user (must be admin)
        report_type: Type of report (monthly, quarterly, annual)
        
    Returns:
        Compliance report data
    """
    analytics_service = AnalyticsService(db)
    
    report = await analytics_service.generate_compliance_report(
        company_id=current_user.company_id,
        report_type=report_type
    )
    
    return report


@router.get("/export")
async def export_analytics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_company_admin),
    format: str = Query("json", regex="^(json|csv)$", description="Export format"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
):
    """
    Export analytics data (admin only).
    
    Args:
        db: Database session
        current_user: Current authenticated user (must be admin)
        format: Export format (json or csv)
        start_date: Optional start date
        end_date: Optional end date
        
    Returns:
        Exported data in requested format
    """
    analytics_service = AnalyticsService(db)
    
    # Set default date range
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=30)
        
    # Get data
    data = await analytics_service.get_dashboard_metrics(
        company_id=current_user.company_id,
        date_range=(start_date, end_date)
    )
    
    if format == "csv":
        # TODO: Implement CSV export
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="CSV export not yet implemented"
        )
        
    return data