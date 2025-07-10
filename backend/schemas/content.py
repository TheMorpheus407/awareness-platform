"""Content delivery schemas."""

from datetime import datetime
from typing import Optional

from pydantic import Field, HttpUrl

from .base import BaseSchema


class ContentAccessToken(BaseSchema):
    """Content access token information."""
    
    token: str = Field(..., description="JWT access token for content")
    expires_at: datetime = Field(..., description="Token expiration time")
    content_id: str = Field(..., description="Content identifier")
    content_type: str = Field(..., description="Type of content")


class SecureContentURL(BaseSchema):
    """Secure URL for content access."""
    
    url: str = Field(..., description="Content URL (may be signed)")
    access_token: str = Field(..., description="Access token for content")
    expires_at: datetime = Field(..., description="URL expiration time")
    content_type: str = Field(..., description="MIME type of content")


class ContentMetadata(BaseSchema):
    """Content file metadata."""
    
    id: str = Field(..., description="Content unique identifier")
    name: str = Field(..., description="File name")
    content_type: str = Field(..., description="MIME type")
    size_bytes: int = Field(..., description="File size in bytes")
    upload_date: datetime = Field(..., description="When file was uploaded")
    download_url: Optional[str] = Field(None, description="Download URL with token")
    thumbnail_url: Optional[str] = Field(None, description="Thumbnail URL if applicable")


class ContentUploadResponse(BaseSchema):
    """Response after content upload."""
    
    content_id: str = Field(..., description="Unique content identifier")
    filename: str = Field(..., description="Original filename")
    size_bytes: int = Field(..., description="File size in bytes")
    content_type: str = Field(..., description="MIME type")
    upload_date: datetime = Field(..., description="Upload timestamp")
    message: str = Field("File uploaded successfully")


class ContentUploadRequest(BaseSchema):
    """Request for content upload."""
    
    filename: str = Field(..., description="Original filename")
    content_type: str = Field(..., description="MIME type")
    course_id: Optional[int] = Field(None, description="Associated course ID")
    description: Optional[str] = Field(None, description="Content description")
    tags: list[str] = Field(default_factory=list, description="Content tags")