# Security Spezifikation - Cybersecurity Awareness Platform
**Version 1.0 | Comprehensive Security Guidelines**

## 1. Security Architecture Overview

### 1.1 Defense in Depth Layers
```
┌─────────────────────────────────────────────┐
│          Application Security               │
│  ┌─────────────────────────────────────┐  │
│  │      Authentication & Authorization   │  │
│  │  ┌─────────────────────────────────┐ │  │
│  │  │       Data Protection          │ │  │
│  │  │  ┌─────────────────────────┐   │ │  │
│  │  │  │   Network Security     │   │ │  │
│  │  │  │  ┌─────────────────┐  │   │ │  │
│  │  │  │  │ Infrastructure  │  │   │ │  │
│  │  │  │  │    Security     │  │   │ │  │
│  │  │  │  └─────────────────┘  │   │ │  │
│  │  │  └─────────────────────────┘   │ │  │
│  │  └─────────────────────────────────┘ │  │
│  └─────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

### 1.2 Security Principles
- **Zero Trust Architecture**: Never trust, always verify
- **Principle of Least Privilege**: Minimal necessary permissions
- **Defense in Depth**: Multiple security layers
- **Security by Design**: Built-in, not bolted-on
- **Data Minimization**: Collect only necessary data

## 2. Authentication & Authorization

### 2.1 Authentication Implementation

#### JWT Token Structure
```typescript
// Token Payload Structure
interface JWTPayload {
  sub: string;          // User ID
  email: string;        // User email
  company_id: string;   // Company ID
  role: UserRole;       // User role
  permissions: string[]; // Granular permissions
  iat: number;          // Issued at
  exp: number;          // Expiration
  jti: string;          // JWT ID for revocation
}
```

#### Token Management
```python
# backend/app/core/security.py
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import secrets
from jose import JWTError, jwt
from passlib.context import CryptContext
from redis import Redis

class TokenManager:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
    def create_access_token(
        self, 
        user_id: str, 
        user_data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=30)
        
        # Generate unique JWT ID
        jti = secrets.token_urlsafe(16)
        
        payload = {
            "sub": user_id,
            "email": user_data["email"],
            "company_id": user_data["company_id"],
            "role": user_data["role"],
            "permissions": self._get_role_permissions(user_data["role"]),
            "exp": expire,
            "iat": datetime.utcnow(),
            "jti": jti
        }
        
        # Store JTI in Redis for revocation capability
        self.redis.setex(
            f"jwt:{jti}",
            timedelta(minutes=30),
            user_id
        )
        
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    def create_refresh_token(self, user_id: str) -> str:
        """Create long-lived refresh token"""
        token = secrets.token_urlsafe(32)
        
        # Store in Redis with longer expiration
        self.redis.setex(
            f"refresh:{token}",
            timedelta(days=7),
            user_id
        )
        
        return token
    
    def revoke_token(self, jti: str) -> bool:
        """Revoke a specific token"""
        return self.redis.delete(f"jwt:{jti}") > 0
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=[settings.ALGORITHM]
            )
            
            # Check if token is revoked
            jti = payload.get("jti")
            if not self.redis.exists(f"jwt:{jti}"):
                return None
                
            return payload
        except JWTError:
            return None
    
    def _get_role_permissions(self, role: str) -> List[str]:
        """Get permissions based on role"""
        permissions_map = {
            "admin": [
                "users:read", "users:write", "users:delete",
                "courses:read", "courses:write", "courses:delete",
                "phishing:read", "phishing:write", "phishing:execute",
                "reports:read", "reports:generate",
                "settings:read", "settings:write"
            ],
            "manager": [
                "users:read", "users:write",
                "courses:read", "courses:assign",
                "phishing:read", "phishing:execute",
                "reports:read", "reports:generate"
            ],
            "employee": [
                "courses:read", "courses:complete",
                "reports:read:own"
            ]
        }
        return permissions_map.get(role, [])
```

### 2.2 Multi-Factor Authentication

#### TOTP Implementation
```python
# backend/app/services/mfa_service.py
import pyotp
import qrcode
from io import BytesIO
import base64

class MFAService:
    def __init__(self):
        self.issuer = "CyberSec Awareness Platform"
    
    def generate_totp_secret(self) -> str:
        """Generate new TOTP secret"""
        return pyotp.random_base32()
    
    def generate_qr_code(self, user_email: str, secret: str) -> str:
        """Generate QR code for TOTP setup"""
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user_email,
            issuer_name=self.issuer
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buf = BytesIO()
        img.save(buf, format='PNG')
        
        return base64.b64encode(buf.getvalue()).decode()
    
    def verify_totp(self, secret: str, token: str) -> bool:
        """Verify TOTP token"""
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)
    
    def generate_backup_codes(self, count: int = 10) -> List[str]:
        """Generate backup codes for account recovery"""
        return [secrets.token_hex(4) for _ in range(count)]
