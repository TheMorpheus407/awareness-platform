"""User schemas for request/response validation."""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from models.user import UserRole
from .base import BaseSchema, IDMixin, TimestampMixin


class UserBase(BaseSchema):
    """Base user schema."""
    
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    role: UserRole = Field(default=UserRole.EMPLOYEE)
    is_active: bool = True
    department: Optional[str] = Field(None, max_length=100)
    job_title: Optional[str] = Field(None, max_length=100)
    language: str = Field(default="de", max_length=5)


class UserCreate(UserBase):
    """Schema for creating a user."""
    
    password: str = Field(..., min_length=8, max_length=100)
    company_id: UUID  # Required for user creation
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain at least one digit")
        if not any(char.isupper() for char in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(char.islower() for char in v):
            raise ValueError("Password must contain at least one lowercase letter")
        return v


class UserUpdate(BaseSchema):
    """Schema for updating a user."""
    
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    department: Optional[str] = Field(None, max_length=100)
    job_title: Optional[str] = Field(None, max_length=100)
    language: Optional[str] = Field(None, max_length=5)
    avatar_url: Optional[str] = None


class UserResponse(UserBase, IDMixin, TimestampMixin):
    """Schema for user response."""
    
    company_id: UUID
    email_verified: bool
    email_verified_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None
    full_name: str
    is_company_admin: bool
    is_system_admin: bool
    is_manager: bool
    is_employee: bool
    avatar_url: Optional[str] = None
    totp_enabled: bool = False
    has_2fa_enabled: bool = False


class UserInDB(UserResponse):
    """Schema for user in database."""
    
    password_hash: str
    password_changed_at: Optional[datetime] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    is_locked: bool
    is_verified: bool  # Backward compatibility property


class UserLogin(BaseSchema):
    """Schema for user login."""
    
    email: EmailStr
    password: str


class Token(BaseSchema):
    """Schema for JWT token response."""
    
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseSchema):
    """Schema for JWT token payload."""
    
    sub: str
    exp: datetime
    type: str


# Two-Factor Authentication Schemas
class TwoFactorSetupRequest(BaseSchema):
    """Request to setup 2FA."""
    
    password: str  # Require password confirmation for security


class TwoFactorSetupResponse(BaseSchema):
    """Response with 2FA setup data."""
    
    secret: str
    qr_code: str  # Base64 encoded QR code image
    backup_codes: List[str]
    manual_entry_key: str  # For manual entry if QR code fails


class TwoFactorVerifyRequest(BaseSchema):
    """Request to verify 2FA setup."""
    
    totp_code: str = Field(..., min_length=6, max_length=6, pattern="^[0-9]{6}$")


class TwoFactorLoginRequest(BaseSchema):
    """Request for login with 2FA."""
    
    email: EmailStr
    password: str
    totp_code: Optional[str] = Field(None, min_length=6, max_length=6, pattern="^[0-9]{6}$")


class TwoFactorDisableRequest(BaseSchema):
    """Request to disable 2FA."""
    
    password: str  # Require password confirmation
    totp_code: str = Field(..., min_length=6, max_length=6, pattern="^[0-9]{6}$")


class BackupCodeVerifyRequest(BaseSchema):
    """Request to verify using backup code."""
    
    email: EmailStr
    password: str
    backup_code: str = Field(..., pattern="^[A-Z0-9]{4}-[A-Z0-9]{4}$")