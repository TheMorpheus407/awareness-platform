"""Simple authentication utilities for MVP."""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import secrets

from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
import pyotp

from backend.core.config import settings
from backend.models.user import User

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Token settings
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any]) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")


def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")


def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    """Verify and decode JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        if payload.get("type") != token_type:
            return None
        return payload
    except JWTError:
        return None


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate user with email and password."""
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


def generate_2fa_secret() -> str:
    """Generate a new 2FA secret."""
    return pyotp.random_base32()


def generate_2fa_qr_uri(email: str, secret: str) -> str:
    """Generate QR code URI for 2FA setup."""
    return pyotp.totp.TOTP(secret).provisioning_uri(
        name=email,
        issuer_name=settings.APP_NAME
    )


def verify_2fa_token(secret: str, token: str) -> bool:
    """Verify a 2FA token."""
    totp = pyotp.TOTP(secret)
    return totp.verify(token, valid_window=1)


def generate_password_reset_token() -> str:
    """Generate a secure password reset token."""
    return secrets.token_urlsafe(32)