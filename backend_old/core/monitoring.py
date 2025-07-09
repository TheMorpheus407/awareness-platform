"""Monitoring and observability module."""

import time
import psutil
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from loguru import logger
from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY
from fastapi import Request, Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings


# Initialize Sentry
def init_sentry():
    """Initialize Sentry error tracking and performance monitoring."""
    if settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                SqlalchemyIntegration(),
                LoggingIntegration(
                    level=logging.INFO,  # Capture info and above as breadcrumbs
                    event_level=logging.ERROR  # Send errors as events
                ),
            ],
            traces_sample_rate=0.1 if settings.ENVIRONMENT == "production" else 1.0,
            profiles_sample_rate=0.1 if settings.ENVIRONMENT == "production" else 1.0,
            environment=settings.ENVIRONMENT,
            release=f"{settings.APP_NAME}@{settings.APP_VERSION}",
            attach_stacktrace=True,
            send_default_pii=False,
            before_send=before_send_filter,
        )
        logger.info("Sentry initialized successfully")
    else:
        logger.warning("Sentry DSN not configured, error tracking disabled")


def before_send_filter(event, hint):
    """Filter sensitive data before sending to Sentry."""
    # Remove sensitive data from request
    if "request" in event and "data" in event["request"]:
        sensitive_fields = ["password", "token", "secret", "api_key", "credit_card"]
        for field in sensitive_fields:
            if field in event["request"]["data"]:
                event["request"]["data"][field] = "[FILTERED]"
    
    # Don't send events in development unless explicitly enabled
    if settings.ENVIRONMENT == "development" and not settings.DEBUG:
        return None
    
    return event


# Prometheus metrics
request_count = Counter(
    "app_requests_total",
    "Total number of requests",
    ["method", "endpoint", "status_code"]
)

request_duration = Histogram(
    "app_request_duration_seconds",
    "Request duration in seconds",
    ["method", "endpoint"]
)

active_users = Gauge(
    "app_active_users",
    "Number of active users"
)

db_query_duration = Histogram(
    "app_db_query_duration_seconds",
    "Database query duration in seconds",
    ["query_type"]
)

course_completions = Counter(
    "app_course_completions_total",
    "Total number of course completions",
    ["course_id"]
)

user_registrations = Counter(
    "app_user_registrations_total",
    "Total number of user registrations"
)

failed_logins = Counter(
    "app_failed_logins_total",
    "Total number of failed login attempts"
)

payment_transactions = Counter(
    "app_payment_transactions_total",
    "Total number of payment transactions",
    ["status", "payment_method"]
)

# Custom metrics tracking
class MetricsCollector:
    """Collect and track custom application metrics."""
    
    def __init__(self):
        self._active_sessions = set()
        self._last_cleanup = datetime.utcnow()
    
    def track_active_user(self, user_id: str):
        """Track active user session."""
        self._active_sessions.add((user_id, datetime.utcnow()))
        self._cleanup_sessions()
        active_users.set(len(self._active_sessions))
    
    def _cleanup_sessions(self):
        """Remove expired sessions (older than 30 minutes)."""
        if datetime.utcnow() - self._last_cleanup < timedelta(minutes=5):
            return
        
        cutoff = datetime.utcnow() - timedelta(minutes=30)
        self._active_sessions = {
            (user_id, timestamp)
            for user_id, timestamp in self._active_sessions
            if timestamp > cutoff
        }
        self._last_cleanup = datetime.utcnow()
        active_users.set(len(self._active_sessions))
    
    def track_course_completion(self, course_id: str):
        """Track course completion."""
        course_completions.labels(course_id=course_id).inc()
    
    def track_user_registration(self):
        """Track new user registration."""
        user_registrations.inc()
    
    def track_failed_login(self):
        """Track failed login attempt."""
        failed_logins.inc()
    
    def track_payment(self, status: str, payment_method: str):
        """Track payment transaction."""
        payment_transactions.labels(
            status=status,
            payment_method=payment_method
        ).inc()


# Global metrics collector instance
metrics_collector = MetricsCollector()


# Monitoring middleware
class MonitoringMiddleware:
    """Middleware for request monitoring and metrics collection."""
    
    async def __call__(self, request: Request, call_next):
        # Skip monitoring for health check and metrics endpoints
        if request.url.path in ["/health", "/metrics", "/api/health", "/api/metrics"]:
            return await call_next(request)
        
        # Start timing
        start_time = time.time()
        
        # Add request ID to Sentry scope
        with sentry_sdk.configure_scope() as scope:
            request_id = request.headers.get("X-Request-ID", "unknown")
            scope.set_tag("request_id", request_id)
            scope.set_context("request", {
                "method": request.method,
                "url": str(request.url),
                "headers": dict(request.headers),
            })
        
        # Process request
        response = None
        try:
            response = await call_next(request)
            
            # Track metrics
            duration = time.time() - start_time
            request_count.labels(
                method=request.method,
                endpoint=request.url.path,
                status_code=response.status_code
            ).inc()
            
            request_duration.labels(
                method=request.method,
                endpoint=request.url.path
            ).observe(duration)
            
            # Log slow requests
            if duration > 1.0:
                logger.warning(
                    f"Slow request: {request.method} {request.url.path} "
                    f"took {duration:.2f}s"
                )
            
            return response
            
        except Exception as e:
            # Track error metrics
            duration = time.time() - start_time
            request_count.labels(
                method=request.method,
                endpoint=request.url.path,
                status_code=500
            ).inc()
            
            # Let Sentry capture the exception
            sentry_sdk.capture_exception(e)
            raise


