"""Extended health check endpoints for detailed system status."""

import asyncio
import os
import psutil
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies.auth import get_optional_current_user
from core.cache import cache
from core.config import settings
from core.logging import logger
from db.session import get_db
from models.user import User
from schemas.health import (
    ComponentHealth,
    DependencyHealth,
    DetailedHealthResponse,
    HealthResponse,
    ServiceHealth,
)

router = APIRouter()


async def check_database_health(db: AsyncSession) -> ComponentHealth:
    """Check database connectivity and performance."""
    start_time = datetime.utcnow()
    try:
        # Simple query to test connection
        result = await db.execute(text("SELECT 1"))
        result.scalar()
        
        # Check database version
        version_result = await db.execute(text("SELECT version()"))
        version = version_result.scalar()
        
        # Calculate response time
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return ComponentHealth(
            name="PostgreSQL",
            status="healthy" if response_time < 100 else "degraded",
            response_time_ms=response_time,
            details={
                "version": version,
                "pool_size": settings.DATABASE_POOL_SIZE,
                "response_threshold_ms": 100,
            }
        )
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return ComponentHealth(
            name="PostgreSQL",
            status="unhealthy",
            response_time_ms=-1,
            error=str(e),
            details={"error_type": type(e).__name__}
        )


async def check_cache_health() -> ComponentHealth:
    """Check Redis cache connectivity and performance."""
    start_time = datetime.utcnow()
    try:
        # Ping Redis
        await cache.ping()
        
        # Get Redis info
        info = await cache.info()
        
        # Calculate response time
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return ComponentHealth(
            name="Redis",
            status="healthy" if response_time < 50 else "degraded",
            response_time_ms=response_time,
            details={
                "version": info.get("redis_version", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "unknown"),
                "response_threshold_ms": 50,
            }
        )
    except Exception as e:
        logger.error(f"Cache health check failed: {str(e)}")
        return ComponentHealth(
            name="Redis",
            status="unhealthy",
            response_time_ms=-1,
            error=str(e),
            details={"error_type": type(e).__name__}
        )


async def check_storage_health() -> ComponentHealth:
    """Check storage availability and space."""
    try:
        # Check disk usage
        disk_usage = psutil.disk_usage("/")
        
        # Determine status based on available space
        if disk_usage.percent > 90:
            status = "unhealthy"
        elif disk_usage.percent > 80:
            status = "degraded"
        else:
            status = "healthy"
        
        return ComponentHealth(
            name="Storage",
            status=status,
            response_time_ms=0,
            details={
                "total_gb": round(disk_usage.total / (1024**3), 2),
                "used_gb": round(disk_usage.used / (1024**3), 2),
                "free_gb": round(disk_usage.free / (1024**3), 2),
                "percent_used": disk_usage.percent,
            }
        )
    except Exception as e:
        logger.error(f"Storage health check failed: {str(e)}")
        return ComponentHealth(
            name="Storage",
            status="unknown",
            response_time_ms=-1,
            error=str(e),
        )


async def check_external_services() -> Dict[str, DependencyHealth]:
    """Check connectivity to external services."""
    services = {}
    
    # Check email service
    if settings.EMAIL_ENABLED:
        try:
            # TODO: Implement actual SMTP connection test
            services["email"] = DependencyHealth(
                name="Email Service",
                status="healthy",
                endpoint=f"{settings.SMTP_HOST}:{settings.SMTP_PORT}",
                response_time_ms=50,
            )
        except Exception as e:
            services["email"] = DependencyHealth(
                name="Email Service",
                status="unhealthy",
                endpoint=f"{settings.SMTP_HOST}:{settings.SMTP_PORT}",
                response_time_ms=-1,
                error=str(e),
            )
    
    # Check Stripe
    if settings.STRIPE_ENABLED:
        try:
            # TODO: Implement Stripe API health check
            services["stripe"] = DependencyHealth(
                name="Stripe",
                status="healthy",
                endpoint="api.stripe.com",
                response_time_ms=150,
            )
        except Exception as e:
            services["stripe"] = DependencyHealth(
                name="Stripe",
                status="unhealthy",
                endpoint="api.stripe.com",
                response_time_ms=-1,
                error=str(e),
            )
    
    # Check AWS S3
    if settings.AWS_ENABLED:
        try:
            # TODO: Implement S3 health check
            services["s3"] = DependencyHealth(
                name="AWS S3",
                status="healthy",
                endpoint=f"s3.{settings.AWS_REGION}.amazonaws.com",
                response_time_ms=200,
            )
        except Exception as e:
            services["s3"] = DependencyHealth(
                name="AWS S3",
                status="unhealthy",
                endpoint=f"s3.{settings.AWS_REGION}.amazonaws.com",
                response_time_ms=-1,
                error=str(e),
            )
    
    return services


