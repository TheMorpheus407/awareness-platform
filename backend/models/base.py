"""Base model class with common fields and functionality."""

from datetime import datetime
from typing import Any, Dict, Optional
import uuid

from sqlalchemy import Column, DateTime, Integer, func, text
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all models with common functionality."""
    
    # Allow legacy annotations without Mapped[]
    __allow_unmapped__ = True
    
    @declared_attr
    def __tablename__(cls) -> str:
        """Generate table name from class name."""
        # Convert CamelCase to snake_case
        name = cls.__name__
        # Handle acronyms and add underscores before capitals
        result = []
        for i, char in enumerate(name):
            if i > 0 and char.isupper():
                # Check if previous char is lowercase or if next char exists and is lowercase
                if (name[i-1].islower() or 
                    (i < len(name) - 1 and name[i+1].islower())):
                    result.append('_')
            result.append(char.lower())
        return ''.join(result)


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""
    
    created_at = Column(
        DateTime(timezone=True), 
        nullable=False, 
        server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True), 
        nullable=False, 
        server_default=func.now(),
        onupdate=func.now()
    )


class SoftDeleteMixin:
    """Mixin for soft delete functionality."""
    
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    @property
    def is_deleted(self) -> bool:
        """Check if the record is soft deleted."""
        return self.deleted_at is not None
    
    def soft_delete(self) -> None:
        """Soft delete the record."""
        self.deleted_at = datetime.utcnow()
    
    def restore(self) -> None:
        """Restore a soft deleted record."""
        self.deleted_at = None


class UUIDPrimaryKeyMixin:
    """Mixin for UUID primary key."""
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )


class IntegerPrimaryKeyMixin:
    """Mixin for integer primary key."""
    
    id = Column(Integer, primary_key=True, nullable=False)


class BaseModel(Base, IntegerPrimaryKeyMixin, TimestampMixin):
    """Base model with integer ID and timestamps."""
    
    __abstract__ = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
    
    def update(self, **kwargs: Any) -> None:
        """Update model attributes."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)


class BaseUUIDModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Base model with UUID ID and timestamps."""
    
    __abstract__ = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, uuid.UUID):
                value = str(value)
            elif isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
        return result
    
    def update(self, **kwargs: Any) -> None:
        """Update model attributes."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)