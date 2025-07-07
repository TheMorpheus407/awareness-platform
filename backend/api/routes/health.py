"""Health check endpoints."""

from typing import Dict

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from core.config import settings
from db.session import get_db

router = APIRouter()


@router.get("/health", response_model=Dict[str, str])
async def health_check() -> Dict[str, str]:
    """
    Basic health check endpoint.
    
    Returns:
        Status message
    """
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@router.get("/health/db", response_model=Dict[str, str])
async def database_health_check(
    db: AsyncSession = Depends(get_db),
) -> Dict[str, str]:
    """
    Database health check endpoint.
    
    Args:
        db: Database session
        
    Returns:
        Database status
    """
    try:
        # Execute a simple query
        result = await db.execute(text("SELECT 1"))
        result.scalar()
        
        return {
            "status": "healthy",
            "database": "connected",
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
        }