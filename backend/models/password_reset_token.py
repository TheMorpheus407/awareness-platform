"""Password reset token model for secure password recovery."""

from datetime import datetime, timedelta
from typing import TYPE_CHECKING
import secrets

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, text
from sqlalchemy.orm import relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .user import User


class PasswordResetToken(BaseModel):
    """Password reset token model for secure password recovery."""
    
    __tablename__ = "password_reset_tokens"
    
    # Foreign Keys
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # Token Information
    token = Column(String(255), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Usage Tracking
    used = Column(Boolean, nullable=False, server_default=text('false'))
    used_at = Column(DateTime(timezone=True), nullable=True)
    
    # Request Information
    requested_ip = Column(String(45), nullable=True)
    requested_user_agent = Column(String(500), nullable=True)
    used_ip = Column(String(45), nullable=True)
    used_user_agent = Column(String(500), nullable=True)
    
    # Relationships
    user: "User" = relationship("User", foreign_keys=[user_id])
    
    # Default expiration time (hours)
    DEFAULT_EXPIRATION_HOURS = 24
    
    @classmethod
    def generate_token(cls) -> str:
        """Generate a secure random token."""
        return secrets.token_urlsafe(32)
    
    @classmethod
    def create_for_user(
        cls,
        user_id: int,
        expiration_hours: int = None,
        requested_ip: str = None,
        requested_user_agent: str = None
    ) -> "PasswordResetToken":
        """
        Create a new password reset token for a user.
        
        Args:
            user_id: The ID of the user requesting password reset
            expiration_hours: Hours until token expires (default: 24)
            requested_ip: IP address of the request
            requested_user_agent: User agent of the request
        
        Returns:
            New PasswordResetToken instance
        """
        if expiration_hours is None:
            expiration_hours = cls.DEFAULT_EXPIRATION_HOURS
        
        expires_at = datetime.utcnow() + timedelta(hours=expiration_hours)
        
        return cls(
            user_id=user_id,
            token=cls.generate_token(),
            expires_at=expires_at,
            requested_ip=requested_ip,
            requested_user_agent=requested_user_agent
        )
    
    @property
    def is_expired(self) -> bool:
        """Check if token has expired."""
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Check if token is valid (not used and not expired)."""
        return not self.used and not self.is_expired
    
    @property
    def time_until_expiration(self) -> timedelta:
        """Get time remaining until token expires."""
        if self.is_expired:
            return timedelta(0)
        return self.expires_at - datetime.utcnow()
    
    def mark_as_used(self, used_ip: str = None, used_user_agent: str = None) -> None:
        """
        Mark token as used.
        
        Args:
            used_ip: IP address that used the token
            used_user_agent: User agent that used the token
        """
        self.used = True
        self.used_at = datetime.utcnow()
        self.used_ip = used_ip
        self.used_user_agent = used_user_agent
    
    def get_reset_url(self, base_url: str) -> str:
        """
        Generate password reset URL.
        
        Args:
            base_url: Base URL of the application
        
        Returns:
            Complete password reset URL
        """
        return f"{base_url}/auth/reset-password?token={self.token}"
    
    def __repr__(self) -> str:
        """String representation of PasswordResetToken."""
        status = "Used" if self.used else ("Expired" if self.is_expired else "Valid")
        return f"<PasswordResetToken User:{self.user_id} ({status})>"