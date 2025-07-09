"""Two-factor authentication implementation using pyotp."""

import base64
import io
import secrets
from typing import List, Optional, Tuple

import pyotp
import qrcode
from PIL import Image

from core.config import settings
from core.logging import logger


class TwoFactorAuth:
    """Two-factor authentication utilities."""
    
    def __init__(self):
        """Initialize 2FA utilities."""
        self.issuer = settings.OTP_ISSUER
        self.validity_seconds = settings.OTP_VALIDITY_SECONDS
        self.backup_codes_count = settings.OTP_BACKUP_CODES_COUNT
    
    def generate_secret(self) -> str:
        """
        Generate a new TOTP secret.
        
        Returns:
            Base32-encoded secret key
        """
        # Generate 20 bytes (160 bits) of randomness
        random_bytes = secrets.token_bytes(20)
        # Encode to base32
        secret = base64.b32encode(random_bytes).decode('utf-8')
        return secret
    
    def generate_qr_code(self, secret: str, email: str) -> str:
        """
        Generate QR code for TOTP setup.
        
        Args:
            secret: TOTP secret key
            email: User's email address
            
        Returns:
            Base64-encoded QR code image
        """
        # Create TOTP URI
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=email,
            issuer_name=self.issuer
        )
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return f"data:image/png;base64,{qr_base64}"
    
    def verify_token(self, secret: str, token: str, window: int = 1) -> bool:
        """
        Verify a TOTP token.
        
        Args:
            secret: TOTP secret key
            token: Token to verify
            window: Number of time windows to check (for clock skew)
            
        Returns:
            True if token is valid, False otherwise
        """
        try:
            totp = pyotp.TOTP(secret)
            # Verify with time window for clock skew tolerance
            return totp.verify(token, valid_window=window)
        except Exception as e:
            logger.error(f"Error verifying TOTP token: {e}")
            return False
    
    def generate_backup_codes(self) -> List[str]:
        """
        Generate backup codes for 2FA recovery.
        
        Returns:
            List of backup codes
        """
        codes = []
        for _ in range(self.backup_codes_count):
            # Generate 8-character alphanumeric code
            code = ''.join(secrets.choice('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ') for _ in range(8))
            # Format as XXXX-XXXX for readability
            formatted_code = f"{code[:4]}-{code[4:]}"
            codes.append(formatted_code)
        
        return codes
    
    def hash_backup_code(self, code: str) -> str:
        """
        Hash a backup code for storage.
        
        Args:
            code: Backup code to hash
            
        Returns:
            Hashed backup code
        """
        # Remove formatting
        clean_code = code.replace('-', '')
        
        # Use the same password hasher for consistency
        from core.security import security
        return security.hash_password(clean_code)
    
    def verify_backup_code(self, code: str, hashed_code: str) -> bool:
        """
        Verify a backup code against its hash.
        
        Args:
            code: Backup code to verify
            hashed_code: Hashed backup code
            
        Returns:
            True if code matches, False otherwise
        """
        # Remove formatting
        clean_code = code.replace('-', '')
        
        # Use the same password verifier
        from core.security import security
        return security.verify_password(clean_code, hashed_code)
    
    def get_current_otp(self, secret: str) -> str:
        """
        Get the current OTP for a secret (for testing/debugging).
        
        Args:
            secret: TOTP secret key
            
        Returns:
            Current OTP code
        """
        totp = pyotp.TOTP(secret)
        return totp.now()
    
    def get_provisioning_uri(self, secret: str, email: str) -> str:
        """
        Get the provisioning URI for manual entry.
        
        Args:
            secret: TOTP secret key
            email: User's email address
            
        Returns:
            Provisioning URI string
        """
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(
            name=email,
            issuer_name=self.issuer
        )
    
    def generate_recovery_token(self) -> str:
        """
        Generate a recovery token for account recovery.
        
        Returns:
            Recovery token
        """
        # Generate a secure random token
        return secrets.token_urlsafe(32)
    
    def validate_token_format(self, token: str) -> Tuple[bool, Optional[str]]:
        """
        Validate the format of a TOTP token.
        
        Args:
            token: Token to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Remove any spaces or hyphens
        clean_token = token.replace(' ', '').replace('-', '')
        
        # Check if it's all digits
        if not clean_token.isdigit():
            return False, "Token must contain only digits"
        
        # Check length (TOTP tokens are typically 6 digits)
        if len(clean_token) != 6:
            return False, "Token must be exactly 6 digits"
        
        return True, None
    
    def time_remaining(self) -> int:
        """
        Get the time remaining for the current TOTP window.
        
        Returns:
            Seconds remaining in current window
        """
        import time
        current_time = int(time.time())
        return self.validity_seconds - (current_time % self.validity_seconds)


# Global 2FA instance
two_factor_auth = TwoFactorAuth()