# Database query monitoring
@asynccontextmanager
async def monitored_db_query(query_type: str):
    """Context manager for monitoring database queries."""
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        db_query_duration.labels(query_type=query_type).observe(duration)
        
        # Log slow queries
        if duration > 0.5:
            logger.warning(
                f"Slow database query ({query_type}): {duration:.2f}s"
            )


# System health checks
class HealthChecker:
    """Comprehensive health checking system."""
    
    @staticmethod
    async def check_database(db: AsyncSession) -> Dict[str, Any]:
        """Check database health."""
        try:
            start_time = time.time()
            result = await db.execute(text("SELECT 1"))
            await db.execute(text("SELECT COUNT(*) FROM users"))
            duration = time.time() - start_time
            
            return {
                "status": "healthy",
                "response_time_ms": round(duration * 1000, 2),
                "connection_pool": {
                    "size": db.bind.pool.size(),
                    "checked_in": db.bind.pool.checkedin(),
                    "checked_out": db.bind.pool.checkedout(),
                    "overflow": db.bind.pool.overflow(),
                    "total": db.bind.pool.total()
                }
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    @staticmethod
    def check_disk_space() -> Dict[str, Any]:
        """Check disk space usage."""
        try:
            disk_usage = psutil.disk_usage('/')
            return {
                "status": "healthy" if disk_usage.percent < 90 else "warning",
                "usage_percent": disk_usage.percent,
                "free_gb": round(disk_usage.free / (1024**3), 2),
                "total_gb": round(disk_usage.total / (1024**3), 2)
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    @staticmethod
    def check_memory() -> Dict[str, Any]:
        """Check memory usage."""
        try:
            memory = psutil.virtual_memory()
            return {
                "status": "healthy" if memory.percent < 90 else "warning",
                "usage_percent": memory.percent,
                "available_gb": round(memory.available / (1024**3), 2),
                "total_gb": round(memory.total / (1024**3), 2)
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    @staticmethod
    def check_cpu() -> Dict[str, Any]:
        """Check CPU usage."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            return {
                "status": "healthy" if cpu_percent < 80 else "warning",
                "usage_percent": cpu_percent,
                "core_count": psutil.cpu_count()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    @classmethod
    async def check_all(cls, db: Optional[AsyncSession] = None) -> Dict[str, Any]:
        """Run all health checks."""
        checks = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "checks": {}
        }
        
        # System checks
        checks["checks"]["disk"] = cls.check_disk_space()
        checks["checks"]["memory"] = cls.check_memory()
        checks["checks"]["cpu"] = cls.check_cpu()
        
        # Database check
        if db:
            checks["checks"]["database"] = await cls.check_database(db)
        
        # Determine overall status
        for check in checks["checks"].values():
            if check.get("status") == "unhealthy":
                checks["status"] = "unhealthy"
                break
            elif check.get("status") == "warning" and checks["status"] != "unhealthy":
                checks["status"] = "warning"
        
        return checks


# Performance profiling decorator
def profile_performance(operation_name: str):
    """Decorator for profiling function performance."""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            with sentry_sdk.start_transaction(op=operation_name, name=func.__name__):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    duration = time.time() - start_time
                    
                    # Log slow operations
                    if duration > 1.0:
                        logger.warning(
                            f"Slow operation {operation_name}: "
                            f"{func.__name__} took {duration:.2f}s"
                        )
                    
                    return result
                except Exception as e:
                    sentry_sdk.capture_exception(e)
                    raise
        
        def sync_wrapper(*args, **kwargs):
            with sentry_sdk.start_transaction(op=operation_name, name=func.__name__):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time
                    
                    # Log slow operations
                    if duration > 1.0:
                        logger.warning(
                            f"Slow operation {operation_name}: "
                            f"{func.__name__} took {duration:.2f}s"
                        )
                    
                    return result
                except Exception as e:
                    sentry_sdk.capture_exception(e)
                    raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


# Alerting system
class AlertManager:
    """Simple alert management system."""
    
    def __init__(self):
        self.alerts = []
        self.alert_thresholds = {
            "high_error_rate": 0.05,  # 5% error rate
            "high_response_time": 2.0,  # 2 seconds
            "low_disk_space": 10,  # 10% free space
            "high_memory_usage": 90,  # 90% memory usage
        }
    
    async def check_alerts(self):
        """Check for alert conditions."""
        # This would integrate with external alerting systems
        # For now, just log critical conditions
        health = await HealthChecker.check_all()
        
        if health["checks"]["disk"]["usage_percent"] > 90:
            logger.critical(
                f"ALERT: Low disk space - {health['checks']['disk']['usage_percent']}% used"
            )
        
        if health["checks"]["memory"]["usage_percent"] > 90:
            logger.critical(
                f"ALERT: High memory usage - {health['checks']['memory']['usage_percent']}%"
            )


# Export functions and classes
__all__ = [
    "init_sentry",
    "metrics_collector",
    "MonitoringMiddleware",
    "monitored_db_query",
    "HealthChecker",
    "profile_performance",
    "AlertManager",
    "generate_latest",
]