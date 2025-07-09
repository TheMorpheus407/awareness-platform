"""Application exceptions."""

from typing import Optional, Any, Dict


class BaseError(Exception):
    """Base exception class."""
    
    def __init__(
        self, 
        message: str, 
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details or {}


class NotFoundError(BaseError):
    """Resource not found error."""
    pass


class ValidationError(BaseError):
    """Validation error."""
    pass


class PermissionError(BaseError):
    """Permission denied error."""
    pass


class AuthenticationError(BaseError):
    """Authentication failed error."""
    pass


class RateLimitError(BaseError):
    """Rate limit exceeded error."""
    pass


class ConfigurationError(BaseError):
    """Configuration error."""
    pass


class ExternalServiceError(BaseError):
    """External service error."""
    pass