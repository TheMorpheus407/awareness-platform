"""Monitoring and health check endpoints."""

from typing import Any, Dict
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Response, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from prometheus_client import generate_latest

from core.database import get_db
from core.monitoring import HealthChecker, metrics_collector
from models.user import User
from api.dependencies import get_current_user_optional
from core.config import settings

router = APIRouter()


@router.get("/health", tags=["monitoring"])
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint.
    
    Returns simple status for load balancer health checks.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.APP_VERSION
    }


@router.get("/health/detailed", tags=["monitoring"])
async def detailed_health_check(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional)
) -> Dict[str, Any]:
    """
    Detailed health check endpoint.
    
    Returns comprehensive system health information.
    Requires authentication in production.
    """
    # In production, require authentication
    if settings.ENVIRONMENT == "production" and not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Run all health checks
    health_status = await HealthChecker.check_all(db)
    
    return health_status


@router.get("/metrics", tags=["monitoring"])
async def metrics_endpoint(
    current_user: User = Depends(get_current_user_optional)
) -> Response:
    """
    Prometheus metrics endpoint.
    
    Returns metrics in Prometheus format.
    Requires authentication in production.
    """
    # In production, require authentication
    if settings.ENVIRONMENT == "production" and not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Generate Prometheus metrics
    metrics = generate_latest()
    
    return Response(content=metrics, media_type="text/plain; version=0.0.4")


@router.get("/status", tags=["monitoring"])
async def system_status(
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    System status endpoint.
    
    Returns current system operational status.
    """
    # Get basic health
    health = await HealthChecker.check_all(db)
    
    # Add uptime information
    # This would typically come from a monitoring service
    status = {
        "operational": health["status"] == "healthy",
        "status": health["status"],
        "timestamp": health["timestamp"],
        "version": health["version"],
        "environment": health["environment"],
        "components": {
            "api": "operational" if health["status"] == "healthy" else "degraded",
            "database": health["checks"]["database"]["status"],
            "system": "operational" if all(
                check["status"] == "healthy" 
                for check in [
                    health["checks"]["disk"],
                    health["checks"]["memory"],
                    health["checks"]["cpu"]
                ]
            ) else "degraded"
        }
    }
    
    return status


@router.post("/track/event", tags=["monitoring"])
async def track_event(
    event_type: str,
    event_data: Dict[str, Any],
    current_user: User = Depends(get_current_user_optional)
) -> Dict[str, str]:
    """
    Track custom application events.
    
    Used for tracking user actions and business metrics.
    """
    # Track different event types
    if event_type == "course_completed" and "course_id" in event_data:
        metrics_collector.track_course_completion(event_data["course_id"])
    
    elif event_type == "user_active" and current_user:
        metrics_collector.track_active_user(str(current_user.id))
    
    elif event_type == "payment" and all(k in event_data for k in ["status", "method"]):
        metrics_collector.track_payment(
            event_data["status"],
            event_data["method"]
        )
    
    # Log the event for analysis
    from loguru import logger
    logger.info(f"Event tracked: {event_type}", event_data=event_data)
    
    return {"status": "tracked", "event_type": event_type}


@router.get("/logs/recent", tags=["monitoring"])
async def recent_logs(
    lines: int = 100,
    level: str = "INFO",
    current_user: User = Depends(get_current_user_optional)
) -> Dict[str, Any]:
    """
    Get recent application logs.
    
    Requires authentication. For development/debugging purposes.
    """
    # Require authentication
    if not current_user or not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # In production, this would query a log aggregation service
    # For now, return a sample response
    return {
        "logs": [
            {
                "timestamp": datetime.utcnow().isoformat(),
                "level": level,
                "message": "Sample log entry",
                "context": {}
            }
        ],
        "total": 1,
        "filters": {
            "lines": lines,
            "level": level
        }
    }


@router.get("/performance/summary", tags=["monitoring"])
async def performance_summary(
    timeframe: str = "1h",
    current_user: User = Depends(get_current_user_optional)
) -> Dict[str, Any]:
    """
    Get performance summary.
    
    Returns key performance metrics for the specified timeframe.
    """
    # In production, require authentication
    if settings.ENVIRONMENT == "production" and not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Parse timeframe
    timeframe_map = {
        "1h": timedelta(hours=1),
        "24h": timedelta(days=1),
        "7d": timedelta(days=7),
        "30d": timedelta(days=30)
    }
    
    if timeframe not in timeframe_map:
        raise HTTPException(status_code=400, detail="Invalid timeframe")
    
    # In a real implementation, this would query metrics storage
    # For now, return sample data
    return {
        "timeframe": timeframe,
        "metrics": {
            "avg_response_time_ms": 125.5,
            "p95_response_time_ms": 450.2,
            "p99_response_time_ms": 890.1,
            "total_requests": 15234,
            "error_rate": 0.002,
            "active_users": 142,
            "course_completions": 28,
            "successful_payments": 15
        },
        "trends": {
            "response_time": "stable",
            "traffic": "increasing",
            "errors": "decreasing"
        }
    }


@router.get("/alerts/active", tags=["monitoring"])
async def active_alerts(
    current_user: User = Depends(get_current_user_optional)
) -> Dict[str, Any]:
    """
    Get active system alerts.
    
    Returns any active alerts or warnings.
    """
    # Require authentication
    if not current_user or not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Check system health
    health = await HealthChecker.check_all()
    
    alerts = []
    
    # Check for system issues
    if health["checks"]["disk"]["usage_percent"] > 80:
        alerts.append({
            "id": "disk_space_warning",
            "severity": "warning" if health["checks"]["disk"]["usage_percent"] < 90 else "critical",
            "title": "Low Disk Space",
            "message": f"Disk usage at {health['checks']['disk']['usage_percent']}%",
            "timestamp": datetime.utcnow().isoformat()
        })
    
    if health["checks"]["memory"]["usage_percent"] > 80:
        alerts.append({
            "id": "high_memory_usage",
            "severity": "warning" if health["checks"]["memory"]["usage_percent"] < 90 else "critical",
            "title": "High Memory Usage",
            "message": f"Memory usage at {health['checks']['memory']['usage_percent']}%",
            "timestamp": datetime.utcnow().isoformat()
        })
    
    return {
        "alerts": alerts,
        "total": len(alerts),
        "status": "all_clear" if not alerts else "has_alerts"
    }