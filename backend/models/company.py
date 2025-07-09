"""Company model for organization management."""

from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Column, DateTime, Integer, String, text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ENUM

from .base import BaseModel, SoftDeleteMixin

if TYPE_CHECKING:
    from .user import User
    from .course import UserCourseProgress
    from .phishing import PhishingCampaign, PhishingTemplate
    from .analytics import AnalyticsEvent
    from .audit import AuditLog
    from .email_campaign import EmailCampaign
    from .payment import Subscription, PaymentMethod, Invoice, Payment


class CompanySize:
    """Company size enumeration."""
    
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    ENTERPRISE = "enterprise"


class CompanyStatus:
    """Company status enumeration."""
    
    TRIAL = "trial"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"


class SubscriptionTier:
    """Subscription tier enumeration."""
    
    FREE = "free"
    BASIC = "basic"
    STARTER = "starter"
    PREMIUM = "premium"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class Company(BaseModel, SoftDeleteMixin):
    """Company model for organization management."""
    
    __tablename__ = "companies"
    
    # Basic Information
    name = Column(String(255), nullable=False, index=True)
    domain = Column(String(255), nullable=False, unique=True, index=True)
    
    # Company Details
    size = Column(
        ENUM('small', 'medium', 'large', 'enterprise', name='companysize', create_type=False),
        nullable=False,
        server_default='small'
    )
    status = Column(
        ENUM('trial', 'active', 'suspended', 'cancelled', name='companystatus', create_type=False),
        nullable=False,
        server_default='trial'
    )
    subscription_tier = Column(
        ENUM('free', 'basic', 'starter', 'premium', 'professional', 'enterprise', name='subscriptiontier', create_type=False),
        nullable=False,
        server_default='free',
        index=True
    )
    max_users = Column(Integer, nullable=False, server_default=text('10'))
    
    # Business Information
    industry = Column(String(100), nullable=True)
    website = Column(String(255), nullable=True)
    logo_url = Column(String(500), nullable=True)
    
    # Contact Information
    country = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    address = Column(String(255), nullable=True)
    postal_code = Column(String(20), nullable=True)
    phone = Column(String(20), nullable=True)
    
    # Status
    is_active = Column(Boolean, nullable=False, server_default=text('true'), index=True)
    
    # Relationships
    users: List["User"] = relationship(
        "User",
        back_populates="company",
        cascade="all, delete-orphan"
    )
    user_course_progress: List["UserCourseProgress"] = relationship(
        "UserCourseProgress",
        back_populates="company",
        cascade="all, delete-orphan"
    )
    phishing_campaigns: List["PhishingCampaign"] = relationship(
        "PhishingCampaign",
        back_populates="company",
        cascade="all, delete-orphan"
    )
    phishing_templates: List["PhishingTemplate"] = relationship(
        "PhishingTemplate",
        back_populates="company",
        cascade="all, delete-orphan"
    )
    analytics_events: List["AnalyticsEvent"] = relationship(
        "AnalyticsEvent",
        back_populates="company"
    )
    audit_logs: List["AuditLog"] = relationship(
        "AuditLog",
        back_populates="company"
    )
    email_campaigns: List["EmailCampaign"] = relationship(
        "EmailCampaign",
        back_populates="company"
    )
    
    # Payment relationships (from migration 004)
    subscriptions: List["Subscription"] = relationship(
        "Subscription",
        back_populates="company",
        cascade="all, delete-orphan"
    )
    payment_methods: List["PaymentMethod"] = relationship(
        "PaymentMethod",
        back_populates="company",
        cascade="all, delete-orphan"
    )
    invoices: List["Invoice"] = relationship(
        "Invoice",
        back_populates="company",
        cascade="all, delete-orphan"
    )
    payments: List["Payment"] = relationship(
        "Payment",
        back_populates="company",
        cascade="all, delete-orphan"
    )
    
    @property
    def is_trial(self) -> bool:
        """Check if company is in trial period."""
        return self.status == CompanyStatus.TRIAL
    
    @property
    def is_paid(self) -> bool:
        """Check if company has a paid subscription."""
        return self.subscription_tier != SubscriptionTier.FREE
    
    @property
    def can_add_users(self, count: int = 1) -> bool:
        """Check if company can add more users."""
        if self.subscription_tier == SubscriptionTier.ENTERPRISE:
            return True
        current_users = len([u for u in self.users if u.is_active])
        return current_users + count <= self.max_users
    
    @property
    def active_users_count(self) -> int:
        """Get count of active users."""
        return len([u for u in self.users if u.is_active and not u.is_deleted])
    
    @property
    def has_custom_branding(self) -> bool:
        """Check if company tier supports custom branding."""
        return self.subscription_tier in [
            SubscriptionTier.PROFESSIONAL,
            SubscriptionTier.ENTERPRISE
        ]
    
    @property
    def has_advanced_analytics(self) -> bool:
        """Check if company tier supports advanced analytics."""
        return self.subscription_tier in [
            SubscriptionTier.PREMIUM,
            SubscriptionTier.PROFESSIONAL,
            SubscriptionTier.ENTERPRISE
        ]
    
    @property
    def has_api_access(self) -> bool:
        """Check if company tier supports API access."""
        return self.subscription_tier == SubscriptionTier.ENTERPRISE
    
    def get_feature_limits(self) -> dict:
        """Get feature limits based on subscription tier."""
        limits = {
            SubscriptionTier.FREE: {
                "max_users": 10,
                "max_courses": 5,
                "max_phishing_campaigns": 1,
                "custom_branding": False,
                "advanced_analytics": False,
                "api_access": False,
                "priority_support": False
            },
            SubscriptionTier.BASIC: {
                "max_users": 25,
                "max_courses": 10,
                "max_phishing_campaigns": 3,
                "custom_branding": False,
                "advanced_analytics": False,
                "api_access": False,
                "priority_support": False
            },
            SubscriptionTier.STARTER: {
                "max_users": 50,
                "max_courses": 20,
                "max_phishing_campaigns": 5,
                "custom_branding": False,
                "advanced_analytics": False,
                "api_access": False,
                "priority_support": False
            },
            SubscriptionTier.PREMIUM: {
                "max_users": 100,
                "max_courses": 50,
                "max_phishing_campaigns": 10,
                "custom_branding": False,
                "advanced_analytics": True,
                "api_access": False,
                "priority_support": True
            },
            SubscriptionTier.PROFESSIONAL: {
                "max_users": 500,
                "max_courses": -1,  # Unlimited
                "max_phishing_campaigns": -1,  # Unlimited
                "custom_branding": True,
                "advanced_analytics": True,
                "api_access": False,
                "priority_support": True
            },
            SubscriptionTier.ENTERPRISE: {
                "max_users": -1,  # Unlimited
                "max_courses": -1,  # Unlimited
                "max_phishing_campaigns": -1,  # Unlimited
                "custom_branding": True,
                "advanced_analytics": True,
                "api_access": True,
                "priority_support": True
            }
        }
        return limits.get(self.subscription_tier, limits[SubscriptionTier.FREE])
    
    def __repr__(self) -> str:
        """String representation of Company."""
        return f"<Company {self.name} ({self.domain})>"