"""Analytics routes."""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio

from db.session import get_db
from api.dependencies.auth import get_current_active_user, require_company_admin
from models.user import User
from models.company import Company
from services.analytics_service import AnalyticsService
from services.analytics_realtime import RealTimeAnalyticsService
from services.analytics_campaign import CampaignAnalyticsService
from services.analytics_predictive import PredictiveAnalyticsService
from services.analytics_export import AnalyticsExportService
from services.analytics_aggregation import AnalyticsAggregationService
from core.cache import cache, cached

router = APIRouter()

# Initialize services
realtime_service = None
predictive_service = None
export_service = AnalyticsExportService()


@router.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global realtime_service, predictive_service
    
    # Initialize real-time service
    # Note: This would need proper DB session in production
    # realtime_service = RealTimeAnalyticsService(db)
    # await realtime_service.initialize()
    
    # Initialize predictive service
    # predictive_service = PredictiveAnalyticsService(db)
    # await predictive_service.initialize_models()


@router.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    if realtime_service:
        await realtime_service.shutdown()


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


@router.get("/campaigns/overview")
@cached(expire=300, key_prefix="campaign_overview")
async def get_campaign_overview(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    campaign_type: Optional[str] = Query(None, regex="^(email|phishing)$", description="Campaign type filter"),
    days: int = Query(30, ge=1, le=365, description="Number of days to include"),
):
    """
    Get campaign performance overview.
    
    Args:
        db: Database session
        current_user: Current authenticated user
        campaign_type: Optional campaign type filter
        days: Number of days to include
        
    Returns:
        Campaign performance metrics
    """
    campaign_service = CampaignAnalyticsService(db)
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    overview = await campaign_service.get_campaign_overview(
        company_id=current_user.company_id,
        campaign_type=campaign_type,
        date_range=(start_date, end_date)
    )
    
    return overview


