"""Two-factor authentication attempt tracking model."""

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, text
from sqlalchemy.orm import relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .user import User


class TwoFAAttempt(BaseModel):
    """Two-factor authentication attempt model for rate limiting and security monitoring."""
    
    __tablename__ = "two_fa_attempts"
    
    # Foreign Keys
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # Attempt Information
    attempt_type = Column(String(50), nullable=False)  # 'totp', 'backup_code'
    success = Column(Boolean, nullable=False)
    
    # Request Information
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Note: No updated_at as these records are immutable
    updated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user: "User" = relationship("User", back_populates="two_fa_attempts")
    
    # Attempt types
    class AttemptType:
        TOTP = "totp"
        BACKUP_CODE = "backup_code"
    
    @classmethod
    def log_attempt(
        cls,
        user_id: int,
        attempt_type: str,
        success: bool,
        ip_address: str = None,
        user_agent: str = None
    ) -> "TwoFAAttempt":
        """
        Create and return a new 2FA attempt log.
        
        Note: This method creates the attempt instance but doesn't save it to the database.
        The caller is responsible for adding it to the session and committing.
        """
        return cls(
            user_id=user_id,
            attempt_type=attempt_type,
            success=success,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @classmethod
    def log_totp_attempt(
        cls,
        user_id: int,
        success: bool,
        ip_address: str = None,
        user_agent: str = None
    ) -> "TwoFAAttempt":
        """Log a TOTP authentication attempt."""
        return cls.log_attempt(
            user_id=user_id,
            attempt_type=cls.AttemptType.TOTP,
            success=success,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @classmethod
    def log_backup_code_attempt(
        cls,
        user_id: int,
        success: bool,
        ip_address: str = None,
        user_agent: str = None
    ) -> "TwoFAAttempt":
        """Log a backup code authentication attempt."""
        return cls.log_attempt(
            user_id=user_id,
            attempt_type=cls.AttemptType.BACKUP_CODE,
            success=success,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @property
    def is_totp(self) -> bool:
        """Check if attempt was TOTP."""
        return self.attempt_type == self.AttemptType.TOTP
    
    @property
    def is_backup_code(self) -> bool:
        """Check if attempt was backup code."""
        return self.attempt_type == self.AttemptType.BACKUP_CODE
    
    def __repr__(self) -> str:
        """String representation of TwoFAAttempt."""
        status = "Success" if self.success else "Failed"
        return f"<TwoFAAttempt User:{self.user_id} {self.attempt_type} ({status})>"