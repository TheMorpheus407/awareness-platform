"""Simplified API module for MVP."""
from fastapi import APIRouter

from .routes import courses, phishing, analytics

# Create main API router
api_router = APIRouter(prefix="/v1")

# Include all route modules
api_router.include_router(courses.router)
api_router.include_router(phishing.router)
api_router.include_router(analytics.router)