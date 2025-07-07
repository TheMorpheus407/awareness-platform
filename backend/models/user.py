"""User model."""

from datetime import datetime
from typing import TYPE_CHECKING, List
import enum

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
import json
from typing import Optional

from .base import Base

if TYPE_CHECKING:
    from .company import Company


class UserRole(str, enum.Enum):
    """User role enumeration."""
    SYSTEM_ADMIN = "system_admin"
    COMPANY_ADMIN = "company_admin"
    MANAGER = "manager"
    EMPLOYEE = "employee"


class User(Base):
    """User model for authentication and profile management."""
    
    __tablename__ = "users"
    
    # Company relationship (NOT NULL in database)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    company = relationship("Company", back_populates="users")
    
    # Authentication fields
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    
    # Profile fields
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    role = Column(Enum(UserRole, values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=UserRole.EMPLOYEE.value)
    department = Column(String(100), nullable=True)
    job_title = Column(String(100), nullable=True)
    phone = Column(String(50), nullable=True)
    avatar_url = Column(Text, nullable=True)
    language = Column(String(5), nullable=False, default="de")
    
    # Status fields
    is_active = Column(Boolean, nullable=False, default=True)
    email_verified = Column(Boolean, nullable=False, default=False)
    email_verified_at = Column(DateTime(timezone=True), nullable=True)
    
    # Login tracking
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    password_changed_at = Column(DateTime(timezone=True), nullable=True)
    failed_login_attempts = Column(Integer, nullable=False, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    
    # Soft delete
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Two-Factor Authentication fields
    totp_secret = Column(String(255), nullable=True)  # Encrypted TOTP secret
    totp_enabled = Column(Boolean, nullable=False, default=False)
    totp_verified_at = Column(DateTime(timezone=True), nullable=True)
    backup_codes = Column(Text, nullable=True)  # JSON array of encrypted backup codes
    two_fa_recovery_codes_used = Column(Integer, nullable=False, default=0)
    
    # Relationships
    password_reset_tokens = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")
    two_fa_attempts = relationship("TwoFAAttempt", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<User {self.email}>"
    
    @property
    def full_name(self) -> str:
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_company_admin(self) -> bool:
        """Check if user is a company admin."""
        return self.role == UserRole.COMPANY_ADMIN
    
    @property
    def is_system_admin(self) -> bool:
        """Check if user is a system admin."""
        return self.role == UserRole.SYSTEM_ADMIN
    
    @property
    def is_manager(self) -> bool:
        """Check if user is a manager."""
        return self.role == UserRole.MANAGER
    
    @property
    def is_employee(self) -> bool:
        """Check if user is an employee."""
        return self.role == UserRole.EMPLOYEE
    
    @property
    def is_verified(self) -> bool:
        """Backward compatibility property for email_verified."""
        return self.email_verified
    
    @property
    def is_locked(self) -> bool:
        """Check if user account is locked."""
        if self.locked_until:
            return datetime.utcnow() < self.locked_until
        return False
    
    @property
    def has_2fa_enabled(self) -> bool:
        """Check if user has 2FA enabled and verified."""
        return self.totp_enabled and self.totp_secret is not None
    
    def get_backup_codes(self) -> Optional[List[str]]:
        """Get decrypted backup codes."""
        if self.backup_codes:
            try:
                return json.loads(self.backup_codes)
            except:
                return None
        return None
    
    def set_backup_codes(self, codes: List[str]) -> None:
        """Set encrypted backup codes."""
        self.backup_codes = json.dumps(codes)