"""Tests for Two-Factor Authentication utilities."""

import pytest
import pyotp
from unittest.mock import patch
import base64

from core.two_factor_auth import two_factor_auth


class TestTwoFactorAuth:
    """Test cases for TwoFactorAuth class."""
    
    def test_generate_secret(self):
        """Test secret generation."""
        secret = two_factor_auth.generate_secret()
        
        # Should be a valid base32 string
        assert isinstance(secret, str)
        assert len(secret) == 32
        
        # Should be valid for TOTP
        totp = pyotp.TOTP(secret)
        assert totp.now() is not None
    
    def test_encrypt_decrypt_secret(self):
        """Test secret encryption and decryption."""
        original_secret = "TESTSECRETSECRET"
        
        # Encrypt
        encrypted = two_factor_auth.encrypt_secret(original_secret)
        assert encrypted != original_secret
        assert isinstance(encrypted, str)
        
        # Decrypt
        decrypted = two_factor_auth.decrypt_secret(encrypted)
        assert decrypted == original_secret
    
    def test_generate_qr_code(self):
        """Test QR code generation."""
        secret = two_factor_auth.generate_secret()
        email = "test@example.com"
        
        qr_code_base64 = two_factor_auth.generate_qr_code(email, secret)
        
        # Should be a valid base64 string
        assert isinstance(qr_code_base64, str)
        
        # Should be decodable
        try:
            decoded = base64.b64decode(qr_code_base64)
            assert len(decoded) > 0
        except:
            pytest.fail("QR code is not valid base64")
        
        # Should start with PNG header
        assert decoded[:8] == b'\x89PNG\r\n\x1a\n'
    
    def test_verify_totp_valid(self):
        """Test TOTP verification with valid code."""
        secret = two_factor_auth.generate_secret()
        totp = pyotp.TOTP(secret)
        current_code = totp.now()
        
        # Should verify current code
        assert two_factor_auth.verify_totp(secret, current_code) is True
    
    def test_verify_totp_invalid(self):
        """Test TOTP verification with invalid code."""
        secret = two_factor_auth.generate_secret()
        
        # Should not verify invalid code
        assert two_factor_auth.verify_totp(secret, "000000") is False
        assert two_factor_auth.verify_totp(secret, "invalid") is False
        assert two_factor_auth.verify_totp(secret, "") is False
    
    def test_generate_backup_codes(self):
        """Test backup code generation."""
        codes = two_factor_auth.generate_backup_codes()
        
        # Should generate 8 codes by default
        assert len(codes) == 8
        
        # All codes should be unique
        assert len(set(codes)) == 8
        
        # Should have correct format: XXXX-XXXX
        for code in codes:
            assert len(code) == 9
            assert code[4] == '-'
            assert code[:4].isalnum()
            assert code[5:].isalnum()
    
    def test_generate_backup_codes_custom_count(self):
        """Test backup code generation with custom count."""
        codes = two_factor_auth.generate_backup_codes(count=12)
        assert len(codes) == 12
        assert len(set(codes)) == 12
    
    def test_hash_and_verify_backup_code(self):
        """Test backup code hashing and verification."""
        code = "TEST-CODE"
        
        # Hash the code
        hashed = two_factor_auth.hash_backup_code(code)
        assert hashed != code
        assert isinstance(hashed, str)
        
        # Should verify correctly
        assert two_factor_auth.verify_backup_code(code, hashed) is True
        
        # Should not verify wrong code
        assert two_factor_auth.verify_backup_code("WRONG-CODE", hashed) is False
    
    def test_get_totp_uri(self):
        """Test TOTP URI generation."""
        secret = "TESTSECRETSECRET"
        email = "user@example.com"
        
        uri = two_factor_auth.get_totp_uri(email, secret)
        
        # Should contain required components
        assert uri.startswith("otpauth://totp/")
        assert email in uri
        assert f"secret={secret}" in uri
        assert "issuer=" in uri
    
    def test_encryption_persistence(self):
        """Test that encryption key is persistent."""
        secret = "PERSISTENCETEST"
        
        # Encrypt with first instance
        encrypted1 = two_factor_auth.encrypt_secret(secret)
        
        # Create new instance (simulating app restart)
        from core.two_factor_auth import TwoFactorAuth
        new_instance = TwoFactorAuth()
        
        # Should be able to decrypt with new instance
        decrypted = new_instance.decrypt_secret(encrypted1)
        assert decrypted == secret