```

### 2.3 OAuth2 Integration

```python
# backend/app/core/oauth.py
from authlib.integrations.starlette_client import OAuth
from fastapi import HTTPException

oauth = OAuth()

# Configure OAuth providers
oauth.register(
    name='google',
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

oauth.register(
    name='microsoft',
    client_id=settings.MICROSOFT_CLIENT_ID,
    client_secret=settings.MICROSOFT_CLIENT_SECRET,
    authorize_url='https://login.microsoftonline.com/common/oauth2/v2.0/authorize',
    token_url='https://login.microsoftonline.com/common/oauth2/v2.0/token',
    client_kwargs={
        'scope': 'openid email profile'
    }
)
```

## 3. Authorization & Access Control

### 3.1 Permission-Based Access Control

```python
# backend/app/core/permissions.py
from typing import List, Optional
from fastapi import Depends, HTTPException, status
from functools import wraps

class PermissionChecker:
    def __init__(self, required_permissions: List[str]):
        self.required_permissions = required_permissions
    
    def __call__(self, current_user: User = Depends(get_current_user)):
        user_permissions = current_user.permissions
        
        for permission in self.required_permissions:
            if permission not in user_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied. Required: {permission}"
                )
        
        return current_user

# Usage example
@router.post("/users", dependencies=[Depends(PermissionChecker(["users:write"]))])
async def create_user(user_data: UserCreate):
    pass
```

### 3.2 Row-Level Security

```python
# backend/app/core/rls.py
from sqlalchemy.orm import Query
from typing import Optional

class RLSMixin:
    """Row Level Security mixin for SQLAlchemy models"""
    
    @classmethod
    def apply_rls(cls, query: Query, user: User) -> Query:
        """Apply row-level security filters"""
        if hasattr(cls, 'company_id'):
            # Filter by company
            query = query.filter(cls.company_id == user.company_id)
        
        if hasattr(cls, 'user_id') and user.role == UserRole.EMPLOYEE:
            # Employees can only see their own data
            query = query.filter(cls.user_id == user.id)
        
        return query

# Model implementation
class UserCourseProgress(Base, RLSMixin):
    __tablename__ = "user_course_progress"
    
    id = Column(UUID, primary_key=True)
    user_id = Column(UUID, ForeignKey("users.id"))
    company_id = Column(UUID, ForeignKey("companies.id"))
    # ... other fields
```

## 4. Data Protection

### 4.1 Encryption at Rest

```python
# backend/app/core/encryption.py
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

class EncryptionService:
    def __init__(self, master_key: str):
        # Derive encryption key from master key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'stable_salt',  # In production, use proper salt management
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(master_key.encode()))
        self.cipher = Fernet(key)
    
    def encrypt_field(self, value: str) -> str:
        """Encrypt a field value"""
        return self.cipher.encrypt(value.encode()).decode()
    
    def decrypt_field(self, encrypted_value: str) -> str:
        """Decrypt a field value"""
        return self.cipher.decrypt(encrypted_value.encode()).decode()
    
    def encrypt_file(self, file_path: str) -> bytes:
        """Encrypt file contents"""
        with open(file_path, 'rb') as file:
            return self.cipher.encrypt(file.read())
    
    def decrypt_file(self, encrypted_data: bytes) -> bytes:
        """Decrypt file contents"""
        return self.cipher.decrypt(encrypted_data)
```

### 4.2 Database Field Encryption

```python
# backend/app/models/encrypted_fields.py
from sqlalchemy import TypeDecorator, String
from app.core.encryption import EncryptionService

encryption_service = EncryptionService(settings.FIELD_ENCRYPTION_KEY)

class EncryptedString(TypeDecorator):
    """Automatically encrypt/decrypt string fields"""
    impl = String
    
    def process_bind_param(self, value, dialect):
        if value is not None:
            return encryption_service.encrypt_field(value)
        return value
    
    def process_result_value(self, value, dialect):
        if value is not None:
            return encryption_service.decrypt_field(value)
        return value

# Usage in models
class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID, primary_key=True)
    email = Column(String, unique=True)  # Not encrypted for lookups
    ssn = Column(EncryptedString)  # Encrypted sensitive data
    tax_id = Column(EncryptedString)  # Encrypted sensitive data
```

### 4.3 Data Anonymization

```python
# backend/app/services/anonymization_service.py
import hashlib
from faker import Faker

