"""API routes."""

from . import (
    auth, users, companies, health, email_verification,
    password_reset, two_factor, payments,
    courses, enrollments, quizzes, certificates, content,
    analytics
)

__all__ = [
    "auth", "users", "companies", "health", "email_verification",
    "password_reset", "two_factor", "payments",
    "courses", "enrollments", "quizzes", "certificates", "content",
    "analytics"
]