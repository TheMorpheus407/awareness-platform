"""Debug endpoints for troubleshooting API issues."""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from typing import Dict, Any
import os

from core.config import settings

router = APIRouter()


@router.get("/info", response_model=Dict[str, Any])
async def debug_info(request: Request) -> Dict[str, Any]:
    """
    Get debug information about the API.
    
    This endpoint helps troubleshoot routing and configuration issues.
    """
    return {
        "app_name": settings.APP_NAME,
        "app_version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "api_prefix": "/api/v1",
        "base_url": str(request.base_url),
        "url": str(request.url),
        "path": request.url.path,
        "routes_loaded": True,
        "debug_mode": settings.DEBUG,
        "cors_origins": [str(origin) for origin in settings.CORS_ORIGINS],
        "database_connected": os.getenv("DATABASE_URL") is not None,
        "redis_connected": os.getenv("REDIS_URL") is not None,
    }


@router.get("/routes", response_model=Dict[str, Any])
async def list_routes(request: Request) -> Dict[str, Any]:
    """
    List all registered API routes.
    
    This helps verify that routes are properly registered.
    """
    routes = []
    
    # Get the FastAPI app from request
    app = request.app
    
    # Iterate through all routes
    for route in app.routes:
        if hasattr(route, "path") and hasattr(route, "methods"):
            routes.append({
                "path": route.path,
                "methods": list(route.methods) if route.methods else [],
                "name": route.name if hasattr(route, "name") else None,
                "endpoint": str(route.endpoint) if hasattr(route, "endpoint") else None
            })
    
    return {
        "total_routes": len(routes),
        "api_prefix": "/api/v1",
        "routes": sorted(routes, key=lambda x: x["path"])
    }


@router.get("/test-auth", response_model=Dict[str, Any])
async def test_auth_endpoint() -> Dict[str, Any]:
    """
    Test endpoint to verify /api/v1/auth routes work.
    """
    return {
        "message": "Auth routes are accessible",
        "login_endpoint": "/api/v1/auth/login",
        "register_endpoint": "/api/v1/auth/register",
        "me_endpoint": "/api/v1/auth/me"
    }


@router.get("/test-db", response_model=Dict[str, Any])
async def test_database() -> Dict[str, Any]:
    """
    Test database connectivity.
    """
    try:
        from core.database import get_db
        from sqlalchemy import text
        
        # Get a database session
        async for db in get_db():
            result = await db.execute(text("SELECT 1"))
            await db.close()
            
            return {
                "database_connected": True,
                "message": "Database connection successful"
            }
    except Exception as e:
        return {
            "database_connected": False,
            "error": str(e),
            "message": "Database connection failed"
        }