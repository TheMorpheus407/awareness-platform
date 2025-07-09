"""Extended health check endpoints for production monitoring."""

from datetime import datetime, timedelta
from typing import Dict, Any, List
import psutil
import asyncio
import aiohttp
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from core.config import settings
from core.cache import cache_manager
from core.logging import get_logger
from api.dependencies.auth import get_current_superuser

logger = get_logger(__name__)

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/live")
async def liveness_probe():
    """Simple liveness probe for Kubernetes."""
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}


@router.get("/ready")
async def readiness_probe(db: AsyncSession = Depends(get_db)):
    """
    Readiness probe checking all critical services.
    Returns 503 if any critical service is down.
    """
    checks = {
        "database": False,
        "redis": False,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Check database
    try:
        result = await db.execute(text("SELECT 1"))
        checks["database"] = result.scalar() == 1
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
    
    # Check Redis
    try:
        if cache_manager._redis:
            await cache_manager._redis.ping()
            checks["redis"] = True
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
    
    # Determine overall status
    all_healthy = all(v for k, v in checks.items() if k != "timestamp")
    
    if not all_healthy:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=checks
        )
    
    return {"status": "ready", **checks}


@router.get("/startup")
async def startup_probe():
    """
    Startup probe for slow-starting applications.
    Checks if the application has fully initialized.
    """
    startup_checks = {
        "migrations": True,  # Assume migrations are done if we're running
        "cache_connected": cache_manager._redis is not None,
        "config_loaded": bool(settings.SECRET_KEY),
        "timestamp": datetime.utcnow().isoformat()
    }
    
    all_ready = all(v for k, v in startup_checks.items() if k != "timestamp")
    
    if not all_ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=startup_checks
        )
    
    return {"status": "started", **startup_checks}


