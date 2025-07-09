"""Application configuration using pydantic-settings."""

import secrets
from datetime import timedelta
from typing import Any, List, Optional, Union

from pydantic import AnyHttpUrl, EmailStr, Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with automatic environment variable loading."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )
    
    # Application Settings
    APP_NAME: str = "Cybersecurity Awareness Platform"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development", pattern="^(development|staging|production|test)$")
    DEBUG: bool = Field(default=False)
    
    # Server Settings
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)
    WORKERS: int = Field(default=4)
    LOG_LEVEL: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    
    # Security Settings
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)
    
    # Password Policy
    PASSWORD_MIN_LENGTH: int = Field(default=8)
    PASSWORD_REQUIRE_UPPERCASE: bool = Field(default=True)
    PASSWORD_REQUIRE_LOWERCASE: bool = Field(default=True)
    PASSWORD_REQUIRE_DIGIT: bool = Field(default=True)
    PASSWORD_REQUIRE_SPECIAL: bool = Field(default=True)
    
    # Two-Factor Authentication
    OTP_ISSUER: str = Field(default="Cybersecurity Awareness Platform")
    OTP_VALIDITY_SECONDS: int = Field(default=30)
    OTP_BACKUP_CODES_COUNT: int = Field(default=10)
    
    # Database Settings
    DATABASE_URL: Optional[PostgresDsn] = Field(default=None)
    DATABASE_POOL_SIZE: int = Field(default=10)
    DATABASE_MAX_OVERFLOW: int = Field(default=20)
    DATABASE_POOL_TIMEOUT: int = Field(default=30)
    DATABASE_POOL_RECYCLE: int = Field(default=1800)
    
    # Redis Settings
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    REDIS_PASSWORD: Optional[str] = Field(default=None)
    REDIS_POOL_SIZE: int = Field(default=10)
    REDIS_DECODE_RESPONSES: bool = Field(default=True)
    
    # CORS Settings
    CORS_ORIGINS: List[AnyHttpUrl] = Field(default=["http://localhost:3000"])
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True)
    CORS_ALLOW_METHODS: List[str] = Field(default=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
    CORS_ALLOW_HEADERS: List[str] = Field(default=["*"])
    
    # Email Settings
    SMTP_HOST: str = Field(default="localhost")
    SMTP_PORT: int = Field(default=587)
    SMTP_USER: Optional[str] = Field(default=None)
    SMTP_PASSWORD: Optional[str] = Field(default=None)
    SMTP_TLS: bool = Field(default=True)
    SMTP_SSL: bool = Field(default=False)
    SMTP_TIMEOUT: int = Field(default=30)
    EMAIL_FROM_NAME: str = Field(default="Cybersecurity Awareness Platform")
    EMAIL_FROM_EMAIL: EmailStr = Field(default="noreply@example.com")
    
    # Frontend Settings
    FRONTEND_URL: AnyHttpUrl = Field(default="http://localhost:3000")
    
    # Monitoring Settings
    SENTRY_DSN: Optional[str] = Field(default=None)
    SENTRY_ENVIRONMENT: Optional[str] = Field(default=None)
    SENTRY_TRACES_SAMPLE_RATE: float = Field(default=0.1, ge=0.0, le=1.0)
    PROMETHEUS_ENABLED: bool = Field(default=True)
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = Field(default=True)
    RATE_LIMIT_REQUESTS: int = Field(default=100)
    RATE_LIMIT_PERIOD: int = Field(default=60)  # seconds
    RATE_LIMIT_STORAGE_URL: Optional[str] = Field(default=None)
    
    # File Upload Settings
    MAX_UPLOAD_SIZE: int = Field(default=10 * 1024 * 1024)  # 10MB
    ALLOWED_UPLOAD_EXTENSIONS: List[str] = Field(default=[".pdf", ".png", ".jpg", ".jpeg"])
    
    # Stripe Settings
    STRIPE_SECRET_KEY: Optional[str] = Field(default=None)
    STRIPE_WEBHOOK_SECRET: Optional[str] = Field(default=None)
    STRIPE_PUBLISHABLE_KEY: Optional[str] = Field(default=None)
    
    # AWS Settings
    AWS_ACCESS_KEY_ID: Optional[str] = Field(default=None)
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(default=None)
    AWS_REGION: str = Field(default="eu-central-1")
    AWS_S3_BUCKET: Optional[str] = Field(default=None)
    AWS_S3_CUSTOM_DOMAIN: Optional[str] = Field(default=None)
    
    # Celery Settings
    CELERY_BROKER_URL: Optional[str] = Field(default=None)
    CELERY_RESULT_BACKEND: Optional[str] = Field(default=None)
    CELERY_TASK_ALWAYS_EAGER: bool = Field(default=False)
    CELERY_TASK_EAGER_PROPAGATES: bool = Field(default=True)
    
    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], values: dict) -> Any:
        if isinstance(v, str):
            return v
        return None
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    @field_validator("SENTRY_ENVIRONMENT", mode="before")
    @classmethod
    def set_sentry_environment(cls, v: Optional[str], info) -> str:
        if v is None:
            return info.data.get("ENVIRONMENT", "development")
        return v
    
    @field_validator("RATE_LIMIT_STORAGE_URL", mode="before")
    @classmethod
    def set_rate_limit_storage(cls, v: Optional[str], info) -> Optional[str]:
        if v is None:
            return info.data.get("REDIS_URL")
        return v
    
    @field_validator("CELERY_BROKER_URL", mode="before")
    @classmethod
    def set_celery_broker(cls, v: Optional[str], info) -> Optional[str]:
        if v is None:
            return info.data.get("REDIS_URL")
        return v
    
    @field_validator("CELERY_RESULT_BACKEND", mode="before")
    @classmethod
    def set_celery_backend(cls, v: Optional[str], info) -> Optional[str]:
        if v is None:
            return info.data.get("REDIS_URL")
        return v
    
    @property
    def access_token_expire_timedelta(self) -> timedelta:
        """Get access token expiration as timedelta."""
        return timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    @property
    def refresh_token_expire_timedelta(self) -> timedelta:
        """Get refresh token expiration as timedelta."""
        return timedelta(days=self.REFRESH_TOKEN_EXPIRE_DAYS)
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT == "development"


# Create global settings instance
settings = Settings()