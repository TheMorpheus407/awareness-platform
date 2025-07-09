"""Monitoring setup for Sentry and Prometheus."""

import time
from typing import Callable, Optional

import logging
import sentry_sdk
from fastapi import Request, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse

from core.config import settings
from core.logging import logger

# Prometheus metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"]
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint"]
)

ACTIVE_REQUESTS = Gauge(
    "http_requests_active",
    "Active HTTP requests"
)

DATABASE_CONNECTIONS = Gauge(
    "database_connections_active",
    "Active database connections"
)

CACHE_HITS = Counter(
    "cache_hits_total",
    "Total cache hits",
    ["cache_type"]
)

CACHE_MISSES = Counter(
    "cache_misses_total",
    "Total cache misses",
    ["cache_type"]
)

USER_REGISTRATIONS = Counter(
    "user_registrations_total",
    "Total user registrations"
)

USER_LOGINS = Counter(
    "user_logins_total",
    "Total user logins",
    ["auth_method"]
)

FAILED_LOGINS = Counter(
    "user_failed_logins_total",
    "Total failed login attempts"
)

TWO_FACTOR_SETUPS = Counter(
    "two_factor_setups_total",
    "Total 2FA setups"
)

EMAIL_SENT = Counter(
    "emails_sent_total",
    "Total emails sent",
    ["email_type"]
)

EMAIL_FAILURES = Counter(
    "email_failures_total",
    "Total email failures",
    ["email_type", "error_type"]
)

PAYMENT_TRANSACTIONS = Counter(
    "payment_transactions_total",
    "Total payment transactions",
    ["status", "payment_method"]
)

PAYMENT_AMOUNT = Histogram(
    "payment_amount_euros",
    "Payment amounts in euros",
    buckets=[10, 25, 50, 100, 250, 500, 1000, 2500, 5000]
)


def init_sentry() -> None:
    """Initialize Sentry error tracking."""
    if settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.SENTRY_ENVIRONMENT or settings.ENVIRONMENT,
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                LoggingIntegration(
                    level=logging.INFO,  # Capture info and above as breadcrumbs
                    event_level=logging.ERROR  # Send errors as events
                ),
                SqlalchemyIntegration(),
            ],
            # Set profiles_sample_rate to 1.0 to profile 100%
            # of sampled transactions.
            # We recommend adjusting this value in production.
            profiles_sample_rate=0.1 if settings.is_production else 0.0,
            # Additional options
            attach_stacktrace=True,
            send_default_pii=False,  # Don't send personally identifiable information
            before_send=before_send_filter,
            release=settings.APP_VERSION,
        )
        logger.info("Sentry initialized successfully")
    else:
        logger.warning("Sentry DSN not configured, error tracking disabled")


def before_send_filter(event: dict, hint: dict) -> Optional[dict]:
    """Filter sensitive data before sending to Sentry."""
    # Filter out health check endpoints
    if "request" in event and "url" in event["request"]:
        url = event["request"]["url"]
        if any(path in url for path in ["/health", "/metrics", "/docs", "/openapi.json"]):
            return None
    
    # Remove sensitive headers
    if "request" in event and "headers" in event["request"]:
        sensitive_headers = ["authorization", "cookie", "x-api-key", "x-csrf-token"]
        event["request"]["headers"] = {
            k: v for k, v in event["request"]["headers"].items()
            if k.lower() not in sensitive_headers
        }
    
    # Remove sensitive data from extra context
    if "extra" in event:
        sensitive_keys = ["password", "token", "secret", "api_key", "credit_card"]
        event["extra"] = {
            k: "[REDACTED]" if any(s in k.lower() for s in sensitive_keys) else v
            for k, v in event["extra"].items()
        }
    
    return event


class MonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware for monitoring requests with Prometheus."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Monitor request metrics."""
        # Skip monitoring for certain endpoints
        if request.url.path in ["/metrics", "/health", "/api/health"]:
            return await call_next(request)
        
        # Increment active requests
        ACTIVE_REQUESTS.inc()
        
        # Start timing
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Get endpoint path for grouping
        endpoint = request.url.path
        
        # Update metrics
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=endpoint,
            status_code=response.status_code
        ).inc()
        
        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=endpoint
        ).observe(duration)
        
        # Decrement active requests
        ACTIVE_REQUESTS.dec()
        
        return response


async def metrics_endpoint(request: Request) -> StarletteResponse:
    """Endpoint to expose Prometheus metrics."""
    if not settings.PROMETHEUS_ENABLED:
        return StarletteResponse(
            content="Metrics disabled",
            status_code=503,
            media_type="text/plain"
        )
    
    metrics = generate_latest()
    return StarletteResponse(
        content=metrics,
        media_type="text/plain; version=0.0.4"
    )


# Monitoring utility functions
def track_user_registration():
    """Track a user registration event."""
    USER_REGISTRATIONS.inc()


def track_user_login(auth_method: str = "password"):
    """Track a successful user login."""
    USER_LOGINS.labels(auth_method=auth_method).inc()


def track_failed_login():
    """Track a failed login attempt."""
    FAILED_LOGINS.inc()


def track_2fa_setup():
    """Track a 2FA setup."""
    TWO_FACTOR_SETUPS.inc()


def track_email_sent(email_type: str):
    """Track a sent email."""
    EMAIL_SENT.labels(email_type=email_type).inc()


def track_email_failure(email_type: str, error_type: str):
    """Track an email failure."""
    EMAIL_FAILURES.labels(email_type=email_type, error_type=error_type).inc()


def track_payment(status: str, payment_method: str, amount: float):
    """Track a payment transaction."""
    PAYMENT_TRANSACTIONS.labels(status=status, payment_method=payment_method).inc()
    if status == "successful":
        PAYMENT_AMOUNT.observe(amount)


def track_cache_hit(cache_type: str = "redis"):
    """Track a cache hit."""
    CACHE_HITS.labels(cache_type=cache_type).inc()


def track_cache_miss(cache_type: str = "redis"):
    """Track a cache miss."""
    CACHE_MISSES.labels(cache_type=cache_type).inc()


def update_database_connections(count: int):
    """Update active database connection count."""
    DATABASE_CONNECTIONS.set(count)