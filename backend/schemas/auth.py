"""
Authentication-related schemas for the application.
"""

from datetime import datetime
from typing import Optional

from pydantic import EmailStr, Field, field_validator

from .base import BaseSchema
from .company import Company
from .user import User


class TokenResponse(BaseSchema):
    """OAuth2 compatible token response."""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: Optional[str] = Field(None, description="JWT refresh token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(1800, description="Token validity in seconds")
    scope: Optional[str] = Field(None, description="Token scope")


class LoginRequest(BaseSchema):
    """Login request schema."""

    username: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=1)
    grant_type: str = Field("password", description="OAuth2 grant type")
    scope: Optional[str] = Field(None, description="Requested scope")
    remember_me: bool = Field(False, description="Extended session duration")

    @field_validator("username")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        """Normalize email to lowercase."""
        return v.lower()


class RefreshTokenRequest(BaseSchema):
    """Refresh token request schema."""

    refresh_token: str = Field(..., description="Valid refresh token")
    grant_type: str = Field("refresh_token", description="OAuth2 grant type")


class ForgotPasswordRequest(BaseSchema):
    """Forgot password request schema."""

    email: EmailStr = Field(..., description="User email address")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        """Normalize email to lowercase."""
        return v.lower()


class ResetPasswordRequest(BaseSchema):
    """Reset password request schema."""

    token: str = Field(..., description="Password reset token")
    new_password: str = Field(
        ...,
        min_length=8,
        description="Password must contain uppercase, lowercase, number and special character",
    )
    confirm_password: str = Field(..., min_length=8)

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        """Ensure passwords match."""
        if "new_password" in info.data and v != info.data["new_password"]:
            raise ValueError("Passwords do not match")
        return v


class VerifyEmailRequest(BaseSchema):
    """Email verification request schema."""

    token: str = Field(..., description="Email verification token")


class RegistrationResponse(BaseSchema):
    """Registration response with company and user details."""

    company: Company
    user: User
    message: str = Field("Registration successful. Please check your email to verify your account.")
    verification_email_sent: bool = Field(True)


class TwoFactorSetupRequest(BaseSchema):
    """Two-factor authentication setup request."""

    password: str = Field(..., description="Current password for verification")


class TwoFactorSetupResponse(BaseSchema):
    """Two-factor authentication setup response."""

    secret: str = Field(..., description="TOTP secret key")
    qr_code: str = Field(..., description="QR code as base64 image")
    backup_codes: list[str] = Field(..., description="Backup recovery codes")


class TwoFactorVerifyRequest(BaseSchema):
    """Two-factor authentication verification request."""

    code: str = Field(..., pattern=r"^\d{6}$", description="6-digit TOTP code")


class TwoFactorLoginRequest(BaseSchema):
    """Two-factor authentication during login."""

    session_token: str = Field(..., description="Temporary session token from login")
    code: str = Field(..., pattern=r"^\d{6}$", description="6-digit TOTP code")


class SessionInfo(BaseSchema):
    """User session information."""

    session_id: str
    user_id: str
    created_at: datetime
    expires_at: datetime
    ip_address: str
    user_agent: Optional[str] = None
    is_active: bool = True


class ChangePasswordRequest(BaseSchema):
    """Change password request for authenticated users."""

    current_password: str = Field(..., min_length=1)
    new_password: str = Field(
        ...,
        min_length=8,
        description="Password must contain uppercase, lowercase, number and special character",
    )
    confirm_password: str = Field(..., min_length=8)
    logout_other_sessions: bool = Field(
        False, description="Logout from all other sessions"
    )

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        """Ensure passwords match."""
        if "new_password" in info.data and v != info.data["new_password"]:
            raise ValueError("Passwords do not match")
        return v


class APIKeyCreate(BaseSchema):
    """API key creation request."""

    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    expires_at: Optional[datetime] = Field(None, description="Optional expiration date")
    scopes: list[str] = Field(
        default_factory=list, description="API key permissions"
    )


class APIKeyResponse(BaseSchema):
    """API key response."""

    id: str
    name: str
    key: str = Field(..., description="API key (only shown once)")
    description: Optional[str] = None
    scopes: list[str]
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None


class AuthenticationLog(BaseSchema):
    """Authentication event log."""

    id: str
    user_id: str
    event_type: str = Field(
        ..., description="login, logout, password_change, 2fa_enabled, etc."
    )
    success: bool
    ip_address: str
    user_agent: Optional[str] = None
    location: Optional[str] = None
    timestamp: datetime
    details: Optional[dict] = None