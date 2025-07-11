"""Main FastAPI application."""

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from api import api_router
from core.config import settings
from core.middleware import RequestIdMiddleware, CSRFMiddleware, limiter
from core.security_headers import EnhancedSecurityHeadersMiddleware
from core.rate_limiting import EnhancedRateLimitMiddleware
from core.monitoring import init_sentry, MonitoringMiddleware
from core.cache import cache
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

# Configure logging
from core.logging import setup_logging
setup_logging()

# Initialize Sentry
init_sentry()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    
    # Initialize Redis cache
    try:
        await cache.connect()
        logger.info("Redis cache connected")
    except Exception as e:
        logger.error(f"Failed to connect to Redis cache: {e}")
        # Continue without cache in development
        if settings.ENVIRONMENT == "production":
            raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")
    
    # Disconnect from Redis
    try:
        await cache.disconnect()
        logger.info("Redis cache disconnected")
    except Exception as e:
        logger.error(f"Error disconnecting from Redis: {e}")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    openapi_url="/api/openapi.json" if settings.DEBUG else None,
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# Add security middleware
app.add_middleware(EnhancedSecurityHeadersMiddleware)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(EnhancedRateLimitMiddleware)

# Add CSRF protection
app.add_middleware(
    CSRFMiddleware,
    secret_key=settings.SECRET_KEY,
    cookie_secure=settings.is_production,
    exclude_paths={
        "/api/health",
        "/api/health/db",
        "/health",
        "/api/docs",
        "/api/redoc",
        "/api/openapi.json",
        "/api/v1/auth/login",  # Exclude login endpoint to allow initial token generation
        "/api/v1/auth/register",  # Exclude registration endpoint
    }
)

# Add monitoring middleware
app.add_middleware(MonitoringMiddleware)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add trusted host middleware
if settings.ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=[settings.FRONTEND_URL.host, "localhost", "127.0.0.1"]
    )

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.CORS_ORIGINS],
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler to catch all unhandled exceptions.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    # Don't expose internal errors in production
    if settings.DEBUG:
        return JSONResponse(
            status_code=500,
            content={
                "detail": str(exc),
                "type": type(exc).__name__,
            },
        )
    else:
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )


# Root endpoint
@app.get("/", response_model=dict)
async def root() -> Any:
    """
    Root endpoint.
    """
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/api/docs" if settings.DEBUG else "Disabled in production",
    }


# Include API router
# Note: api_router already has /v1 prefix, so we just use /api here
app.include_router(api_router, prefix="/api")


# Health check middleware for logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Log all incoming requests.
    """
    # Skip logging for health checks
    if request.url.path in ["/health", "/api/health", "/api/health/db"]:
        return await call_next(request)
    
    logger.info(f"{request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"{request.method} {request.url.path} - {response.status_code}")
    
    return response


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=1 if settings.DEBUG else settings.WORKERS,
        log_level=settings.LOG_LEVEL.lower(),
    )