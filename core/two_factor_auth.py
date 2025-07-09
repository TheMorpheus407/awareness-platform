"""Two-Factor Authentication utilities."""

import pyotp
import qrcode
import secrets
import string
import hashlib
from io import BytesIO
from typing import List, Tuple, Optional
from base64 import b64encode, b64decode
from cryptography.fernet import Fernet
from core.config import settings


class TwoFactorAuth:
    """Utilities for managing Two-Factor Authentication."""
    
    def __init__(self):
        """Initialize with encryption key from settings."""
        # Derive a proper encryption key from SECRET_KEY
        # This ensures the key is persistent across app restarts
        key_material = hashlib.pbkdf2_hmac(
            'sha256',
            settings.SECRET_KEY.encode(),
            b'2fa_encryption_salt',  # Salt for key derivation
            100000  # Iterations
        )
        # Fernet requires a 32-byte key encoded as base64
        self.cipher_suite = Fernet(b64encode(key_material[:32]))
    
    def generate_secret(self) -> str:
        """Generate a new TOTP secret."""
        return pyotp.random_base32()
    
    def encrypt_secret(self, secret: str) -> str:
        """Encrypt TOTP secret for database storage."""
        return self.cipher_suite.encrypt(secret.encode()).decode()
    
    def decrypt_secret(self, encrypted_secret: str) -> str:
        """Decrypt TOTP secret from database."""
        return self.cipher_suite.decrypt(encrypted_secret.encode()).decode()
    
    def generate_qr_code(self, user_email: str, secret: str) -> str:
        """Generate QR code for TOTP setup.
        
        Args:
            user_email: User's email address
            secret: TOTP secret
            
        Returns:
            Base64 encoded QR code image
        """
        # Create provisioning URI
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user_email,
            issuer_name=settings.APP_NAME or "Cybersecurity Platform"
        )
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return b64encode(buffer.getvalue()).decode()
    
    def verify_totp(self, secret: str, token: str, window: int = 1) -> bool:
        """Verify a TOTP token.
        
        Args:
            secret: TOTP secret
            token: 6-digit token to verify
            window: Time window for validation (default: 1 = 30 seconds before/after)
            
        Returns:
            True if token is valid, False otherwise
        """
        try:
            totp = pyotp.TOTP(secret)
            return totp.verify(token, valid_window=window)
        except:
            return False
    
    def generate_backup_codes(self, count: int = 8) -> List[str]:
        """Generate backup codes for account recovery.
        
        Args:
            count: Number of backup codes to generate (default: 8)
            
        Returns:
            List of backup codes
        """
        codes = []
        # Generate codes in format: XXXX-XXXX
        for _ in range(count):
            part1 = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(4))
            part2 = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(4))
            codes.append(f"{part1}-{part2}")
        
        return codes
    
    def hash_backup_code(self, code: str) -> str:
        """Hash a backup code for storage.
        
        We store backup codes as hashes to prevent exposure if database is compromised.
        """
        from passlib.hash import bcrypt
        return bcrypt.hash(code)
    
    def verify_backup_code(self, code: str, hashed_code: str) -> bool:
        """Verify a backup code against its hash."""
        from passlib.hash import bcrypt
        try:
            return bcrypt.verify(code, hashed_code)
        except:
            return False
    
    def get_totp_uri(self, user_email: str, secret: str) -> str:
        """Get the TOTP provisioning URI for manual entry.
        
        Args:
            user_email: User's email address
            secret: TOTP secret
            
        Returns:
            TOTP provisioning URI
        """
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(
            name=user_email,
            issuer_name=settings.APP_NAME or "Cybersecurity Platform"
        )


# Global instance
two_factor_auth = TwoFactorAuth()