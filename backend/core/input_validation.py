"""Enhanced input validation and sanitization utilities."""

import re
import html
import bleach
from typing import Any, Dict, List, Optional, Pattern, Union
from urllib.parse import urlparse
from pydantic import BaseModel, Field, validator, root_validator
from email_validator import validate_email, EmailNotValidError
from core.logging import logger


class InputSanitizer:
    """Comprehensive input sanitization utilities."""
    
    # Allowed HTML tags for rich text content
    ALLOWED_TAGS = [
        'p', 'br', 'strong', 'em', 'u', 'i', 'b',
        'ul', 'ol', 'li', 'blockquote', 'code', 'pre',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'a', 'img', 'table', 'thead', 'tbody', 'tr', 'th', 'td'
    ]
    
    # Allowed HTML attributes
    ALLOWED_ATTRIBUTES = {
        'a': ['href', 'title', 'target'],
        'img': ['src', 'alt', 'width', 'height'],
        'blockquote': ['cite'],
        'code': ['class']
    }
    
    # Regex patterns for validation
    PATTERNS = {
        'alphanumeric': re.compile(r'^[a-zA-Z0-9]+$'),
        'alphanumeric_space': re.compile(r'^[a-zA-Z0-9\s]+$'),
        'alphanumeric_dash': re.compile(r'^[a-zA-Z0-9\-_]+$'),
        'numeric': re.compile(r'^[0-9]+$'),
        'decimal': re.compile(r'^[0-9]+\.?[0-9]*$'),
        'phone': re.compile(r'^[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{4,6}$'),
        'username': re.compile(r'^[a-zA-Z0-9_.-]+$'),
        'safe_string': re.compile(r'^[a-zA-Z0-9\s\-_.,!?@#$%&*()+=\[\]{};:\'"/\\|<>]+$'),
        'sql_injection': re.compile(r'(\b(union|select|insert|update|delete|drop|create|alter|exec|execute|script|javascript|vbscript|onload|onerror|onclick)\b)|(-{2})|(/\*|\*/)', re.IGNORECASE),
        'xss_attempt': re.compile(r'(<script|<iframe|javascript:|vbscript:|on\w+\s*=)', re.IGNORECASE),
        'path_traversal': re.compile(r'\.\.[\\/]|\.\.%2[fF]|\.\.%5[cC]'),
        'null_byte': re.compile(r'%00|\x00'),
        'command_injection': re.compile(r'[;&|`$]|\$\(|\bsh\b|\bbash\b|\bcmd\b|\bpowershell\b', re.IGNORECASE)
    }
    
    @staticmethod
    def sanitize_html(content: str, allowed_tags: Optional[List[str]] = None, 
                     allowed_attributes: Optional[Dict[str, List[str]]] = None) -> str:
        """Sanitize HTML content using bleach."""
        if not content:
            return ""
        
        tags = allowed_tags or InputSanitizer.ALLOWED_TAGS
        attrs = allowed_attributes or InputSanitizer.ALLOWED_ATTRIBUTES
        
        # Clean HTML
        cleaned = bleach.clean(
            content,
            tags=tags,
            attributes=attrs,
            strip=True,
            strip_comments=True
        )
        
        # Additional XSS protection
        cleaned = InputSanitizer._remove_javascript_urls(cleaned)
        
        return cleaned
    
    @staticmethod
    def _remove_javascript_urls(content: str) -> str:
        """Remove javascript: and vbscript: URLs."""
        # Remove javascript: and vbscript: protocols
        content = re.sub(r'javascript\s*:', '', content, flags=re.IGNORECASE)
        content = re.sub(r'vbscript\s*:', '', content, flags=re.IGNORECASE)
        content = re.sub(r'data\s*:.*script', '', content, flags=re.IGNORECASE)
        return content
    
    @staticmethod
    def sanitize_string(value: str, max_length: Optional[int] = None,
                       allowed_pattern: Optional[Pattern] = None) -> str:
        """Sanitize a string value."""
        if not value:
            return ""
        
        # Strip whitespace
        value = value.strip()
        
        # Escape HTML entities
        value = html.escape(value)
        
        # Apply length limit
        if max_length and len(value) > max_length:
            value = value[:max_length]
        
        # Check against allowed pattern
        if allowed_pattern and not allowed_pattern.match(value):
            raise ValueError(f"Invalid format for value: {value}")
        
        return value
    
    @staticmethod
    def sanitize_email(email: str) -> str:
        """Sanitize and validate email address."""
        if not email:
            return ""
        
        email = email.strip().lower()
        
        try:
            # Validate email format
            valid = validate_email(email)
            return valid.email
        except EmailNotValidError as e:
            raise ValueError(f"Invalid email address: {str(e)}")
    
    @staticmethod
    def sanitize_url(url: str, allowed_schemes: Optional[List[str]] = None) -> str:
        """Sanitize and validate URL."""
        if not url:
            return ""
        
        url = url.strip()
        allowed_schemes = allowed_schemes or ['http', 'https']
        
        try:
            parsed = urlparse(url)
            
            # Check scheme
            if parsed.scheme not in allowed_schemes:
                raise ValueError(f"Invalid URL scheme: {parsed.scheme}")
            
            # Check for common injection attempts
            if InputSanitizer.PATTERNS['xss_attempt'].search(url):
                raise ValueError("Potential XSS attempt detected in URL")
            
            return url
        except Exception as e:
            raise ValueError(f"Invalid URL: {str(e)}")
    
    @staticmethod
    def sanitize_filename(filename: str, allowed_extensions: Optional[List[str]] = None) -> str:
        """Sanitize filename to prevent directory traversal and other attacks."""
        if not filename:
            return ""
        
        # Remove path components
        filename = filename.replace('\\', '/').split('/')[-1]
        
        # Remove null bytes
        filename = filename.replace('\x00', '')
        
        # Remove special characters except dots and dashes
        filename = re.sub(r'[^\w\s.-]', '', filename)
        
        # Check extension
        if allowed_extensions:
            ext = filename.split('.')[-1].lower() if '.' in filename else ''
            if ext not in allowed_extensions:
                raise ValueError(f"File extension '{ext}' not allowed")
        
        return filename
    
    @staticmethod
    def sanitize_json_input(data: Dict[str, Any], schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Sanitize JSON input data."""
        sanitized = {}
        
        for key, value in data.items():
            # Sanitize key
            if not isinstance(key, str) or len(key) > 100:
                continue
            
            sanitized_key = InputSanitizer.sanitize_string(key, max_length=100)
            
            # Sanitize value based on type
            if isinstance(value, str):
                sanitized[sanitized_key] = InputSanitizer.sanitize_string(value)
            elif isinstance(value, (int, float)):
                sanitized[sanitized_key] = value
            elif isinstance(value, bool):
                sanitized[sanitized_key] = value
            elif isinstance(value, list):
                sanitized[sanitized_key] = [
                    InputSanitizer.sanitize_string(item) if isinstance(item, str) else item
                    for item in value[:1000]  # Limit array size
                ]
            elif isinstance(value, dict):
                sanitized[sanitized_key] = InputSanitizer.sanitize_json_input(value)
            
        return sanitized
    
    @staticmethod
    def detect_injection_attempt(value: str) -> bool:
        """Detect potential injection attempts."""
        if not value:
            return False
        
        # Check for SQL injection patterns
        if InputSanitizer.PATTERNS['sql_injection'].search(value):
            logger.warning(f"Potential SQL injection attempt detected: {value[:100]}")
            return True
        
        # Check for XSS patterns
        if InputSanitizer.PATTERNS['xss_attempt'].search(value):
            logger.warning(f"Potential XSS attempt detected: {value[:100]}")
            return True
        
        # Check for path traversal
        if InputSanitizer.PATTERNS['path_traversal'].search(value):
            logger.warning(f"Potential path traversal attempt detected: {value[:100]}")
            return True
        
        # Check for command injection
        if InputSanitizer.PATTERNS['command_injection'].search(value):
            logger.warning(f"Potential command injection attempt detected: {value[:100]}")
            return True
        
        # Check for null byte injection
        if InputSanitizer.PATTERNS['null_byte'].search(value):
            logger.warning(f"Potential null byte injection detected: {value[:100]}")
            return True
        
        return False


class SecureInputMixin:
    """Mixin for Pydantic models to add input validation."""
    
    @root_validator(pre=True)
    def sanitize_inputs(cls, values):
        """Sanitize all string inputs."""
        for field, value in values.items():
            if isinstance(value, str):
                # Check for injection attempts
                if InputSanitizer.detect_injection_attempt(value):
                    raise ValueError(f"Potential injection attempt detected in field: {field}")
                
                # Basic sanitization
                values[field] = value.strip()
        
        return values


class StrictEmailStr(str):
    """Strict email validation type."""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if not isinstance(v, str):
            raise TypeError('string required')
        
        return InputSanitizer.sanitize_email(v)


class SafeStr(str):
    """Safe string type with injection protection."""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if not isinstance(v, str):
            raise TypeError('string required')
        
        if InputSanitizer.detect_injection_attempt(v):
            raise ValueError('Potential injection attempt detected')
        
        return InputSanitizer.sanitize_string(v)


class SafeHTMLStr(str):
    """Safe HTML string type."""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if not isinstance(v, str):
            raise TypeError('string required')
        
        return InputSanitizer.sanitize_html(v)


class SecureFileUpload(BaseModel):
    """Secure file upload validation."""
    
    filename: str = Field(..., min_length=1, max_length=255)
    content_type: str = Field(..., regex=r'^[\w.-]+/[\w.-]+$')
    size: int = Field(..., gt=0, le=10485760)  # Max 10MB
    
    @validator('filename')
    def validate_filename(cls, v):
        """Validate and sanitize filename."""
        return InputSanitizer.sanitize_filename(v)
    
    @validator('content_type')
    def validate_content_type(cls, v):
        """Validate content type."""
        allowed_types = [
            'image/jpeg', 'image/png', 'image/gif', 'image/webp',
            'application/pdf', 'text/plain', 'text/csv',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        ]
        
        if v not in allowed_types:
            raise ValueError(f"Content type '{v}' not allowed")
        
        return v


def validate_pagination_params(page: int = 1, page_size: int = 10) -> tuple[int, int]:
    """Validate pagination parameters."""
    # Validate page
    if page < 1:
        page = 1
    elif page > 10000:
        page = 10000
    
    # Validate page size
    if page_size < 1:
        page_size = 1
    elif page_size > 100:
        page_size = 100
    
    return page, page_size


def validate_sort_params(sort_by: str, allowed_fields: List[str]) -> str:
    """Validate sort parameters."""
    # Remove any potential SQL injection
    sort_by = re.sub(r'[^\w\s,-]', '', sort_by)
    
    # Parse sort fields
    sort_fields = []
    for field in sort_by.split(','):
        field = field.strip()
        
        # Check for descending order
        desc = False
        if field.startswith('-'):
            desc = True
            field = field[1:]
        
        # Validate field name
        if field in allowed_fields:
            sort_fields.append(f"-{field}" if desc else field)
    
    return ','.join(sort_fields) if sort_fields else allowed_fields[0]