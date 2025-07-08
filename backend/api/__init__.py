"""API module."""

from fastapi import APIRouter

from .routes import (
    auth, users, companies, health, email_verification,
    password_reset, two_factor, payments, monitoring,
    courses, enrollments, quizzes, certificates, content,
    analytics
)

api_router = APIRouter(prefix="/v1")

# Include routers
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(email_verification.router, prefix="/auth/email", tags=["email-verification"])
api_router.include_router(password_reset.router, prefix="/auth/password", tags=["password-reset"])
api_router.include_router(two_factor.router, prefix="/auth/2fa", tags=["two-factor-auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(companies.router, prefix="/companies", tags=["companies"])
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])
api_router.include_router(courses.router, prefix="/courses", tags=["courses"])
api_router.include_router(enrollments.router, prefix="/enrollments", tags=["enrollments"])
api_router.include_router(quizzes.router, prefix="/quizzes", tags=["quizzes"])
api_router.include_router(certificates.router, prefix="/certificates", tags=["certificates"])
api_router.include_router(content.router, prefix="/content", tags=["content"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])

__all__ = ["api_router"]