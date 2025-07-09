"""Audit log model for tracking system changes and user actions."""

from typing import TYPE_CHECKING, Any, Dict, Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSON

from .base import BaseModel

if TYPE_CHECKING:
    from .user import User
    from .company import Company


class AuditLog(BaseModel):
    """Audit log model for tracking system changes and user actions."""
    
    __tablename__ = "audit_logs"
    
    # Foreign Keys
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'), nullable=True, index=True)
    
    # Audit Information
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(100), nullable=False)
    resource_id = Column(Integer, nullable=True)
    
    # Change Tracking
    changes = Column(JSON, nullable=True)  # {"field": {"old": "value1", "new": "value2"}}
    
    # Request Information
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Relationships
    user: Optional["User"] = relationship("User", back_populates="audit_logs")
    company: Optional["Company"] = relationship("Company", back_populates="audit_logs")
    
    # Common actions
    class Action:
        # CRUD operations
        CREATE = "create"
        READ = "read"
        UPDATE = "update"
        DELETE = "delete"
        
        # Authentication actions
        LOGIN = "login"
        LOGOUT = "logout"
        LOGIN_FAILED = "login_failed"
        PASSWORD_RESET = "password_reset"
        PASSWORD_CHANGED = "password_changed"
        
        # Permission actions
        PERMISSION_GRANTED = "permission_granted"
        PERMISSION_REVOKED = "permission_revoked"
        ROLE_CHANGED = "role_changed"
        
        # Data export/import
        EXPORT = "export"
        IMPORT = "import"
        
        # Configuration changes
        CONFIG_CHANGED = "config_changed"
        SETTINGS_UPDATED = "settings_updated"
        
        # Security actions
        SECURITY_ALERT = "security_alert"
        SUSPICIOUS_ACTIVITY = "suspicious_activity"
        ACCESS_DENIED = "access_denied"
    
    # Resource types
    class ResourceType:
        USER = "user"
        COMPANY = "company"
        COURSE = "course"
        QUIZ = "quiz"
        PHISHING_CAMPAIGN = "phishing_campaign"
        PHISHING_TEMPLATE = "phishing_template"
        EMAIL_CAMPAIGN = "email_campaign"
        EMAIL_TEMPLATE = "email_template"
        PAYMENT = "payment"
        SUBSCRIPTION = "subscription"
        SETTINGS = "settings"
        SYSTEM = "system"
    
    @classmethod
    def log(
        cls,
        action: str,
        resource_type: str,
        resource_id: Optional[int] = None,
        user_id: Optional[int] = None,
        company_id: Optional[int] = None,
        changes: Optional[Dict[str, Dict[str, Any]]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> "AuditLog":
        """
        Create and return a new audit log entry.
        
        Note: This method creates the audit log instance but doesn't save it to the database.
        The caller is responsible for adding it to the session and committing.
        """
        return cls(
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            company_id=company_id,
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @classmethod
    def log_create(
        cls,
        resource_type: str,
        resource_id: int,
        user_id: int,
        company_id: Optional[int] = None,
        data: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> "AuditLog":
        """Log a resource creation."""
        changes = {"created": {"old": None, "new": data}} if data else None
        return cls.log(
            action=cls.Action.CREATE,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            company_id=company_id,
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @classmethod
    def log_update(
        cls,
        resource_type: str,
        resource_id: int,
        user_id: int,
        company_id: Optional[int] = None,
        changes: Optional[Dict[str, Dict[str, Any]]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> "AuditLog":
        """Log a resource update."""
        return cls.log(
            action=cls.Action.UPDATE,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            company_id=company_id,
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @classmethod
    def log_delete(
        cls,
        resource_type: str,
        resource_id: int,
        user_id: int,
        company_id: Optional[int] = None,
        data: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> "AuditLog":
        """Log a resource deletion."""
        changes = {"deleted": {"old": data, "new": None}} if data else None
        return cls.log(
            action=cls.Action.DELETE,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            company_id=company_id,
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @classmethod
    def log_login(
        cls,
        user_id: int,
        company_id: int,
        success: bool = True,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> "AuditLog":
        """Log a login attempt."""
        return cls.log(
            action=cls.Action.LOGIN if success else cls.Action.LOGIN_FAILED,
            resource_type=cls.ResourceType.USER,
            resource_id=user_id,
            user_id=user_id,
            company_id=company_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @classmethod
    def log_security_event(
        cls,
        event_type: str,
        user_id: Optional[int] = None,
        company_id: Optional[int] = None,
        details: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> "AuditLog":
        """Log a security event."""
        return cls.log(
            action=event_type,
            resource_type=cls.ResourceType.SYSTEM,
            user_id=user_id,
            company_id=company_id,
            changes={"details": {"old": None, "new": details}} if details else None,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    def get_change_summary(self) -> str:
        """Get a human-readable summary of changes."""
        if not self.changes:
            return f"{self.action} {self.resource_type}"
        
        summaries = []
        for field, change in self.changes.items():
            old_val = change.get("old", "N/A")
            new_val = change.get("new", "N/A")
            summaries.append(f"{field}: {old_val} → {new_val}")
        
        return f"{self.action} {self.resource_type}: " + ", ".join(summaries)
    
    def __repr__(self) -> str:
        """String representation of AuditLog."""
        return f"<AuditLog {self.action} {self.resource_type} (User: {self.user_id})>"