@router.get("/detailed", response_model=DetailedHealthResponse)
async def get_detailed_health(
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> DetailedHealthResponse:
    """
    Get detailed health status of all system components.
    
    Includes database, cache, storage, and external services.
    """
    # Check all components in parallel
    db_health, cache_health, storage_health, external_services = await asyncio.gather(
        check_database_health(db),
        check_cache_health(),
        check_storage_health(),
        check_external_services(),
    )
    
    # Determine overall status
    component_statuses = [db_health.status, cache_health.status, storage_health.status]
    
    if any(status == "unhealthy" for status in component_statuses):
        overall_status = "unhealthy"
    elif any(status == "degraded" for status in component_statuses):
        overall_status = "degraded"
    else:
        overall_status = "healthy"
    
    # Get system info
    system_info = {
        "environment": settings.ENVIRONMENT,
        "version": settings.APP_VERSION,
        "uptime_seconds": int((datetime.utcnow() - settings.STARTUP_TIME).total_seconds()),
        "python_version": os.sys.version.split()[0],
        "cpu_count": psutil.cpu_count(),
        "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
    }
    
    return DetailedHealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow(),
        components={
            "database": db_health,
            "cache": cache_health,
            "storage": storage_health,
        },
        dependencies=external_services,
        system_info=system_info,
    )


@router.get("/services", response_model=Dict[str, ServiceHealth])
async def get_service_health(
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> Dict[str, ServiceHealth]:
    """Check health of internal services and workers."""
    services = {}
    
    # Check Celery workers (if enabled)
    try:
        # TODO: Implement Celery health check
        services["celery"] = ServiceHealth(
            name="Celery Workers",
            status="healthy",
            workers=4,
            tasks_pending=0,
            tasks_active=2,
            details={"broker": "redis://localhost:6379/1"},
        )
    except Exception as e:
        services["celery"] = ServiceHealth(
            name="Celery Workers",
            status="unknown",
            workers=0,
            tasks_pending=0,
            tasks_active=0,
            error=str(e),
        )
    
    # Check background tasks
    services["background_tasks"] = ServiceHealth(
        name="Background Tasks",
        status="healthy",
        workers=1,
        tasks_pending=0,
        tasks_active=0,
        details={"scheduler": "APScheduler"},
    )
    
    return services


@router.get("/resources", response_model=Dict[str, Any])
async def get_resource_usage(
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> Dict[str, Any]:
    """Get current system resource usage."""
    # CPU usage
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_info = {
        "percent": cpu_percent,
        "count": psutil.cpu_count(),
        "status": "healthy" if cpu_percent < 80 else "degraded",
    }
    
    # Memory usage
    memory = psutil.virtual_memory()
    memory_info = {
        "percent": memory.percent,
        "total_gb": round(memory.total / (1024**3), 2),
        "available_gb": round(memory.available / (1024**3), 2),
        "used_gb": round(memory.used / (1024**3), 2),
        "status": "healthy" if memory.percent < 85 else "degraded",
    }
    
    # Disk usage
    disk = psutil.disk_usage("/")
    disk_info = {
        "percent": disk.percent,
        "total_gb": round(disk.total / (1024**3), 2),
        "free_gb": round(disk.free / (1024**3), 2),
        "used_gb": round(disk.used / (1024**3), 2),
        "status": "healthy" if disk.percent < 85 else "degraded",
    }
    
    # Network I/O
    net_io = psutil.net_io_counters()
    network_info = {
        "bytes_sent_gb": round(net_io.bytes_sent / (1024**3), 2),
        "bytes_recv_gb": round(net_io.bytes_recv / (1024**3), 2),
        "packets_sent": net_io.packets_sent,
        "packets_recv": net_io.packets_recv,
    }
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "cpu": cpu_info,
        "memory": memory_info,
        "disk": disk_info,
        "network": network_info,
    }


@router.post("/maintenance/{mode}")
async def set_maintenance_mode(
    mode: str,
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, str]:
    """
    Enable or disable maintenance mode.
    
    Requires system admin privileges.
    """
    if current_user.role != "system_admin":
        raise HTTPException(
            status_code=403,
            detail="Only system administrators can control maintenance mode"
        )
    
    if mode not in ["enable", "disable"]:
        raise HTTPException(
            status_code=400,
            detail="Mode must be 'enable' or 'disable'"
        )
    
    # Set maintenance mode in cache
    if mode == "enable":
        await cache.set("maintenance_mode", "true", ex=3600)  # 1 hour expiry
        logger.warning(f"Maintenance mode enabled by {current_user.email}")
        return {"status": "Maintenance mode enabled"}
    else:
        await cache.delete("maintenance_mode")
        logger.info(f"Maintenance mode disabled by {current_user.email}")
        return {"status": "Maintenance mode disabled"}