class AnonymizationService:
    def __init__(self):
        self.faker = Faker(['de_DE'])
    
    def anonymize_user(self, user: User) -> Dict[str, Any]:
        """Anonymize user data for GDPR compliance"""
        # Generate consistent fake data based on user ID
        seed = int(hashlib.md5(str(user.id).encode()).hexdigest()[:8], 16)
        self.faker.seed_instance(seed)
        
        return {
            "id": user.id,
            "email": f"user_{hashlib.sha256(user.email.encode()).hexdigest()[:8]}@example.com",
            "first_name": self.faker.first_name(),
            "last_name": self.faker.last_name(),
            "department": user.department,  # Keep for statistics
            "role": user.role,
            "risk_score": user.risk_score,
            "anonymized": True,
            "anonymized_at": datetime.utcnow()
        }
    
    def pseudonymize_data(self, data: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
        """Pseudonymize specific fields"""
        result = data.copy()
        
        for field in fields:
            if field in result:
                # Create reversible pseudonym
                result[field] = base64.b64encode(
                    hashlib.sha256(f"{result[field]}{settings.PSEUDONYM_SALT}".encode()).digest()
                ).decode()[:16]
        
        return result
```

## 5. Input Validation & Sanitization

### 5.1 Request Validation

```python
# backend/app/core/validation.py
from pydantic import BaseModel, validator, EmailStr
import re
from typing import Optional
import bleach

class SecureValidationMixin:
    """Mixin for secure input validation"""
    
    @validator('*', pre=True)
    def strip_strings(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v
    
    @validator('*')
    def prevent_null_bytes(cls, v):
        if isinstance(v, str) and '\x00' in v:
            raise ValueError('Null bytes not allowed')
        return v

class UserCreateSecure(BaseModel, SecureValidationMixin):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain number')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain special character')
        return v
    
    @validator('first_name', 'last_name')
    def validate_name(cls, v):
        # Remove any HTML/script tags
        cleaned = bleach.clean(v, tags=[], strip=True)
        if cleaned != v:
            raise ValueError('Invalid characters in name')
        
        # Check for SQL injection patterns
        sql_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|CREATE|ALTER)\b)",
            r"(--|;|'|\"|`|\\)",
            r"(\bOR\b.*=.*)",
            r"(\bAND\b.*=.*)"
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError('Invalid input detected')
        
        return cleaned
```

### 5.2 File Upload Security

```python
# backend/app/core/file_security.py
import magic
import hashlib
from pathlib import Path
import uuid

class SecureFileHandler:
    ALLOWED_EXTENSIONS = {'.pdf', '.png', '.jpg', '.jpeg', '.csv', '.xlsx'}
    ALLOWED_MIME_TYPES = {
        'application/pdf',
        'image/png',
        'image/jpeg',
        'text/csv',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    }
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    def __init__(self, upload_dir: str):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(exist_ok=True)
    
    async def save_uploaded_file(
        self, 
        file: UploadFile,
        user_id: str,
        scan_for_malware: bool = True
    ) -> Dict[str, Any]:
        """Securely save uploaded file"""
        
        # Check file size
        contents = await file.read()
        if len(contents) > self.MAX_FILE_SIZE:
            raise ValueError(f"File too large. Maximum size: {self.MAX_FILE_SIZE} bytes")
        
        # Reset file position
        await file.seek(0)
        
        # Check file extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in self.ALLOWED_EXTENSIONS:
            raise ValueError(f"File type not allowed: {file_ext}")
        
        # Check MIME type
        mime = magic.from_buffer(contents, mime=True)
        if mime not in self.ALLOWED_MIME_TYPES:
            raise ValueError(f"MIME type not allowed: {mime}")
        
        # Scan for malware if enabled
        if scan_for_malware:
            if not await self._scan_file(contents):
                raise ValueError("File failed security scan")
        
        # Generate secure filename
        file_hash = hashlib.sha256(contents).hexdigest()
        secure_filename = f"{user_id}_{uuid.uuid4().hex}_{file_hash[:8]}{file_ext}"
        
        # Save file
        file_path = self.upload_dir / secure_filename
        with open(file_path, 'wb') as f:
            f.write(contents)
        
        # Set restrictive permissions
        file_path.chmod(0o640)
        
        return {
            "filename": secure_filename,
            "original_filename": file.filename,
            "size": len(contents),
            "mime_type": mime,
            "hash": file_hash,
            "path": str(file_path)
        }
    
    async def _scan_file(self, contents: bytes) -> bool:
        """Scan file for malware using ClamAV or similar"""
        # Implementation depends on malware scanning service
        # Example with pyclamd:
        try:
            import pyclamd
            cd = pyclamd.ClamdUnixSocket()
            result = cd.scan_stream(contents)
            return result is None
        except:
            # If scanning fails, be safe and reject
            return False
