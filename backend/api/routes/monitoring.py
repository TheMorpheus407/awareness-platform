"""Monitoring and metrics endpoints."""

from datetime import datetime, timedelta
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies.auth import get_current_active_user
from core.cache import cache
from core.config import settings
from core.monitoring import (
    REQUEST_COUNT,
    REQUEST_LATENCY,
    ACTIVE_REQUESTS,
    DATABASE_CONNECTIONS,
    CACHE_HITS,
    CACHE_MISSES,
)
from db.session import get_db
from models.analytics import AnalyticsEvent
from models.user import User
from schemas.monitoring import (
    MetricsResponse,
    SystemMetrics,
    DatabaseMetrics,
    CacheMetrics,
    ApplicationMetrics,
    HealthStatus,
)

router = APIRouter()


@router.get("/metrics", response_class=Response)
async def get_prometheus_metrics(
    current_user: User = Depends(get_current_active_user),
) -> Response:
    """
    Get Prometheus metrics.
    
    Returns metrics in Prometheus exposition format.
    Requires admin privileges.
    """
    if current_user.role not in ["system_admin"]:
        raise HTTPException(
            status_code=403,
            detail="Only system administrators can access metrics"
        )
    
    # Generate Prometheus metrics
    metrics_data = generate_latest()
    
    return Response(
        content=metrics_data,
        media_type=CONTENT_TYPE_LATEST,
    )


@router.get("/status", response_model=SystemMetrics)
async def get_system_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> SystemMetrics:
    """
    Get comprehensive system status.
    
    Includes database, cache, and application metrics.
    """
    if current_user.role not in ["company_admin", "system_admin"]:
        raise HTTPException(
            status_code=403,
            detail="Only administrators can access system status"
        )
    
    # Database metrics
    try:
        # Test database connection
        await db.execute(select(1))
        db_status = "healthy"
        
        # Get connection pool stats
        pool = db.bind.pool
        db_metrics = DatabaseMetrics(
            status=db_status,
            active_connections=pool.size(),
            idle_connections=pool.size() - pool.checked_out(),
            total_connections=pool.size(),
            pool_size=settings.DATABASE_POOL_SIZE,
            response_time_ms=0,  # TODO: Measure actual response time
        )
    except Exception as e:
        db_metrics = DatabaseMetrics(
            status="unhealthy",
            active_connections=0,
            idle_connections=0,
            total_connections=0,
            pool_size=settings.DATABASE_POOL_SIZE,
            response_time_ms=-1,
            error=str(e),
        )
    
    # Cache metrics
    try:
        # Test cache connection
        await cache.ping()
        cache_info = await cache.info()
        
        cache_metrics = CacheMetrics(
            status="healthy",
            connected_clients=cache_info.get("connected_clients", 0),
            used_memory_mb=cache_info.get("used_memory", 0) / 1024 / 1024,
            hit_rate=cache_info.get("keyspace_hit_ratio", 0),
            total_commands=cache_info.get("total_commands_processed", 0),
            response_time_ms=0,  # TODO: Measure actual response time
        )
    except Exception as e:
        cache_metrics = CacheMetrics(
            status="unhealthy",
            connected_clients=0,
            used_memory_mb=0,
            hit_rate=0,
            total_commands=0,
            response_time_ms=-1,
            error=str(e),
        )
    
    # Application metrics
    app_metrics = ApplicationMetrics(
        uptime_seconds=int((datetime.utcnow() - settings.STARTUP_TIME).total_seconds()),
        total_requests=request_count._value.get(),
        active_users=active_users._value.get(),
        error_rate=0,  # TODO: Calculate from metrics
        average_response_time_ms=0,  # TODO: Calculate from metrics
        memory_usage_mb=0,  # TODO: Get process memory
        cpu_usage_percent=0,  # TODO: Get CPU usage
    )
    
    return SystemMetrics(
        timestamp=datetime.utcnow(),
        status="healthy" if db_metrics.status == "healthy" and cache_metrics.status == "healthy" else "degraded",
        database=db_metrics,
        cache=cache_metrics,
        application=app_metrics,
    )


