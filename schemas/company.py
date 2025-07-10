"""Company schemas for request/response validation."""

from typing import Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field, HttpUrl

from .base import BaseSchema, IDMixin, TimestampMixin


class CompanyBase(BaseSchema):
    """Base company schema."""
    
    name: str = Field(..., min_length=1, max_length=255)
    display_name: str = Field(..., min_length=1, max_length=255)
    domain: Optional[str] = Field(None, max_length=255)
    contact_email: EmailStr
    contact_phone: Optional[str] = Field(None, max_length=20)
    contact_person: Optional[str] = Field(None, max_length=255)
    
    # Address
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    
    # Details
    industry: Optional[str] = Field(None, max_length=100)
    size: Optional[str] = Field(
        None,
        pattern="^(1-10|11-50|51-200|201-500|501-1000|1000\\+)$"
    )
    website: Optional[HttpUrl] = None


class CompanyCreate(CompanyBase):
    """Schema for creating a company."""
    
    subscription_plan: str = Field(
        default="free",
        pattern="^(free|basic|starter|premium|professional|enterprise)$"
    )


class CompanyUpdate(BaseSchema):
    """Schema for updating a company."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    display_name: Optional[str] = Field(None, min_length=1, max_length=255)
    domain: Optional[str] = Field(None, max_length=255)
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = Field(None, max_length=20)
    contact_person: Optional[str] = Field(None, max_length=255)
    
    # Address
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    
    # Details
    industry: Optional[str] = Field(None, max_length=100)
    size: Optional[str] = Field(
        None,
        pattern="^(1-10|11-50|51-200|201-500|501-1000|1000\\+)$"
    )
    website: Optional[HttpUrl] = None
    
    # Subscription
    subscription_plan: Optional[str] = Field(
        None,
        pattern="^(free|basic|starter|premium|professional|enterprise)$"
    )
    is_active: Optional[bool] = None
    
    # Branding
    logo_url: Optional[str] = None
    primary_color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    secondary_color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    
    # Settings
    settings: Optional[Dict] = None
    features: Optional[Dict] = None
    compliance_frameworks: Optional[List[str]] = None


class CompanyResponse(CompanyBase, IDMixin, TimestampMixin):
    """Schema for company response."""
    
    subscription_plan: str
    subscription_expires: Optional[str] = None
    is_active: bool
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    employee_count: int
    is_premium: bool


class CompanyInDB(CompanyResponse):
    """Schema for company in database."""
    
    settings: Optional[Dict] = None
    features: Optional[Dict] = None
    compliance_frameworks: Optional[List[str]] = None