```

## 6. API Security

### 6.1 Rate Limiting

```python
# backend/app/middleware/rate_limit.py
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import time
from collections import defaultdict
import asyncio

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients = defaultdict(list)
        self._cleanup_task = asyncio.create_task(self._cleanup())
    
    async def dispatch(self, request: Request, call_next):
        # Get client identifier
        client_id = self._get_client_id(request)
        
        # Get current time
        now = time.time()
        
        # Clean old entries
        self.clients[client_id] = [
            timestamp for timestamp in self.clients[client_id]
            if timestamp > now - self.period
        ]
        
        # Check rate limit
        if len(self.clients[client_id]) >= self.calls:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
                headers={
                    "X-RateLimit-Limit": str(self.calls),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(now + self.period))
                }
            )
        
        # Add current request
        self.clients[client_id].append(now)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.calls)
        response.headers["X-RateLimit-Remaining"] = str(
            self.calls - len(self.clients[client_id])
        )
        response.headers["X-RateLimit-Reset"] = str(int(now + self.period))
        
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier from request"""
        # Try to get authenticated user ID
        if hasattr(request.state, "user_id"):
            return f"user:{request.state.user_id}"
        
        # Fall back to IP address
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return f"ip:{forwarded.split(',')[0].strip()}"
        
        return f"ip:{request.client.host}"
    
    async def _cleanup(self):
        """Periodic cleanup of old entries"""
        while True:
            await asyncio.sleep(300)  # Every 5 minutes
            now = time.time()
            
            # Clean up old entries
            for client_id in list(self.clients.keys()):
                self.clients[client_id] = [
                    timestamp for timestamp in self.clients[client_id]
                    if timestamp > now - self.period
                ]
                
                # Remove empty entries
                if not self.clients[client_id]:
                    del self.clients[client_id]
```

### 6.2 API Key Management

```python
# backend/app/services/api_key_service.py
import secrets
import hashlib
from datetime import datetime, timedelta

class APIKeyService:
    def __init__(self, db: Session):
        self.db = db
    
    def generate_api_key(
        self, 
        user_id: str, 
        name: str,
        permissions: List[str],
        expires_in_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generate new API key"""
        # Generate secure random key
        raw_key = secrets.token_urlsafe(32)
        
        # Hash for storage
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        
        # Calculate expiration
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        
        # Store in database
        api_key = APIKey(
            user_id=user_id,
            name=name,
            key_hash=key_hash,
            permissions=permissions,
            expires_at=expires_at,
            last_used_at=None
        )
        self.db.add(api_key)
        self.db.commit()
        
        # Return key only once
        return {
            "id": api_key.id,
            "key": raw_key,
            "name": name,
            "created_at": api_key.created_at,
            "expires_at": expires_at
        }
    
    def verify_api_key(self, raw_key: str) -> Optional[APIKey]:
        """Verify API key and return associated data"""
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        
        api_key = self.db.query(APIKey).filter(
            APIKey.key_hash == key_hash,
            APIKey.is_active == True
        ).first()
        
        if not api_key:
            return None
        
        # Check expiration
        if api_key.expires_at and api_key.expires_at < datetime.utcnow():
            return None
        
        # Update last used
        api_key.last_used_at = datetime.utcnow()
        self.db.commit()
        
        return api_key
```

## 7. Infrastructure Security

### 7.1 Container Security

```dockerfile
# Secure Dockerfile example
FROM python:3.11-slim AS base

# Security updates
RUN apt-get update && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=appuser:appuser . .

# Security scanning
RUN pip install safety && safety check

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run with limited permissions
CMD ["gunicorn", "main:app", "--bind", "0.0.0.0:8000", "--workers", "4"]
```

### 7.2 Network Security

```yaml
# docker-compose.security.yml
version: '3.9'

services:
  backend:
    networks:
      - internal
      - database
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    read_only: true
    tmpfs:
      - /tmp
    environment:
      - PYTHONDONTWRITEBYTECODE=1

  postgres:
    networks:
      - database
    security_opt:
      - no-new-privileges:true
    environment:
      - POSTGRES_INITDB_ARGS=--auth-host=scram-sha-256 --auth-local=trust

  nginx:
    networks:
      - external
      - internal
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
      - CHOWN
      - SETUID
      - SETGID

networks:
  external:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
  internal:
    driver: bridge
    internal: true
    ipam:
      config:
        - subnet: 172.21.0.0/16
  database:
    driver: bridge
    internal: true
    ipam:
      config:
        - subnet: 172.22.0.0/16
```

### 7.3 Secrets Management

```python
# backend/app/core/secrets_manager.py
import hvac
from typing import Dict, Any, Optional
import json

