"""API module."""

from fastapi import APIRouter

from .routes import auth, users, companies, health, email_verification, password_reset

api_router = APIRouter()

# Include routers
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(email_verification.router, prefix="/auth/email", tags=["email-verification"])
api_router.include_router(password_reset.router, prefix="/auth/password", tags=["password-reset"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(companies.router, prefix="/companies", tags=["companies"])

__all__ = ["api_router"]