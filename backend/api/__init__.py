"""Simplified API module."""
from fastapi import APIRouter

# Create main API router
api_router = APIRouter(prefix="/v1")

# Import only the routes we need
from .routes import auth, health

# Include simplified routes
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(health.router, prefix="/health", tags=["Health"])

# Import simplified course, phishing, and analytics if they exist
try:
    from backend.simple_api.routes import courses, phishing, analytics
    api_router.include_router(courses.router, tags=["Courses"])
    api_router.include_router(phishing.router, tags=["Phishing"])
    api_router.include_router(analytics.router, tags=["Analytics"])
except ImportError:
    pass

__all__ = ["api_router"]