class SecretsManager:
    def __init__(self, vault_url: str, vault_token: str):
        self.client = hvac.Client(url=vault_url, token=vault_token)
        
        if not self.client.is_authenticated():
            raise Exception("Failed to authenticate with Vault")
    
    def get_secret(self, path: str) -> Dict[str, Any]:
        """Retrieve secret from Vault"""
        response = self.client.read(path)
        if response is None:
            raise KeyError(f"Secret not found at path: {path}")
        
        return response['data']['data']
    
    def set_secret(self, path: str, secret: Dict[str, Any]) -> None:
        """Store secret in Vault"""
        self.client.write(path, data=secret)
    
    def rotate_database_credentials(self) -> Dict[str, str]:
        """Rotate database credentials"""
        # Request new credentials from Vault
        response = self.client.read('database/creds/cybersec-app')
        
        return {
            'username': response['data']['username'],
            'password': response['data']['password']
        }
    
    def get_encryption_key(self, key_name: str) -> bytes:
        """Get encryption key from Vault"""
        response = self.client.read(f'transit/keys/{key_name}')
        return base64.b64decode(response['data']['keys']['1'])

# Usage
secrets_manager = SecretsManager(
    vault_url=os.getenv("VAULT_URL"),
    vault_token=os.getenv("VAULT_TOKEN")
)

# Get database credentials
db_creds = secrets_manager.get_secret("secret/data/database")
DATABASE_URL = f"postgresql://{db_creds['username']}:{db_creds['password']}@{db_creds['host']}/cybersec_db"
```

## 8. Security Monitoring & Logging

### 8.1 Security Event Logging

```python
# backend/app/core/security_logger.py
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
import traceback

class SecurityLogger:
    def __init__(self, logger_name: str = "security"):
        self.logger = logging.getLogger(logger_name)
        handler = logging.StreamHandler()
        handler.setFormatter(self._get_formatter())
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def _get_formatter(self):
        return logging.Formatter(
            json.dumps({
                "timestamp": "%(asctime)s",
                "level": "%(levelname)s",
                "event_type": "%(event_type)s",
                "user_id": "%(user_id)s",
                "ip_address": "%(ip_address)s",
                "details": "%(details)s",
                "trace_id": "%(trace_id)s"
            })
        )
    
    def log_authentication_attempt(
        self, 
        success: bool,
        user_email: str,
        ip_address: str,
        reason: Optional[str] = None,
        trace_id: Optional[str] = None
    ):
        """Log authentication attempts"""
        self.logger.info(
            "Authentication attempt",
            extra={
                "event_type": "auth_attempt",
                "user_id": user_email,
                "ip_address": ip_address,
                "details": json.dumps({
                    "success": success,
                    "reason": reason
                }),
                "trace_id": trace_id or ""
            }
        )
    
    def log_authorization_failure(
        self,
        user_id: str,
        resource: str,
        action: str,
        ip_address: str,
        trace_id: Optional[str] = None
    ):
        """Log authorization failures"""
        self.logger.warning(
            "Authorization failure",
            extra={
                "event_type": "auth_failure",
                "user_id": user_id,
                "ip_address": ip_address,
                "details": json.dumps({
                    "resource": resource,
                    "action": action
                }),
                "trace_id": trace_id or ""
            }
        )
    
    def log_suspicious_activity(
        self,
        activity_type: str,
        user_id: Optional[str],
        ip_address: str,
        details: Dict[str, Any],
        trace_id: Optional[str] = None
    ):
        """Log suspicious activities"""
        self.logger.warning(
            "Suspicious activity detected",
            extra={
                "event_type": f"suspicious_{activity_type}",
                "user_id": user_id or "anonymous",
                "ip_address": ip_address,
                "details": json.dumps(details),
                "trace_id": trace_id or ""
            }
        )
    
    def log_data_access(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        action: str,
        ip_address: str,
        trace_id: Optional[str] = None
    ):
        """Log sensitive data access"""
        self.logger.info(
            "Data access",
            extra={
                "event_type": "data_access",
                "user_id": user_id,
                "ip_address": ip_address,
                "details": json.dumps({
                    "resource_type": resource_type,
                    "resource_id": resource_id,
                    "action": action
                }),
                "trace_id": trace_id or ""
            }
        )

# Initialize global security logger
security_logger = SecurityLogger()
```

### 8.2 Intrusion Detection

```python
# backend/app/services/intrusion_detection.py
from typing import Dict, List, Optional
import re
from datetime import datetime, timedelta

