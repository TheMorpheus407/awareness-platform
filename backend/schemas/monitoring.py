"""Monitoring and metrics schemas."""

from datetime import datetime
from typing import Dict, Any, Optional

from pydantic import Field

from .base import BaseSchema


class HealthStatus(BaseSchema):
    """Basic health status."""
    
    status: str = Field(..., description="Health status", pattern="^(healthy|degraded|unhealthy)$")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Environment name")


class DatabaseMetrics(BaseSchema):
    """Database connection metrics."""
    
    status: str = Field(..., description="Database health status")
    active_connections: int = Field(..., description="Active connection count")
    idle_connections: int = Field(..., description="Idle connection count")
    total_connections: int = Field(..., description="Total connections in pool")
    pool_size: int = Field(..., description="Maximum pool size")
    response_time_ms: float = Field(..., description="Average response time")
    error: Optional[str] = Field(None, description="Error message if unhealthy")


class CacheMetrics(BaseSchema):
    """Cache (Redis) metrics."""
    
    status: str = Field(..., description="Cache health status")
    connected_clients: int = Field(..., description="Number of connected clients")
    used_memory_mb: float = Field(..., description="Used memory in MB")
    hit_rate: float = Field(..., description="Cache hit rate percentage")
    total_commands: int = Field(..., description="Total commands processed")
    response_time_ms: float = Field(..., description="Average response time")
    error: Optional[str] = Field(None, description="Error message if unhealthy")


class ApplicationMetrics(BaseSchema):
    """Application performance metrics."""
    
    uptime_seconds: int = Field(..., description="Application uptime in seconds")
    total_requests: int = Field(..., description="Total requests handled")
    active_users: int = Field(..., description="Currently active users")
    error_rate: float = Field(..., description="Error rate percentage")
    average_response_time_ms: float = Field(..., description="Average response time")
    memory_usage_mb: float = Field(..., description="Memory usage in MB")
    cpu_usage_percent: float = Field(..., description="CPU usage percentage")


class SystemMetrics(BaseSchema):
    """Complete system metrics."""
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(..., description="Overall system status")
    database: DatabaseMetrics
    cache: CacheMetrics
    application: ApplicationMetrics


class MetricsResponse(BaseSchema):
    """Prometheus-compatible metrics response."""
    
    metrics: str = Field(..., description="Prometheus exposition format metrics")
    generated_at: datetime = Field(default_factory=datetime.utcnow)