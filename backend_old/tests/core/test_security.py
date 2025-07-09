"""Tests for security module."""

import pytest
from datetime import datetime, timedelta
from jose import jwt

from core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from core.config import settings


class TestPasswordHashing:
    """Test password hashing functions."""
    
    def test_password_hash_verification(self):
        """Test password hashing and verification."""
        password = "SecurePassword123!"
        
        # Hash password
        hashed = get_password_hash(password)
        
        # Verify correct password
        assert verify_password(password, hashed) is True
        
        # Verify incorrect password
        assert verify_password("WrongPassword", hashed) is False
    
    def test_password_hash_is_different(self):
        """Test that same password produces different hashes."""
        password = "TestPassword123!"
        
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        # Hashes should be different due to salt
        assert hash1 != hash2
        
        # But both should verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True
    
    def test_empty_password(self):
        """Test handling of empty password."""
        # Should still hash empty string
        hashed = get_password_hash("")
        assert verify_password("", hashed) is True
        assert verify_password("not empty", hashed) is False


class TestTokenCreation:
    """Test JWT token creation functions."""
    
    def test_create_access_token_default_expiry(self):
        """Test access token creation with default expiry."""
        subject = "test-user-id"
        token = create_access_token(subject)
        
        # Decode token
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        assert payload["sub"] == subject
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload
    
    def test_create_access_token_custom_expiry(self):
        """Test access token creation with custom expiry."""
        subject = "test-user-id"
        expires_delta = timedelta(hours=1)
        
        token = create_access_token(subject, expires_delta)
        
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        # Check expiry is approximately 1 hour from now
        exp_time = datetime.fromtimestamp(payload["exp"])
        expected_exp = datetime.utcnow() + expires_delta
        
        # Allow 1 minute tolerance for test execution time
        assert abs((exp_time - expected_exp).total_seconds()) < 60
    
    def test_create_refresh_token(self):
        """Test refresh token creation."""
        subject = "test-user-id"
        token = create_refresh_token(subject)
        
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        assert payload["sub"] == subject
        assert payload["type"] == "refresh"
        assert "exp" in payload
        assert "iat" in payload
        
        # Check expiry is approximately 7 days from now
        exp_time = datetime.fromtimestamp(payload["exp"])
        expected_exp = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        # Allow 1 minute tolerance
        assert abs((exp_time - expected_exp).total_seconds()) < 60


class TestTokenDecoding:
    """Test JWT token decoding function."""
    
    def test_decode_valid_token(self):
        """Test decoding a valid token."""
        subject = "test-user-id"
        token = create_access_token(subject)
        
        payload = decode_token(token)
        
        assert payload is not None
        assert payload["sub"] == subject
        assert payload["type"] == "access"
    
    def test_decode_expired_token(self):
        """Test decoding an expired token."""
        subject = "test-user-id"
        # Create token that expires immediately
        token = create_access_token(subject, timedelta(seconds=-1))
        
        payload = decode_token(token)
        
        assert payload is None
    
    def test_decode_invalid_token(self):
        """Test decoding an invalid token."""
        invalid_token = "invalid.token.here"
        
        payload = decode_token(invalid_token)
        
        assert payload is None
    
    def test_decode_token_wrong_algorithm(self):
        """Test decoding token with wrong algorithm."""
        # Create token with different algorithm
        payload = {
            "sub": "test-user-id",
            "type": "access",
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        
        # Create token with HS512 instead of HS256
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS512")
        
        # Should fail to decode with HS256
        decoded = decode_token(token)
        
        assert decoded is None
    
    def test_decode_token_wrong_secret(self):
        """Test decoding token with wrong secret."""
        payload = {
            "sub": "test-user-id",
            "type": "access",
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        
        # Create token with different secret
        token = jwt.encode(payload, "wrong-secret", algorithm=settings.ALGORITHM)
        
        # Should fail to decode
        decoded = decode_token(token)
        
        assert decoded is None
    
    def test_token_types(self):
        """Test that access and refresh tokens have correct types."""
        subject = "test-user-id"
        
        access_token = create_access_token(subject)
        refresh_token = create_refresh_token(subject)
        
        access_payload = decode_token(access_token)
        refresh_payload = decode_token(refresh_token)
        
        assert access_payload["type"] == "access"
        assert refresh_payload["type"] == "refresh"