class IntrusionDetectionService:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.patterns = self._load_attack_patterns()
    
    def _load_attack_patterns(self) -> Dict[str, List[re.Pattern]]:
        """Load known attack patterns"""
        return {
            "sql_injection": [
                re.compile(r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION)\b)", re.I),
                re.compile(r"(--|\||;|'|\")"),
                re.compile(r"(\bOR\b.*=.*)", re.I),
            ],
            "xss": [
                re.compile(r"<script[^>]*>.*?</script>", re.I),
                re.compile(r"javascript:", re.I),
                re.compile(r"on\w+\s*=", re.I),
            ],
            "path_traversal": [
                re.compile(r"\.\.(/|\\)"),
                re.compile(r"%2e%2e(/|\\)", re.I),
                re.compile(r"\.\.%2f", re.I),
            ],
            "command_injection": [
                re.compile(r"[;&|`]\s*(ls|cat|rm|wget|curl|nc)", re.I),
                re.compile(r"\$\(.*\)"),
                re.compile(r"`.*`"),
            ]
        }
    
    async def check_request(
        self, 
        request_data: Dict[str, Any],
        user_id: Optional[str] = None,
        ip_address: str = None
    ) -> Optional[Dict[str, Any]]:
        """Check request for suspicious patterns"""
        threats = []
        
        # Check all string values in request
        for key, value in request_data.items():
            if isinstance(value, str):
                for attack_type, patterns in self.patterns.items():
                    for pattern in patterns:
                        if pattern.search(value):
                            threats.append({
                                "type": attack_type,
                                "field": key,
                                "pattern": pattern.pattern
                            })
        
        if threats:
            # Log threat
            threat_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "user_id": user_id,
                "ip_address": ip_address,
                "threats": threats,
                "request_data": request_data
            }
            
            # Store in Redis for analysis
            threat_key = f"threat:{datetime.utcnow().strftime('%Y%m%d')}:{ip_address}"
            self.redis.rpush(threat_key, json.dumps(threat_data))
            self.redis.expire(threat_key, 86400 * 7)  # Keep for 7 days
            
            # Check if IP should be blocked
            if await self._should_block_ip(ip_address):
                await self._block_ip(ip_address)
            
            return threat_data
        
        return None
    
    async def _should_block_ip(self, ip_address: str) -> bool:
        """Check if IP has too many threats"""
        threat_count = 0
        
        # Count threats in last hour
        for i in range(60):
            time_key = (datetime.utcnow() - timedelta(minutes=i)).strftime('%Y%m%d%H%M')
            key = f"threat:{time_key}:{ip_address}"
            threat_count += self.redis.llen(key)
        
        return threat_count > 10  # Block after 10 threats in an hour
    
    async def _block_ip(self, ip_address: str):
        """Block IP address"""
        self.redis.setex(
            f"blocked_ip:{ip_address}",
            3600,  # Block for 1 hour
            json.dumps({
                "blocked_at": datetime.utcnow().isoformat(),
                "reason": "Too many security threats detected"
            })
        )
```

## 9. Incident Response

### 9.1 Incident Response Plan

```python
# backend/app/services/incident_response.py
from enum import Enum
from typing import Dict, Any, List
import asyncio

class IncidentSeverity(Enum):
    CRITICAL = "critical"  # Data breach, system compromise
    HIGH = "high"        # Multiple failed auth attempts, suspicious activity
    MEDIUM = "medium"    # Single security event
    LOW = "low"          # Informational

