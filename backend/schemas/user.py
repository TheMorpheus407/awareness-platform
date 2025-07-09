"""
User-related schemas for the application.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import EmailStr, Field, field_validator

from .base import BaseSchema, PaginatedResponse, TimestampMixin, UUIDMixin
from .company import Company


class UserRole(str, Enum):
    """User role enumeration."""

    ADMIN = "admin"
    MANAGER = "manager"
    EMPLOYEE = "employee"


class UserBase(BaseSchema):
    """Base user schema with common fields."""

    email: EmailStr = Field(..., description="User email address")
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    role: UserRole = Field(UserRole.EMPLOYEE, description="User role")
    department: Optional[str] = Field(None, max_length=100)


class UserCreate(UserBase):
    """Schema for creating a new user."""

    send_invite: bool = Field(True, description="Send invitation email to user")

    @field_validator("email")
    @classmethod
    def validate_email_domain(cls, v: str) -> str:
        """Ensure email is lowercase."""
        return v.lower()


class UserUpdate(BaseSchema):
    """Schema for updating an existing user."""

    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    role: Optional[UserRole] = None
    department: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None


class UserProfileUpdate(BaseSchema):
    """Schema for users updating their own profile."""

    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    department: Optional[str] = Field(None, max_length=100)


class User(UserBase, UUIDMixin, TimestampMixin):
    """User response schema."""

    is_active: bool = Field(True, description="User active status")
    is_verified: bool = Field(False, description="Email verification status")
    risk_score: float = Field(
        50.0, description="User risk score", ge=0, le=100
    )
    last_login_at: Optional[datetime] = None
    company_id: UUID = Field(..., description="Company ID")

    @field_validator("risk_score")
    @classmethod
    def round_risk_score(cls, v: float) -> float:
        """Round risk score to 2 decimal places."""
        return round(v, 2)


class UserDetail(User):
    """Detailed user response with additional information."""

    company: Company = Field(..., description="User's company")
    training_completion_rate: float = Field(
        0.0, description="Percentage of trainings completed", ge=0, le=100
    )
    phishing_click_rate: float = Field(
        0.0, description="Phishing click rate percentage", ge=0, le=100
    )
    last_training_date: Optional[datetime] = None
    courses_completed: int = Field(0, ge=0)
    courses_in_progress: int = Field(0, ge=0)
    courses_assigned: int = Field(0, ge=0)
    two_factor_enabled: bool = Field(False, description="2FA status")

    @field_validator("training_completion_rate", "phishing_click_rate")
    @classmethod
    def round_percentages(cls, v: float) -> float:
        """Round percentages to 2 decimal places."""
        return round(v, 2)


class BulkUserError(BaseSchema):
    """Error detail for bulk user operations."""

    row: int = Field(..., description="CSV row number", ge=1)
    email: str = Field(..., description="Email that failed")
    error: str = Field(..., description="Error message")


class BulkUserResponse(BaseSchema):
    """Response for bulk user creation."""

    created: int = Field(0, description="Number of users created", ge=0)
    failed: int = Field(0, description="Number of failures", ge=0)
    errors: List[BulkUserError] = Field(
        default_factory=list, description="List of errors"
    )


class UserListResponse(PaginatedResponse[User]):
    """Paginated user list response."""

    pass


class UserInvitation(BaseSchema):
    """User invitation schema."""

    id: UUID
    email: EmailStr
    token: str
    expires_at: datetime
    accepted: bool = False
    created_at: datetime


class UserPasswordChange(BaseSchema):
    """Schema for changing user password."""

    current_password: str = Field(..., min_length=8)
    new_password: str = Field(
        ...,
        min_length=8,
        pattern=r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$",
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


class UserLoginHistory(BaseSchema):
    """User login history entry."""

    id: UUID
    user_id: UUID
    ip_address: str
    user_agent: Optional[str]
    success: bool
    failure_reason: Optional[str]
    timestamp: datetime


class UserActivity(BaseSchema):
    """User activity summary."""

    user_id: UUID
    last_login: Optional[datetime]
    last_course_access: Optional[datetime]
    last_phishing_interaction: Optional[datetime]
    total_logins_30d: int = 0
    courses_completed_30d: int = 0
    phishing_reported_30d: int = 0