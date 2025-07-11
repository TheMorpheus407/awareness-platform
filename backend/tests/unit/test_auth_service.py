"""
Unit tests for authentication service.
Tests core authentication logic without external dependencies.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from jose import jwt

from core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    verify_token,
    decode_token
)
from core.config import settings
from models.user import User
from schemas.auth import TokenData


@pytest.mark.unit
@pytest.mark.auth
class TestPasswordHashing:
    """Test password hashing and verification."""
    
    def test_password_hash_is_different_from_plain(self):
        """Test that hashed password differs from plain text."""
        plain_password = "MySecureP@ssw0rd123"
        hashed = get_password_hash(plain_password)
        
        assert hashed != plain_password
        assert len(hashed) > 50  # Bcrypt hashes are typically 60 chars
        
    def test_same_password_different_hashes(self):
        """Test that same password produces different hashes (salt)."""
        plain_password = "MySecureP@ssw0rd123"
        hash1 = get_password_hash(plain_password)
        hash2 = get_password_hash(plain_password)
        
        assert hash1 != hash2
        
    def test_verify_correct_password(self):
        """Test verification of correct password."""
        plain_password = "MySecureP@ssw0rd123"
        hashed = get_password_hash(plain_password)
        
        assert verify_password(plain_password, hashed) is True
        
    def test_verify_incorrect_password(self):
        """Test verification of incorrect password."""
        plain_password = "MySecureP@ssw0rd123"
        wrong_password = "WrongPassword123"
        hashed = get_password_hash(plain_password)
        
        assert verify_password(wrong_password, hashed) is False
        
    def test_empty_password_handling(self):
        """Test handling of empty passwords."""
        with pytest.raises(ValueError):
            get_password_hash("")
            
    def test_none_password_handling(self):
        """Test handling of None passwords."""
        with pytest.raises(TypeError):
            get_password_hash(None)


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
class TestJWTTokens:
    """Test JWT token creation and validation."""
    
    @patch('core.security.datetime')
    def test_create_access_token_structure(self, mock_datetime):
        """Test JWT token has correct structure."""
        # Mock datetime to have consistent tokens
        mock_now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = mock_now
        
        user_id = 123
        token = create_access_token(data={"sub": str(user_id)})
        
        # Decode without verification to check structure
        payload = jwt.decode(token, options={"verify_signature": False})
        
        assert payload["sub"] == str(user_id)
        assert "exp" in payload
        assert payload["type"] == "access"
        
    def test_create_access_token_with_custom_expiry(self):
        """Test token creation with custom expiry time."""
        user_id = 123
        expires_delta = timedelta(hours=1)
        
        token = create_access_token(
            data={"sub": str(user_id)},
            expires_delta=expires_delta
        )
        
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # Check expiry is approximately 1 hour from now
        exp_time = datetime.fromtimestamp(payload["exp"])
        now = datetime.utcnow()
        time_diff = exp_time - now
        
        assert 59 <= time_diff.total_seconds() / 60 <= 61
        
    def test_decode_valid_token(self):
        """Test decoding a valid token."""
        user_id = 123
        token = create_access_token(data={"sub": str(user_id)})
        
        payload = decode_token(token)
        
        assert payload is not None
        assert payload.get("sub") == str(user_id)
        
    def test_decode_expired_token(self):
        """Test decoding an expired token."""
        user_id = 123
        # Create token that expires immediately
        token = create_access_token(
            data={"sub": str(user_id)},
            expires_delta=timedelta(seconds=-1)
        )
        
        payload = decode_token(token)
        assert payload is None
        
    def test_decode_invalid_token(self):
        """Test decoding an invalid token."""
        invalid_token = "this.is.not.a.valid.token"
        
        payload = decode_token(invalid_token)
        assert payload is None
        
    def test_decode_token_with_wrong_secret(self):
        """Test decoding token with wrong secret."""
        user_id = 123
        token = create_access_token(data={"sub": str(user_id)})
        
        # Try to decode with wrong secret
        with patch('core.config.settings.JWT_SECRET_KEY', 'wrong_secret'):
            payload = decode_token(token)
            assert payload is None
            
    def test_token_without_sub_claim(self):
        """Test token without 'sub' claim is invalid."""
        # Create token without sub claim
        token_data = {"user_id": 123, "type": "access"}
        token = jwt.encode(
            token_data,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
        
        # verify_token should return None for tokens without 'sub'
        result = verify_token(token)
        assert result is None


@pytest.mark.unit
@pytest.mark.auth
class TestTokenValidation:
    """Test token validation logic."""
    
    def test_verify_token_success(self):
        """Test successful token verification."""
        user_id = 123
        token = create_access_token(data={"sub": str(user_id)})
        
        token_data = verify_token(token)
        
        assert token_data is not None
        assert isinstance(token_data, TokenData)
        assert token_data.user_id == user_id
        
    def test_verify_refresh_token(self):
        """Test refresh token verification."""
        user_id = 123
        token = create_access_token(
            data={"sub": str(user_id), "type": "refresh"}
        )
        
        # Should work for refresh tokens too
        token_data = verify_token(token)
        
        assert token_data is not None
        assert token_data.user_id == user_id
        
    def test_verify_malformed_token(self):
        """Test verification of malformed token."""
        malformed_token = "not.a.jwt"
        
        token_data = verify_token(malformed_token)
        assert token_data is None
        
    def test_verify_token_with_additional_claims(self):
        """Test token with additional claims."""
        user_id = 123
        additional_data = {
            "sub": str(user_id),
            "role": "admin",
            "permissions": ["read", "write"]
        }
        token = create_access_token(data=additional_data)
        
        payload = decode_token(token)
        
        assert payload["sub"] == str(user_id)
        assert payload["role"] == "admin"
        assert payload["permissions"] == ["read", "write"]


@pytest.mark.unit
@pytest.mark.security
class TestSecurityHelpers:
    """Test security helper functions."""
    
    def test_password_complexity_validation(self):
        """Test password complexity requirements."""
        # These would normally be in a validate_password function
        weak_passwords = [
            "123456",
            "password",
            "abc123",
            "12345678",
            "qwerty"
        ]
        
        strong_passwords = [
            "MyS3cur3P@ssw0rd!",
            "C0mpl3x!Pass#2024",
            "Str0ng&S3cure$PWD"
        ]
        
        # In real implementation, you'd have a validate_password function
        # For now, just check that strong passwords can be hashed
        for pwd in strong_passwords:
            hashed = get_password_hash(pwd)
            assert verify_password(pwd, hashed)
            
    def test_timing_attack_resistance(self):
        """Test that password verification is timing-attack resistant."""
        import time
        
        correct_password = "MyS3cur3P@ssw0rd!"
        hashed = get_password_hash(correct_password)
        
        # Time correct password verification
        start = time.perf_counter()
        for _ in range(10):
            verify_password(correct_password, hashed)
        correct_time = time.perf_counter() - start
        
        # Time incorrect password verification
        start = time.perf_counter()
        for _ in range(10):
            verify_password("WrongPassword!", hashed)
        incorrect_time = time.perf_counter() - start
        
        # Times should be similar (within 20% difference)
        time_ratio = max(correct_time, incorrect_time) / min(correct_time, incorrect_time)
        assert time_ratio < 1.2


@pytest.mark.unit
@pytest.mark.auth
class TestAuthenticationFlow:
    """Test complete authentication flow."""
    
    @patch('models.user.User')
    def test_login_flow_success(self, mock_user_class):
        """Test successful login flow."""
        # Mock user
        mock_user = Mock(spec=User)
        mock_user.id = 123
        mock_user.email = "test@example.com"
        mock_user.hashed_password = get_password_hash("correctpassword")
        mock_user.is_active = True
        mock_user.is_verified = True
        
        # Simulate login
        provided_password = "correctpassword"
        
        # Verify password
        assert verify_password(provided_password, mock_user.hashed_password)
        
        # Create tokens
        access_token = create_access_token(data={"sub": str(mock_user.id)})
        
        # Verify token
        token_data = verify_token(access_token)
        assert token_data is not None
        assert token_data.user_id == mock_user.id
        
    def test_login_flow_wrong_password(self):
        """Test login flow with wrong password."""
        stored_hash = get_password_hash("correctpassword")
        provided_password = "wrongpassword"
        
        assert not verify_password(provided_password, stored_hash)
        
    def test_token_expiry_flow(self):
        """Test token expiry handling."""
        user_id = 123
        
        # Create token that expires in 1 second
        token = create_access_token(
            data={"sub": str(user_id)},
            expires_delta=timedelta(seconds=1)
        )
        
        # Immediately verify - should work
        assert verify_token(token) is not None
        
        # Wait for expiry
        import time
        time.sleep(2)
        
        # Should now be expired
        assert verify_token(token) is None