class IncidentResponse:
    def __init__(self, notification_service, security_logger):
        self.notification_service = notification_service
        self.security_logger = security_logger
        self.response_plans = self._load_response_plans()
    
    def _load_response_plans(self) -> Dict[str, Dict[str, Any]]:
        return {
            "data_breach": {
                "severity": IncidentSeverity.CRITICAL,
                "steps": [
                    "isolate_affected_systems",
                    "preserve_evidence",
                    "notify_security_team",
                    "notify_dpo",  # Data Protection Officer
                    "assess_scope",
                    "contain_breach",
                    "notify_authorities",  # Within 72 hours for GDPR
                    "notify_affected_users"
                ],
                "notifications": ["security_team", "ciso", "legal", "dpo"]
            },
            "account_compromise": {
                "severity": IncidentSeverity.HIGH,
                "steps": [
                    "disable_account",
                    "revoke_all_sessions",
                    "force_password_reset",
                    "audit_recent_activity",
                    "notify_user",
                    "check_related_accounts"
                ],
                "notifications": ["security_team", "affected_user"]
            },
            "brute_force_attack": {
                "severity": IncidentSeverity.HIGH,
                "steps": [
                    "block_source_ip",
                    "increase_monitoring",
                    "check_affected_accounts",
                    "implement_additional_rate_limiting"
                ],
                "notifications": ["security_team"]
            }
        }
    
    async def handle_incident(
        self,
        incident_type: str,
        details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle security incident"""
        plan = self.response_plans.get(incident_type)
        if not plan:
            raise ValueError(f"Unknown incident type: {incident_type}")
        
        incident_id = str(uuid.uuid4())
        
        # Log incident
        self.security_logger.log_incident(
            incident_id=incident_id,
            incident_type=incident_type,
            severity=plan["severity"].value,
            details=details
        )
        
        # Execute response steps
        results = {}
        for step in plan["steps"]:
            method = getattr(self, f"_{step}", None)
            if method:
                try:
                    result = await method(details)
                    results[step] = {"status": "completed", "result": result}
                except Exception as e:
                    results[step] = {"status": "failed", "error": str(e)}
            else:
                results[step] = {"status": "skipped", "reason": "Not implemented"}
        
        # Send notifications
        await self._send_notifications(
            plan["notifications"],
            incident_id,
            incident_type,
            plan["severity"],
            details
        )
        
        return {
            "incident_id": incident_id,
            "type": incident_type,
            "severity": plan["severity"].value,
            "response_results": results,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _isolate_affected_systems(self, details: Dict[str, Any]):
        """Isolate affected systems"""
        # Implementation depends on infrastructure
        # Example: Update firewall rules, disable services
        pass
    
    async def _disable_account(self, details: Dict[str, Any]):
        """Disable compromised account"""
        user_id = details.get("user_id")
        if user_id:
            # Disable account in database
            # Revoke all tokens
            # Log action
            pass
    
    async def _block_source_ip(self, details: Dict[str, Any]):
        """Block attacking IP"""
        ip_address = details.get("ip_address")
        if ip_address:
            # Add to firewall blacklist
            # Update application blacklist
            pass
```

## 10. Security Headers & CSP

### 10.1 Security Headers Configuration

```python
# backend/app/middleware/security_headers.py
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), camera=(), geolocation=(), "
            "gyroscope=(), magnetometer=(), microphone=(), "
            "payment=(), usb=()"
        )
        
        # HSTS (only for HTTPS)
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )
        
        # CSP
        response.headers["Content-Security-Policy"] = self._get_csp()
        
        return response
    
    def _get_csp(self) -> str:
        """Generate Content Security Policy"""
        directives = {
            "default-src": ["'self'"],
            "script-src": [
                "'self'",
                "'unsafe-inline'",  # Required for React in dev
                "https://www.youtube.com",
                "https://s.ytimg.com"
            ],
            "style-src": [
                "'self'",
                "'unsafe-inline'",  # Required for styled-components
                "https://fonts.googleapis.com"
            ],
            "img-src": [
                "'self'",
                "data:",
                "https:",
                "blob:"
            ],
            "font-src": [
                "'self'",
                "https://fonts.gstatic.com"
            ],
            "connect-src": [
                "'self'",
                "https://api.cybersec-platform.de",
                "wss://api.cybersec-platform.de"
            ],
            "frame-src": [
                "https://www.youtube.com"
            ],
            "frame-ancestors": ["'none'"],
            "form-action": ["'self'"],
            "base-uri": ["'self'"],
            "object-src": ["'none'"],
            "upgrade-insecure-requests": []
        }
        
        return "; ".join(
            f"{key} {' '.join(values)}" if values else key
            for key, values in directives.items()
        )
```

## 11. GDPR Compliance

### 11.1 Data Privacy Service

```python
# backend/app/services/gdpr_service.py
from typing import Dict, Any, List
import zipfile
import json

class GDPRService:
    def __init__(self, db: Session):
        self.db = db
    
    async def export_user_data(self, user_id: str) -> bytes:
        """Export all user data for GDPR data portability"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
        
        export_data = {
            "user_profile": {
                "id": str(user.id),
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role,
                "department": user.department,
                "created_at": user.created_at.isoformat(),
                "last_login": user.last_login_at.isoformat() if user.last_login_at else None
            },
            "course_progress": [],
            "phishing_results": [],
            "certificates": []
        }
        
        # Get course progress
        progress_records = self.db.query(UserCourseProgress).filter(
            UserCourseProgress.user_id == user_id
        ).all()
        
        for progress in progress_records:
            export_data["course_progress"].append({
                "course_id": str(progress.course_id),
                "course_title": progress.course.title,
                "status": progress.status,
                "started_at": progress.started_at.isoformat() if progress.started_at else None,
                "completed_at": progress.completed_at.isoformat() if progress.completed_at else None,
                "quiz_score": progress.quiz_score
            })
        
        # Create ZIP file with JSON data
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr(
                'user_data.json',
                json.dumps(export_data, indent=2)
            )
        
        return zip_buffer.getvalue()
    
    async def delete_user_data(self, user_id: str, reason: str) -> Dict[str, Any]:
        """Delete user data for GDPR right to erasure"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
        
        # Log deletion request
        deletion_log = DataDeletionLog(
            user_id=user_id,
            user_email=user.email,
            reason=reason,
            requested_at=datetime.utcnow()
        )
        self.db.add(deletion_log)
        
        # Anonymize rather than delete for audit trail
        anonymized_email = f"deleted_{hashlib.sha256(user.email.encode()).hexdigest()[:8]}@example.com"
        
        user.email = anonymized_email
        user.first_name = "DELETED"
        user.last_name = "USER"
        user.is_active = False
        user.hashed_password = "DELETED"
        user.deleted_at = datetime.utcnow()
        
        # Delete related personal data
        self.db.query(PhishingResult).filter(
            PhishingResult.user_id == user_id
        ).update({"ip_addresses": [], "user_agents": []})
        
        self.db.commit()
        
        return {
            "user_id": user_id,
            "status": "deleted",
            "deletion_log_id": str(deletion_log.id),
            "timestamp": deletion_log.requested_at.isoformat()
        }
    
    async def get_consent_status(self, user_id: str) -> Dict[str, Any]:
        """Get user's consent status"""
        consents = self.db.query(UserConsent).filter(
            UserConsent.user_id == user_id,
            UserConsent.is_active == True
        ).all()
        
        return {
            consent.consent_type: {
                "granted": consent.granted,
                "granted_at": consent.granted_at.isoformat() if consent.granted_at else None,
                "expires_at": consent.expires_at.isoformat() if consent.expires_at else None
            }
            for consent in consents
        }
    
    async def update_consent(
        self,
        user_id: str,
        consent_type: str,
        granted: bool,
        ip_address: str
    ) -> Dict[str, Any]:
        """Update user consent"""
        # Deactivate old consent
        self.db.query(UserConsent).filter(
            UserConsent.user_id == user_id,
            UserConsent.consent_type == consent_type,
            UserConsent.is_active == True
        ).update({"is_active": False})
        
        # Create new consent record
        consent = UserConsent(
            user_id=user_id,
            consent_type=consent_type,
            granted=granted,
            granted_at=datetime.utcnow() if granted else None,
            ip_address=ip_address,
            is_active=True
        )
        self.db.add(consent)
        self.db.commit()
        
        return {
            "consent_type": consent_type,
            "granted": granted,
            "timestamp": datetime.utcnow().isoformat()
        }
```

## 12. Security Testing

### 12.1 Security Test Suite

```python
# tests/security/test_authentication.py
import pytest
from jose import jwt
import time

class TestAuthenticationSecurity:
    def test_password_hashing_uses_bcrypt(self):
        """Ensure passwords are properly hashed"""
        from app.core.security import get_password_hash
        
        password = "TestPassword123!"
        hashed = get_password_hash(password)
        
        # Check it's a bcrypt hash
        assert hashed.startswith("$2b$")
        assert len(hashed) == 60
        
        # Ensure different hashes for same password
        hashed2 = get_password_hash(password)
        assert hashed != hashed2
    
    def test_jwt_token_contains_required_claims(self, client):
        """Test JWT token structure"""
        response = client.post("/api/v1/auth/login", data={
            "username": "test@example.com",
            "password": "testpassword"
        })
        
        token = response.json()["access_token"]
        payload = jwt.decode(token, options={"verify_signature": False})
        
        # Check required claims
        required_claims = ["sub", "email", "company_id", "role", "exp", "iat", "jti"]
        for claim in required_claims:
            assert claim in payload
        
        # Check expiration
        assert payload["exp"] > time.time()
    
    def test_session_fixation_prevention(self, client):
        """Test that session ID changes after login"""
        # Get initial session
        response1 = client.get("/api/v1/health")
        session1 = response1.cookies.get("session")
        
        # Login
        response2 = client.post("/api/v1/auth/login", data={
            "username": "test@example.com",
            "password": "testpassword"
        })
        session2 = response2.cookies.get("session")
        
        # Session should be different
        assert session1 != session2
```

### 12.2 Penetration Testing Checklist

```markdown
## Penetration Testing Checklist

### Authentication & Session Management
- [ ] Test for default credentials
- [ ] Test password strength requirements
- [ ] Test account lockout mechanism
- [ ] Test session timeout
- [ ] Test concurrent session handling
- [ ] Test JWT token security
- [ ] Test password reset process
- [ ] Test 2FA bypass attempts

### Authorization
- [ ] Test horizontal privilege escalation
- [ ] Test vertical privilege escalation
- [ ] Test direct object references
- [ ] Test missing function level access control

### Input Validation
- [ ] Test for SQL injection
- [ ] Test for NoSQL injection
- [ ] Test for LDAP injection
- [ ] Test for XSS (reflected, stored, DOM-based)
- [ ] Test for XXE injection
- [ ] Test for command injection
- [ ] Test for directory traversal
- [ ] Test for file upload vulnerabilities

### API Security
- [ ] Test rate limiting
- [ ] Test API versioning
- [ ] Test CORS configuration
- [ ] Test HTTP methods
- [ ] Test content-type validation

### Cryptography
- [ ] Test SSL/TLS configuration
- [ ] Test certificate validation
- [ ] Test encryption at rest
- [ ] Test key management

### Business Logic
- [ ] Test workflow bypass
- [ ] Test price manipulation
- [ ] Test race conditions
- [ ] Test time-based attacks

### Infrastructure
- [ ] Test for open ports
- [ ] Test for outdated software
- [ ] Test container security
- [ ] Test cloud misconfigurations
```

Diese umfassende Security-Spezifikation stellt sicher, dass die Cybersecurity Awareness Platform nach höchsten Sicherheitsstandards entwickelt und betrieben wird.