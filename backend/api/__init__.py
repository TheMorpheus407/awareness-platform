"""Main API router module."""

from fastapi import APIRouter

from .routes import (
    analytics,
    auth,
    certificates,
    companies,
    content,
    courses,
    debug,
    email_campaigns,
    email_verification,
    enrollments,
    health,
    health_extended,
    monitoring,
    notifications,
    password_reset,
    payments,
    phishing,
    quizzes,
    two_factor,
    users,
)

# Create main API router with v1 prefix
api_router = APIRouter(prefix="/v1")

# Include all route modules
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(companies.router, prefix="/admin/companies", tags=["Companies"])
api_router.include_router(courses.router, prefix="/courses", tags=["Courses"])
api_router.include_router(enrollments.router, prefix="/enrollments", tags=["Enrollments"])
api_router.include_router(quizzes.router, prefix="/quizzes", tags=["Quizzes"])
api_router.include_router(certificates.router, prefix="/certificates", tags=["Certificates"])
api_router.include_router(phishing.router, prefix="/phishing", tags=["Phishing"])
api_router.include_router(analytics.router, prefix="/reports", tags=["Analytics"])
api_router.include_router(payments.router, prefix="/payments", tags=["Payments"])
api_router.include_router(email_campaigns.router, prefix="/campaigns", tags=["Email Campaigns"])
api_router.include_router(content.router, prefix="/content", tags=["Content"])
api_router.include_router(two_factor.router, prefix="/auth/2fa", tags=["Two-Factor Auth"])
api_router.include_router(password_reset.router, prefix="/auth/password-reset", tags=["Password Reset"])
api_router.include_router(email_verification.router, prefix="/auth/verify-email", tags=["Email Verification"])
api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(health_extended.router, prefix="/health", tags=["Health"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["Monitoring"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(debug.router, prefix="/debug", tags=["Debug"])

__all__ = ["api_router"]