@router.get("/analytics", response_model=Dict[str, Any])
async def get_analytics_summary(
    timeframe: str = Query("24h", regex="^(1h|24h|7d|30d)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """
    Get analytics summary for monitoring dashboard.
    
    Includes user activity, system usage, and performance metrics.
    """
    if current_user.role not in ["company_admin", "system_admin"]:
        raise HTTPException(
            status_code=403,
            detail="Only administrators can access analytics"
        )
    
    # Calculate time range
    time_ranges = {
        "1h": timedelta(hours=1),
        "24h": timedelta(days=1),
        "7d": timedelta(days=7),
        "30d": timedelta(days=30),
    }
    since = datetime.utcnow() - time_ranges[timeframe]
    
    # Get analytics events
    events_query = select(
        AnalyticsEvent.event_type,
        func.count(AnalyticsEvent.id).label("count"),
    ).where(
        AnalyticsEvent.created_at >= since
    ).group_by(
        AnalyticsEvent.event_type
    )
    
    if current_user.role == "company_admin":
        events_query = events_query.where(
            AnalyticsEvent.company_id == current_user.company_id
        )
    
    result = await db.execute(events_query)
    events = result.all()
    
    # Get unique users
    users_query = select(
        func.count(func.distinct(AnalyticsEvent.user_id))
    ).where(
        AnalyticsEvent.created_at >= since
    )
    
    if current_user.role == "company_admin":
        users_query = users_query.where(
            AnalyticsEvent.company_id == current_user.company_id
        )
    
    unique_users = await db.scalar(users_query)
    
    # Build response
    event_summary = {event.event_type: event.count for event in events}
    
    return {
        "timeframe": timeframe,
        "since": since.isoformat(),
        "unique_users": unique_users or 0,
        "total_events": sum(event_summary.values()),
        "events_by_type": event_summary,
        "top_events": sorted(
            event_summary.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10],
    }


@router.get("/errors", response_model=list[dict])
async def get_recent_errors(
    limit: int = Query(100, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[dict]:
    """
    Get recent application errors.
    
    Returns error logs from various sources.
    """
    if current_user.role not in ["system_admin"]:
        raise HTTPException(
            status_code=403,
            detail="Only system administrators can access error logs"
        )
    
    # Get recent error events from analytics
    query = select(AnalyticsEvent).where(
        AnalyticsEvent.event_category == "error"
    ).order_by(
        AnalyticsEvent.created_at.desc()
    ).limit(limit)
    
    result = await db.execute(query)
    errors = result.scalars().all()
    
    return [
        {
            "id": str(error.id),
            "timestamp": error.created_at.isoformat(),
            "type": error.event_type,
            "user_id": str(error.user_id) if error.user_id else None,
            "details": error.event_data,
            "ip_address": error.ip_address,
            "user_agent": error.user_agent,
        }
        for error in errors
    ]


@router.post("/alert", status_code=204)
async def trigger_alert(
    alert_type: str,
    message: str,
    severity: str = Query("warning", regex="^(info|warning|error|critical)$"),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """
    Manually trigger a monitoring alert.
    
    Useful for testing alert systems.
    """
    if current_user.role not in ["system_admin"]:
        raise HTTPException(
            status_code=403,
            detail="Only system administrators can trigger alerts"
        )
    
    # Log the alert
    logger.log(
        severity.upper(),
        f"Manual alert triggered: {alert_type} - {message}",
        extra={
            "alert_type": alert_type,
            "triggered_by": current_user.id,
        }
    )
    
    # TODO: Send to alerting system (e.g., PagerDuty, Slack)


@router.get("/performance", response_model=dict)
async def get_performance_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """Get application performance metrics."""
    if current_user.role not in ["company_admin", "system_admin"]:
        raise HTTPException(
            status_code=403,
            detail="Only administrators can access performance metrics"
        )
    
    # TODO: Implement actual performance metrics collection
    return {
        "response_times": {
            "p50": 45,
            "p90": 120,
            "p95": 200,
            "p99": 500,
        },
        "throughput": {
            "requests_per_second": 150,
            "bytes_per_second": 1024 * 1024 * 5,  # 5MB/s
        },
        "error_rates": {
            "4xx": 0.02,  # 2%
            "5xx": 0.001,  # 0.1%
        },
        "saturation": {
            "cpu_percent": 35,
            "memory_percent": 60,
            "disk_percent": 45,
        },
    }