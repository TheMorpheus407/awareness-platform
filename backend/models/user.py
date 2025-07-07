"""User model."""

from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .base import Base

if TYPE_CHECKING:
    from .company import Company


class User(Base):
    """User model for authentication and profile management."""
    
    __tablename__ = "users"
    
    # Authentication fields
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # Profile fields
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)
    
    # Role and permissions
    role = Column(String(50), nullable=False, default="user")  # user, admin, company_admin
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    verified_at = Column(DateTime, nullable=True)
    is_superuser = Column(Boolean, default=False, nullable=False)
    
    # Company relationship
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    company = relationship("Company", back_populates="users")
    
    # Additional fields
    last_login = Column(DateTime, nullable=True)
    password_changed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Security fields
    email_verification_token = Column(String(255), nullable=True)
    password_reset_token = Column(String(255), nullable=True)
    password_reset_expires = Column(DateTime, nullable=True)
    
    # Profile
    avatar_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    preferences = Column(Text, nullable=True)  # JSON field for user preferences
    
    def __repr__(self) -> str:
        return f"<User {self.email}>"
    
    @property
    def full_name(self) -> str:
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_company_admin(self) -> bool:
        """Check if user is a company admin."""
        return self.role == "company_admin"
    
    @property
    def is_admin(self) -> bool:
        """Check if user is a platform admin."""
        return self.role == "admin" or self.is_superuser