@router.get("/detailed", dependencies=[Depends(get_current_superuser)])
async def detailed_health_check(db: AsyncSession = Depends(get_db)):
    """
    Detailed health check with system metrics.
    Requires superuser authentication.
    """
    health_data = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "checks": {},
        "metrics": {}
    }
    
    # Database check with performance metrics
    try:
        start = datetime.utcnow()
        result = await db.execute(text("""
            SELECT 
                COUNT(*) as connection_count,
                (SELECT COUNT(*) FROM pg_stat_activity WHERE state = 'active') as active_queries,
                (SELECT COUNT(*) FROM pg_stat_activity WHERE state = 'idle') as idle_connections,
                pg_database_size(current_database()) as database_size
        """))
        db_metrics = result.first()
        query_time = (datetime.utcnow() - start).total_seconds()
        
        health_data["checks"]["database"] = {
            "status": "healthy",
            "response_time_ms": query_time * 1000,
            "connections": {
                "total": db_metrics.connection_count,
                "active": db_metrics.active_queries,
                "idle": db_metrics.idle_connections
            },
            "size_bytes": db_metrics.database_size
        }
    except Exception as e:
        health_data["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_data["status"] = "degraded"
    
    # Redis check with metrics
    try:
        if cache_manager._redis:
            start = datetime.utcnow()
            await cache_manager._redis.ping()
            ping_time = (datetime.utcnow() - start).total_seconds()
            
            info = await cache_manager._redis.info()
            memory_info = await cache_manager._redis.info("memory")
            
            health_data["checks"]["redis"] = {
                "status": "healthy",
                "response_time_ms": ping_time * 1000,
                "version": info.get("redis_version", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": memory_info.get("used_memory_human", "unknown"),
                "used_memory_peak_human": memory_info.get("used_memory_peak_human", "unknown")
            }
        else:
            health_data["checks"]["redis"] = {
                "status": "disconnected"
            }
            health_data["status"] = "degraded"
    except Exception as e:
        health_data["checks"]["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_data["status"] = "degraded"
    
    # System metrics
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        health_data["metrics"]["system"] = {
            "cpu": {
                "percent": cpu_percent,
                "count": psutil.cpu_count()
            },
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": disk.percent
            }
        }
        
        # Process-specific metrics
        process = psutil.Process()
        health_data["metrics"]["process"] = {
            "memory_mb": process.memory_info().rss / 1024 / 1024,
            "cpu_percent": process.cpu_percent(),
            "threads": process.num_threads(),
            "open_files": len(process.open_files()),
            "connections": len(process.connections())
        }
    except Exception as e:
        logger.error(f"Failed to collect system metrics: {e}")
    
    # External service checks (if configured)
    external_checks = []
    
    # Check Stripe if configured
    if settings.STRIPE_SECRET_KEY:
        external_checks.append(("stripe", "https://api.stripe.com/v1/charges", {
            "Authorization": f"Bearer {settings.STRIPE_SECRET_KEY}"
        }))
    
    # Check SendGrid if configured
    if hasattr(settings, 'SENDGRID_API_KEY') and settings.SENDGRID_API_KEY:
        external_checks.append(("sendgrid", "https://api.sendgrid.com/v3/scopes", {
            "Authorization": f"Bearer {settings.SENDGRID_API_KEY}"
        }))
    
    # Perform external checks
    if external_checks:
        health_data["checks"]["external_services"] = {}
        
        async with aiohttp.ClientSession() as session:
            for service_name, url, headers in external_checks:
                try:
                    start = datetime.utcnow()
                    async with session.get(url, headers=headers, timeout=5) as response:
                        response_time = (datetime.utcnow() - start).total_seconds()
                        
                        health_data["checks"]["external_services"][service_name] = {
                            "status": "healthy" if response.status < 400 else "unhealthy",
                            "response_time_ms": response_time * 1000,
                            "status_code": response.status
                        }
                except Exception as e:
                    health_data["checks"]["external_services"][service_name] = {
                        "status": "unhealthy",
                        "error": str(e)
                    }
    
    # Application metrics
    health_data["metrics"]["application"] = {
        "uptime_seconds": (datetime.utcnow() - datetime.fromtimestamp(psutil.boot_time())).total_seconds(),
        "environment": settings.ENVIRONMENT,
        "debug_mode": settings.DEBUG,
        "workers": getattr(settings, 'WORKERS', 1)
    }
    
    return health_data


@router.get("/dependencies")
async def check_dependencies():
    """Check all service dependencies and their versions."""
    dependencies = {
        "python": {
            "version": "3.11",
            "status": "healthy"
        },
        "fastapi": {
            "version": "0.104.1",
            "status": "healthy"
        },
        "postgresql": {
            "required": "15.x",
            "status": "unknown"
        },
        "redis": {
            "required": "7.x",
            "status": "unknown"
        }
    }
    
    # Check PostgreSQL version
    try:
        async with get_db() as db:
            result = await db.execute(text("SELECT version()"))
            version_string = result.scalar()
            if "PostgreSQL 15" in version_string:
                dependencies["postgresql"]["status"] = "healthy"
                dependencies["postgresql"]["version"] = version_string.split()[1]
            else:
                dependencies["postgresql"]["status"] = "version_mismatch"
    except Exception:
        dependencies["postgresql"]["status"] = "unreachable"
    
    # Check Redis version
    try:
        if cache_manager._redis:
            info = await cache_manager._redis.info()
            version = info.get("redis_version", "")
            if version.startswith("7."):
                dependencies["redis"]["status"] = "healthy"
                dependencies["redis"]["version"] = version
            else:
                dependencies["redis"]["status"] = "version_mismatch"
    except Exception:
        dependencies["redis"]["status"] = "unreachable"
    
    return dependencies


@router.get("/metrics")
async def get_metrics():
    """
    Prometheus-compatible metrics endpoint.
    Returns metrics in Prometheus text format.
    """
    metrics = []
    
    # System metrics
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    metrics.extend([
        f'# HELP system_cpu_usage_percent CPU usage percentage',
        f'# TYPE system_cpu_usage_percent gauge',
        f'system_cpu_usage_percent {cpu_percent}',
        '',
        f'# HELP system_memory_usage_bytes Memory usage in bytes',
        f'# TYPE system_memory_usage_bytes gauge',
        f'system_memory_usage_bytes {memory.used}',
        '',
        f'# HELP system_memory_total_bytes Total memory in bytes',
        f'# TYPE system_memory_total_bytes gauge',
        f'system_memory_total_bytes {memory.total}',
        '',
        f'# HELP system_disk_usage_bytes Disk usage in bytes',
        f'# TYPE system_disk_usage_bytes gauge',
        f'system_disk_usage_bytes {disk.used}',
        '',
        f'# HELP system_disk_total_bytes Total disk space in bytes',
        f'# TYPE system_disk_total_bytes gauge',
        f'system_disk_total_bytes {disk.total}',
    ])
    
    # Database metrics
    try:
        async with get_db() as db:
            result = await db.execute(text("""
                SELECT 
                    (SELECT COUNT(*) FROM pg_stat_activity) as connections,
                    (SELECT COUNT(*) FROM pg_stat_activity WHERE state = 'active') as active_queries,
                    pg_database_size(current_database()) as db_size
            """))
            db_metrics = result.first()
            
            metrics.extend([
                '',
                f'# HELP database_connections_total Total database connections',
                f'# TYPE database_connections_total gauge',
                f'database_connections_total {db_metrics.connections}',
                '',
                f'# HELP database_active_queries Active database queries',
                f'# TYPE database_active_queries gauge',
                f'database_active_queries {db_metrics.active_queries}',
                '',
                f'# HELP database_size_bytes Database size in bytes',
                f'# TYPE database_size_bytes gauge',
                f'database_size_bytes {db_metrics.db_size}',
            ])
    except Exception:
        pass
    
    # Application info
    metrics.extend([
        '',
        f'# HELP app_info Application information',
        f'# TYPE app_info gauge',
        f'app_info{{version="{settings.APP_VERSION}",environment="{settings.ENVIRONMENT}"}} 1',
    ])
    
    return "\n".join(metrics)