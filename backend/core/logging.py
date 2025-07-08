"""Custom logging configuration with loguru."""

import sys
import json
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

from loguru import logger
from fastapi import Request

from core.config import settings


class CustomFormatter:
    """Custom formatter for structured logging."""
    
    @staticmethod
    def format_record(record: Dict[str, Any]) -> str:
        """Format log record as structured JSON."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record["level"].name,
            "message": record["message"],
            "module": record["name"],
            "function": record["function"],
            "line": record["line"],
        }
        
        # Add extra fields
        if record.get("extra"):
            log_entry["extra"] = record["extra"]
        
        # Add exception info if present
        if record.get("exception"):
            log_entry["exception"] = {
                "type": record["exception"].type.__name__,
                "value": str(record["exception"].value),
                "traceback": record["exception"].traceback
            }
        
        return json.dumps(log_entry) + "\n"


def setup_logging():
    """Configure logging for the application."""
    # Remove default logger
    logger.remove()
    
    # Console logger (human-readable)
    if settings.ENVIRONMENT == "development":
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level=settings.LOG_LEVEL,
            colorize=True,
            backtrace=True,
            diagnose=True,
        )
    else:
        # Production: structured JSON logs
        logger.add(
            sys.stdout,
            format=CustomFormatter.format_record,
            level=settings.LOG_LEVEL,
            serialize=True,
            backtrace=True,
            diagnose=False,  # Don't include local variables in production
        )
    
    # File logger (always JSON)
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logger.add(
        log_dir / "app.log",
        format=CustomFormatter.format_record,
        level=settings.LOG_LEVEL,
        rotation="500 MB",
        retention="30 days",
        compression="zip",
        serialize=True,
        backtrace=True,
        diagnose=False,
    )
    
    # Error logger (separate file for errors)
    logger.add(
        log_dir / "errors.log",
        format=CustomFormatter.format_record,
        level="ERROR",
        rotation="100 MB",
        retention="90 days",
        compression="zip",
        serialize=True,
        backtrace=True,
        diagnose=True,  # Include local variables for errors
    )
    
    # Security logger (for auth events)
    logger.add(
        log_dir / "security.log",
        format=CustomFormatter.format_record,
        level="INFO",
        filter=lambda record: "security" in record["extra"],
        rotation="100 MB",
        retention="1 year",
        compression="zip",
        serialize=True,
    )
    
    # Performance logger (for slow queries and requests)
    logger.add(
        log_dir / "performance.log",
        format=CustomFormatter.format_record,
        level="WARNING",
        filter=lambda record: "performance" in record["extra"],
        rotation="100 MB",
        retention="30 days",
        compression="zip",
        serialize=True,
    )
    
    # Audit logger (for compliance)
    logger.add(
        log_dir / "audit.log",
        format=CustomFormatter.format_record,
        level="INFO",
        filter=lambda record: "audit" in record["extra"],
        rotation="100 MB",
        retention="5 years",  # Keep audit logs for compliance
        compression="zip",
        serialize=True,
    )


def log_request(request: Request, response_time: float, status_code: int):
    """Log HTTP request with context."""
    logger.info(
        f"{request.method} {request.url.path}",
        extra={
            "request_id": request.headers.get("X-Request-ID", "unknown"),
            "method": request.method,
            "path": request.url.path,
            "query": dict(request.query_params),
            "status_code": status_code,
            "response_time_ms": round(response_time * 1000, 2),
            "client_host": request.client.host if request.client else None,
            "user_agent": request.headers.get("User-Agent"),
        }
    )


def log_security_event(event_type: str, user_id: str = None, **kwargs):
    """Log security-related events."""
    logger.info(
        f"Security event: {event_type}",
        extra={
            "security": True,
            "event_type": event_type,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }
    )


def log_audit_event(action: str, user_id: str, resource: str, **kwargs):
    """Log audit events for compliance."""
    logger.info(
        f"Audit: {action} on {resource}",
        extra={
            "audit": True,
            "action": action,
            "user_id": user_id,
            "resource": resource,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }
    )


def log_performance_issue(issue_type: str, duration: float, **kwargs):
    """Log performance issues."""
    logger.warning(
        f"Performance issue: {issue_type}",
        extra={
            "performance": True,
            "issue_type": issue_type,
            "duration_seconds": round(duration, 3),
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }
    )


def log_business_event(event: str, **kwargs):
    """Log business events (registrations, payments, etc.)."""
    logger.info(
        f"Business event: {event}",
        extra={
            "business": True,
            "event": event,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }
    )


# Export logger and functions
__all__ = [
    "logger",
    "setup_logging",
    "log_request",
    "log_security_event",
    "log_audit_event",
    "log_performance_issue",
    "log_business_event",
]