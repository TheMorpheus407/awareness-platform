"""Two-Factor Authentication attempt model."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base

if TYPE_CHECKING:
    from .user import User


class TwoFAAttempt(Base):
    """Model for tracking 2FA verification attempts."""
    
    __tablename__ = "two_fa_attempts"
    
    # User relationship
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="two_fa_attempts")
    
    # Attempt details
    attempt_type = Column(String(50), nullable=False)  # 'totp', 'backup_code'
    success = Column(Boolean, nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    def __repr__(self) -> str:
        return f"<TwoFAAttempt {self.user_id} - {self.attempt_type} - {'Success' if self.success else 'Failed'}>"