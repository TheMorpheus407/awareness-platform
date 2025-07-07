"""Company model."""

from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, Column, Integer, String, Text, JSON
from sqlalchemy.orm import relationship

from .base import Base

if TYPE_CHECKING:
    from .user import User


class Company(Base):
    """Company model for multi-tenant support."""
    
    __tablename__ = "companies"
    
    # Basic information
    name = Column(String(255), nullable=False, unique=True, index=True)
    display_name = Column(String(255), nullable=False)
    domain = Column(String(255), nullable=True, unique=True, index=True)
    
    # Contact information
    contact_email = Column(String(255), nullable=False)
    contact_phone = Column(String(20), nullable=True)
    contact_person = Column(String(255), nullable=True)
    
    # Address
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True)
    
    # Company details
    industry = Column(String(100), nullable=True)
    size = Column(String(50), nullable=True)  # 1-10, 11-50, 51-200, 201-500, 501-1000, 1000+
    website = Column(String(500), nullable=True)
    
    # Subscription and features
    subscription_plan = Column(String(50), nullable=False, default="free")  # free, starter, professional, enterprise
    subscription_expires = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Configuration
    settings = Column(JSON, nullable=True)  # JSON field for company-specific settings
    features = Column(JSON, nullable=True)  # JSON field for enabled features
    
    # Branding
    logo_url = Column(String(500), nullable=True)
    primary_color = Column(String(7), nullable=True)  # Hex color
    secondary_color = Column(String(7), nullable=True)  # Hex color
    
    # Compliance
    compliance_frameworks = Column(JSON, nullable=True)  # List of compliance frameworks
    
    # Relationships
    users = relationship("User", back_populates="company", lazy="dynamic")
    
    def __repr__(self) -> str:
        return f"<Company {self.name}>"
    
    @property
    def employee_count(self) -> int:
        """Get the number of employees in the company."""
        return self.users.filter_by(is_active=True).count()
    
    @property
    def is_premium(self) -> bool:
        """Check if company has a premium subscription."""
        return self.subscription_plan in ["professional", "enterprise"]