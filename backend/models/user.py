"""User model with authentication and authorization fields."""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ENUM

from .base import BaseModel, SoftDeleteMixin

if TYPE_CHECKING:
    from .company import Company
    from .course import UserCourseProgress
    from .phishing import PhishingResult
    from .analytics import AnalyticsEvent
    from .audit import AuditLog
    from .email_campaign import EmailLog, EmailPreferences
    from .two_fa_attempt import TwoFAAttempt


class UserRole:
    """User role enumeration."""
    
    SYSTEM_ADMIN = "system_admin"
    COMPANY_ADMIN = "company_admin"
    MANAGER = "manager"
    EMPLOYEE = "employee"


class User(BaseModel, SoftDeleteMixin):
    """User model for authentication and user management."""
    
    __tablename__ = "users"
    
    # Basic Information
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)
    
    # Role and Permissions
    role = Column(
        ENUM('system_admin', 'company_admin', 'manager', 'employee', name='userrole', create_type=False),
        nullable=False,
        server_default='employee'
    )
    is_active = Column(Boolean, nullable=False, server_default=text('true'))
    is_superuser = Column(Boolean, nullable=False, server_default=text('false'))
    
    # Email Verification
    is_verified = Column(Boolean, nullable=False, server_default=text('false'))
    verified_at = Column(DateTime(timezone=True), nullable=True)
    email_verification_token = Column(String(255), nullable=True)
    
    # Password Reset
    password_reset_token = Column(String(255), nullable=True)
    password_reset_expires = Column(DateTime(timezone=True), nullable=True)
    password_changed_at = Column(DateTime(timezone=True), nullable=False, server_default=text('now()'))
    
    # Two-Factor Authentication
    totp_secret = Column(String(255), nullable=True)
    totp_enabled = Column(Boolean, nullable=False, server_default=text('false'))
    totp_verified_at = Column(DateTime(timezone=True), nullable=True)
    backup_codes = Column(Text, nullable=True)
    two_fa_recovery_codes_used = Column(Integer, nullable=False, server_default=text('0'))
    
    # Company Association
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=True, index=True)
    
    # Profile Information
    avatar_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    preferences = Column(Text, nullable=True)
    
    # Activity Tracking
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    company: "Company" = relationship("Company", back_populates="users")
    course_progress: List["UserCourseProgress"] = relationship(
        "UserCourseProgress", 
        back_populates="user",
        cascade="all, delete-orphan"
    )
    phishing_results: List["PhishingResult"] = relationship(
        "PhishingResult",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    analytics_events: List["AnalyticsEvent"] = relationship(
        "AnalyticsEvent",
        back_populates="user"
    )
    audit_logs: List["AuditLog"] = relationship(
        "AuditLog",
        back_populates="user"
    )
    email_logs: List["EmailLog"] = relationship(
        "EmailLog",
        back_populates="user"
    )
    email_preferences: Optional["EmailPreferences"] = relationship(
        "EmailPreferences",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    two_fa_attempts: List["TwoFAAttempt"] = relationship(
        "TwoFAAttempt",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    # Created phishing campaigns
    created_phishing_campaigns = relationship(
        "PhishingCampaign",
        back_populates="created_by",
        foreign_keys="PhishingCampaign.created_by_id"
    )
    
    # Created email templates
    created_email_templates = relationship(
        "EmailTemplate",
        back_populates="created_by"
    )
    
    # Created email campaigns
    created_email_campaigns = relationship(
        "EmailCampaign",
        back_populates="created_by"
    )
    
    @property
    def full_name(self) -> str:
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_admin(self) -> bool:
        """Check if user is an admin (system or company)."""
        return self.role in [UserRole.SYSTEM_ADMIN, UserRole.COMPANY_ADMIN]
    
    @property
    def is_system_admin(self) -> bool:
        """Check if user is a system admin."""
        return self.role == UserRole.SYSTEM_ADMIN or self.is_superuser
    
    @property
    def is_company_admin(self) -> bool:
        """Check if user is a company admin."""
        return self.role == UserRole.COMPANY_ADMIN
    
    @property
    def is_manager(self) -> bool:
        """Check if user is a manager."""
        return self.role == UserRole.MANAGER
    
    @property
    def has_2fa_enabled(self) -> bool:
        """Check if user has 2FA enabled."""
        return self.totp_enabled and self.totp_secret is not None
    
    def can_access_company(self, company_id: int) -> bool:
        """Check if user can access a specific company."""
        if self.is_system_admin:
            return True
        return self.company_id == company_id
    
    def can_manage_users(self) -> bool:
        """Check if user can manage other users."""
        return self.is_admin
    
    def can_manage_courses(self) -> bool:
        """Check if user can manage courses."""
        return self.is_admin or self.is_manager
    
    def can_run_phishing_campaigns(self) -> bool:
        """Check if user can run phishing campaigns."""
        return self.is_admin or self.is_manager
    
    def __repr__(self) -> str:
        """String representation of User."""
        return f"<User {self.email} ({self.role})>"