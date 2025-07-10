"""Health check schemas."""

from datetime import datetime
from typing import Dict, Any, Optional

from pydantic import Field

from .base import BaseSchema


class HealthResponse(BaseSchema):
    """Basic health check response."""
    
    status: str = Field(..., description="Service status", pattern="^(ok|degraded|error)$")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: Optional[str] = Field(None, description="Application version")
    environment: Optional[str] = Field(None, description="Environment name")


class ComponentHealth(BaseSchema):
    """Health status of a single component."""
    
    name: str = Field(..., description="Component name")
    status: str = Field(..., description="Component status", pattern="^(healthy|degraded|unhealthy|unknown)$")
    response_time_ms: float = Field(..., description="Response time in milliseconds")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details")
    error: Optional[str] = Field(None, description="Error message if unhealthy")


class DependencyHealth(BaseSchema):
    """Health status of external dependency."""
    
    name: str = Field(..., description="Dependency name")
    status: str = Field(..., description="Dependency status")
    endpoint: str = Field(..., description="Dependency endpoint")
    response_time_ms: float = Field(..., description="Response time in milliseconds")
    error: Optional[str] = Field(None, description="Error message if unhealthy")


class ServiceHealth(BaseSchema):
    """Health status of internal service."""
    
    name: str = Field(..., description="Service name")
    status: str = Field(..., description="Service status")
    workers: int = Field(..., description="Number of workers")
    tasks_pending: int = Field(..., description="Pending tasks count")
    tasks_active: int = Field(..., description="Active tasks count")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details")
    error: Optional[str] = Field(None, description="Error message if unhealthy")


class DetailedHealthResponse(BaseSchema):
    """Detailed health check response."""
    
    status: str = Field(..., description="Overall status")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    components: Dict[str, ComponentHealth] = Field(..., description="Component health statuses")
    dependencies: Dict[str, DependencyHealth] = Field(..., description="External dependency statuses")
    system_info: Dict[str, Any] = Field(..., description="System information")