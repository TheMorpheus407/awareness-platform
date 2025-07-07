"""Base schemas with common fields."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    
    model_config = ConfigDict(from_attributes=True)


class TimestampMixin(BaseModel):
    """Mixin for timestamp fields."""
    
    created_at: datetime
    updated_at: datetime


class IDMixin(BaseModel):
    """Mixin for ID field."""
    
    id: int


class MessageResponse(BaseModel):
    """Simple message response."""
    
    message: str