@router.get("/campaigns/{campaign_id}")
async def get_campaign_details(
    campaign_id: int,
    campaign_type: str = Query(..., regex="^(email|phishing)$", description="Campaign type"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get detailed analytics for a specific campaign.
    
    Args:
        campaign_id: Campaign ID
        campaign_type: Campaign type (email or phishing)
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Detailed campaign analytics
    """
    campaign_service = CampaignAnalyticsService(db)
    
    try:
        details = await campaign_service.get_campaign_details(
            company_id=current_user.company_id,
            campaign_id=campaign_id,
            campaign_type=campaign_type
        )
        return details
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/predictive/phishing-risk")
async def predict_phishing_risk(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    user_ids: Optional[str] = Query(None, description="Comma-separated user IDs"),
):
    """
    Predict phishing risk for users using ML models.
    
    Args:
        db: Database session
        current_user: Current authenticated user
        user_ids: Optional specific user IDs to analyze
        
    Returns:
        Phishing risk predictions
    """
    predictive_service = PredictiveAnalyticsService(db)
    await predictive_service.initialize_models()
    
    user_id_list = None
    if user_ids:
        user_id_list = [int(uid.strip()) for uid in user_ids.split(",")]
    
    predictions = await predictive_service.predict_phishing_risk(
        company_id=current_user.company_id,
        user_ids=user_id_list
    )
    
    return predictions


@router.get("/predictive/training-completion")
async def predict_training_completion(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    days_ahead: int = Query(30, ge=7, le=90, description="Prediction window in days"),
):
    """
    Predict which users will complete training.
    
    Args:
        course_id: Course ID to analyze
        db: Database session
        current_user: Current authenticated user
        days_ahead: Prediction timeframe
        
    Returns:
        Training completion predictions
    """
    predictive_service = PredictiveAnalyticsService(db)
    await predictive_service.initialize_models()
    
    predictions = await predictive_service.predict_training_completion(
        company_id=current_user.company_id,
        course_id=course_id,
        days_ahead=days_ahead
    )
    
    return predictions


@router.get("/predictive/security-incidents")
async def predict_security_incidents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_company_admin),
    timeframe_days: int = Query(30, ge=7, le=90, description="Prediction timeframe"),
):
    """
    Predict likelihood of security incidents (admin only).
    
    Args:
        db: Database session
        current_user: Current authenticated user (must be admin)
        timeframe_days: Prediction timeframe
        
    Returns:
        Security incident predictions
    """
    predictive_service = PredictiveAnalyticsService(db)
    await predictive_service.initialize_models()
    
    predictions = await predictive_service.predict_security_incidents(
        company_id=current_user.company_id,
        timeframe_days=timeframe_days
    )
    
    return predictions


@router.get("/predictive/user-churn")
async def predict_user_churn(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_company_admin),
    days_ahead: int = Query(90, ge=30, le=180, description="Prediction window"),
):
    """
    Predict users at risk of becoming inactive (admin only).
    
    Args:
        db: Database session
        current_user: Current authenticated user (must be admin)
        days_ahead: Prediction timeframe
        
    Returns:
        User churn predictions
    """
    predictive_service = PredictiveAnalyticsService(db)
    await predictive_service.initialize_models()
    
    predictions = await predictive_service.predict_user_churn(
        company_id=current_user.company_id,
        days_ahead=days_ahead
    )
    
    return predictions


@router.post("/aggregation/run")
async def run_aggregation_pipeline(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_company_admin),
    interval: str = Query("hourly", regex="^(hourly|daily|weekly|monthly)$", description="Aggregation interval"),
):
    """
    Run data aggregation pipeline (admin only).
    
    Args:
        db: Database session
        current_user: Current authenticated user (must be admin)
        interval: Aggregation interval
        
    Returns:
        Aggregation results
    """
    aggregation_service = AnalyticsAggregationService(db)
    
    results = await aggregation_service.run_aggregation_pipeline(
        company_id=current_user.company_id,
        interval=interval
    )
    
    return results


@router.websocket("/realtime")
async def websocket_endpoint(
    websocket: WebSocket,
    db: AsyncSession = Depends(get_db),
):
    """
    WebSocket endpoint for real-time analytics updates.
    
    Args:
        websocket: WebSocket connection
        db: Database session
    """
    # Note: In production, you'd need proper authentication for WebSocket
    realtime_service = RealTimeAnalyticsService(db)
    await realtime_service.initialize()
    
    # For demo purposes, using company_id 1
    company_id = 1
    
    await realtime_service.connect(websocket, company_id)
    
    try:
        while True:
            # Wait for messages from client
            data = await websocket.receive_json()
            
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            elif data.get("type") == "get_metrics":
                metrics = await realtime_service.get_live_metrics(company_id)
                await websocket.send_json({
                    "type": "metrics_update",
                    "data": metrics
                })
                
    except WebSocketDisconnect:
        await realtime_service.disconnect(websocket, company_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await realtime_service.disconnect(websocket, company_id)


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
    format: str = Query("json", regex="^(json|csv|excel|pdf)$", description="Export format"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    include_sections: Optional[str] = Query(None, description="Comma-separated sections to include"),
):
    """
    Export analytics data in various formats (admin only).
    
    Args:
        db: Database session
        current_user: Current authenticated user (must be admin)
        format: Export format (json, csv, excel, pdf)
        start_date: Optional start date
        end_date: Optional end date
        include_sections: Optional sections to include
        
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
    
    # Filter sections if specified
    if include_sections:
        sections = include_sections.split(",")
        filtered_data = {k: v for k, v in data.items() if k in sections}
        data = filtered_data
    
    # Export based on format
    if format == "csv":
        output = await export_service.export_to_csv(data)
        return StreamingResponse(
            output,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=analytics_{datetime.utcnow().strftime('%Y%m%d')}.csv"}
        )
    elif format == "excel":
        output = await export_service.export_to_excel(data)
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=analytics_{datetime.utcnow().strftime('%Y%m%d')}.xlsx"}
        )
    elif format == "pdf":
        # Get company name for PDF header
        company_query = await db.get(Company, current_user.company_id)
        company_name = company_query.name if company_query else "Company"
        
        output = await export_service.export_to_pdf(data, company_name=company_name)
        return StreamingResponse(
            output,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=analytics_report_{datetime.utcnow().strftime('%Y%m%d')}.pdf"}
        )
    else:
        # JSON format
        output = await export_service.export_to_json(data)
        return StreamingResponse(
            output,
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=analytics_{datetime.utcnow().strftime('%Y%m%d')}.json"}
        )