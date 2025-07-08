"""Company model."""

from typing import TYPE_CHECKING, List
import enum

from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, String, Text
from sqlalchemy.orm import relationship

from .base import Base

if TYPE_CHECKING:
    from .user import User


class CompanySize(str, enum.Enum):
    """Company size enumeration."""
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    ENTERPRISE = "enterprise"


class CompanyStatus(str, enum.Enum):
    """Company status enumeration."""
    TRIAL = "trial"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"


class SubscriptionTier(str, enum.Enum):
    """Subscription tier enumeration."""
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class Company(Base):
    """Company model for multi-tenant support."""
    
    __tablename__ = "companies"
    
    # Basic information
    name = Column(String(255), nullable=False)
    domain = Column(String(255), nullable=False, unique=True, index=True)
    size = Column(Enum(CompanySize), nullable=False, default=CompanySize.SMALL)
    status = Column(Enum(CompanyStatus), nullable=False, default=CompanyStatus.TRIAL)
    
    # Subscription
    subscription_tier = Column(Enum(SubscriptionTier), nullable=False, default=SubscriptionTier.FREE)
    max_users = Column(Integer, nullable=False, default=10)
    
    # Company details
    industry = Column(String(100), nullable=True)
    country = Column(String(2), nullable=False, default="DE")
    timezone = Column(String(50), nullable=False, default="Europe/Berlin")
    
    # Branding
    logo_url = Column(Text, nullable=True)
    primary_color = Column(String(7), nullable=True, default="#1976d2")
    secondary_color = Column(String(7), nullable=True, default="#dc004e")
    
    # Subscription
    trial_ends_at = Column(DateTime(timezone=True), nullable=True)
    subscription_ends_at = Column(DateTime(timezone=True), nullable=True)
    max_users = Column(Integer, nullable=False, default=50)
    
    # Soft delete
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    users = relationship("User", back_populates="company", lazy="dynamic")
    
    def __repr__(self) -> str:
        return f"<Company {self.name}>"
    
    @property
    def employee_count(self) -> int:
        """Get the number of employees in the company."""
        return self.users.filter_by(is_active=True, deleted_at=None).count()
    
    @property
    def is_trial(self) -> bool:
        """Check if company is in trial mode."""
        return self.status == CompanyStatus.TRIAL
    
    @property
    def is_active(self) -> bool:
        """Check if company is active."""
        return self.status == CompanyStatus.ACTIVE
    
    @property
    def is_suspended(self) -> bool:
        """Check if company is suspended."""
        return self.status == CompanyStatus.SUSPENDED