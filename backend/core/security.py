"""Security utilities for password hashing and JWT tokens."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Union

from jose import JWTError, jwt
from passlib.context import CryptContext

from core.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class SecurityUtils:
    """Security utilities for the application."""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a plain password against a hashed password.
        
        Args:
            plain_password: The plain text password
            hashed_password: The hashed password to verify against
            
        Returns:
            True if password matches, False otherwise
        """
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt.
        
        Args:
            password: The plain text password to hash
            
        Returns:
            The hashed password
        """
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(
        subject: Union[str, Any],
        expires_delta: Optional[timedelta] = None,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a JWT access token.
        
        Args:
            subject: The subject of the token (usually user ID)
            expires_delta: Optional custom expiration time
            additional_claims: Optional additional claims to include
            
        Returns:
            The encoded JWT token
        """
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + settings.access_token_expire_timedelta
        
        to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
        
        if additional_claims:
            to_encode.update(additional_claims)
        
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(
        subject: Union[str, Any],
        expires_delta: Optional[timedelta] = None,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a JWT refresh token.
        
        Args:
            subject: The subject of the token (usually user ID)
            expires_delta: Optional custom expiration time
            additional_claims: Optional additional claims to include
            
        Returns:
            The encoded JWT token
        """
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + settings.refresh_token_expire_timedelta
        
        to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
        
        if additional_claims:
            to_encode.update(additional_claims)
        
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def decode_token(token: str) -> Dict[str, Any]:
        """
        Decode a JWT token.
        
        Args:
            token: The JWT token to decode
            
        Returns:
            The decoded token payload
            
        Raises:
            JWTError: If the token is invalid or expired
        """
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            return payload
        except JWTError:
            raise
    
    @staticmethod
    def create_password_reset_token(email: str) -> str:
        """
        Create a password reset token.
        
        Args:
            email: The email address to create the token for
            
        Returns:
            The encoded JWT token for password reset
        """
        expire = datetime.now(timezone.utc) + timedelta(hours=24)
        to_encode = {
            "exp": expire,
            "sub": email,
            "type": "password_reset"
        }
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_password_reset_token(token: str) -> Optional[str]:
        """
        Verify a password reset token.
        
        Args:
            token: The password reset token to verify
            
        Returns:
            The email address if valid, None otherwise
        """
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            if payload.get("type") != "password_reset":
                return None
            email: str = payload.get("sub")
            return email
        except JWTError:
            return None
    
    @staticmethod
    def create_email_verification_token(email: str) -> str:
        """
        Create an email verification token.
        
        Args:
            email: The email address to verify
            
        Returns:
            The encoded JWT token for email verification
        """
        expire = datetime.now(timezone.utc) + timedelta(days=7)
        to_encode = {
            "exp": expire,
            "sub": email,
            "type": "email_verification"
        }
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_email_verification_token(token: str) -> Optional[str]:
        """
        Verify an email verification token.
        
        Args:
            token: The email verification token to verify
            
        Returns:
            The email address if valid, None otherwise
        """
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            if payload.get("type") != "email_verification":
                return None
            email: str = payload.get("sub")
            return email
        except JWTError:
            return None
    
    @staticmethod
    def validate_password(password: str) -> tuple[bool, str]:
        """
        Validate password against security policy.
        
        Args:
            password: The password to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(password) < settings.PASSWORD_MIN_LENGTH:
            return False, f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters long"
        
        if settings.PASSWORD_REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter"
        
        if settings.PASSWORD_REQUIRE_LOWERCASE and not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter"
        
        if settings.PASSWORD_REQUIRE_DIGIT and not any(c.isdigit() for c in password):
            return False, "Password must contain at least one digit"
        
        if settings.PASSWORD_REQUIRE_SPECIAL and not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            return False, "Password must contain at least one special character"
        
        return True, ""


# Global security instance
security = SecurityUtils()