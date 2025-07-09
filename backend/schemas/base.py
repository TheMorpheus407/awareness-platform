"""
Base schema classes and common mixins for the application.
"""

from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class BaseSchema(BaseModel):
    """
    Base schema with common configuration for all schemas.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        populate_by_name=True,
        use_enum_values=True,
        from_attributes=True,
        validate_assignment=True,
    )


class TimestampMixin(BaseModel):
    """Mixin for models with timestamp fields."""

    created_at: datetime
    updated_at: Optional[datetime] = None


class UUIDMixin(BaseModel):
    """Mixin for models with UUID primary key."""

    id: UUID = Field(..., description="Unique identifier")


class PaginatedResponse(BaseSchema, Generic[T]):
    """
    Generic paginated response wrapper.
    """

    items: List[T] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items", ge=0)
    page: int = Field(..., description="Current page number", ge=0)
    size: int = Field(..., description="Page size", ge=1, le=100)
    pages: int = Field(..., description="Total number of pages", ge=0)

    @classmethod
    def create(
        cls,
        items: List[T],
        total: int,
        page: int = 0,
        size: int = 20,
    ) -> "PaginatedResponse[T]":
        """Create a paginated response with calculated pages."""
        pages = (total + size - 1) // size if size > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages,
        )


class ErrorResponse(BaseSchema):
    """
    Standard error response schema.
    """

    detail: str = Field(..., description="Detailed error message")
    code: Optional[str] = Field(None, description="Error code for client handling")
    field: Optional[str] = Field(None, description="Field that caused the error")
    request_id: Optional[str] = Field(None, description="Request ID for support")


class ValidationErrorDetail(BaseSchema):
    """
    Validation error detail for field-specific errors.
    """

    loc: List[str] = Field(..., description="Error location path")
    msg: str = Field(..., description="Error message")
    type: str = Field(..., description="Error type")


class ValidationErrorResponse(BaseSchema):
    """
    Validation error response with multiple field errors.
    """

    detail: List[ValidationErrorDetail] = Field(
        ..., description="List of validation errors"
    )


class HealthCheckResponse(BaseSchema):
    """
    Health check response schema.
    """

    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(..., description="Current server time")
    version: str = Field(..., description="API version")
    details: Optional[Dict[str, Any]] = Field(
        None, description="Additional health details"
    )


class MessageResponse(BaseSchema):
    """
    Simple message response schema.
    """

    message: str = Field(..., description="Response message")
    success: bool = Field(True, description="Operation success status")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional data")