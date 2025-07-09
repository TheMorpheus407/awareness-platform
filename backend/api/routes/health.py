"""Health check routes."""

from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from api.dependencies.common import get_db
from core.config import settings

router = APIRouter()


@router.get("/", response_model=Dict[str, Any])
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint.
    
    Returns:
        Health status and basic application info
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


@router.get("/db", response_model=Dict[str, Any])
async def database_health_check(
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Database connectivity health check.
    
    Args:
        db: Database session
        
    Returns:
        Database health status
    """
    try:
        # Execute simple query to check database connectivity
        result = await db.execute(text("SELECT 1"))
        result.scalar()
        
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }


@router.get("/ready", response_model=Dict[str, Any])
async def readiness_check(
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Readiness check for container orchestration.
    
    Args:
        db: Database session
        
    Returns:
        Application readiness status
    """
    checks = {
        "database": False,
        "redis": False,  # TODO: Add Redis check when implemented
        "storage": True,  # TODO: Add storage check when implemented
    }
    
    # Check database
    try:
        result = await db.execute(text("SELECT 1"))
        result.scalar()
        checks["database"] = True
    except Exception:
        pass
    
    # TODO: Add Redis connectivity check
    # TODO: Add storage accessibility check
    
    all_healthy = all(checks.values())
    
    return {
        "status": "ready" if all_healthy else "not_ready",
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/live", response_model=Dict[str, Any])
async def liveness_check() -> Dict[str, Any]:
    """
    Liveness check for container orchestration.
    
    Returns:
        Application liveness status
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
    }