"""User schemas for request/response validation."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from .base import BaseSchema, IDMixin, TimestampMixin


class UserBase(BaseSchema):
    """Base user schema."""
    
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    role: str = Field(default="user", pattern="^(user|admin|company_admin)$")
    is_active: bool = True
    company_id: Optional[int] = None


class UserCreate(UserBase):
    """Schema for creating a user."""
    
    password: str = Field(..., min_length=8, max_length=100)
    
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
    role: Optional[str] = Field(None, pattern="^(user|admin|company_admin)$")
    is_active: Optional[bool] = None
    company_id: Optional[int] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None


class UserResponse(UserBase, IDMixin, TimestampMixin):
    """Schema for user response."""
    
    is_verified: bool
    last_login: Optional[datetime] = None
    full_name: str
    is_company_admin: bool
    is_admin: bool
    avatar_url: Optional[str] = None
    bio: Optional[str] = None


class UserInDB(UserResponse):
    """Schema for user in database."""
    
    hashed_password: str
    is_superuser: bool
    email_verification_token: Optional[str] = None
    password_reset_token: Optional[str] = None
    password_reset_expires: Optional[datetime] = None
    password_changed_at: datetime


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