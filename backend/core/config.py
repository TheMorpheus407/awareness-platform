"""Application configuration using Pydantic settings."""

from typing import List, Optional, Union
from pathlib import Path

from pydantic import AnyHttpUrl, EmailStr, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )
    
    # Application Settings
    APP_NAME: str = "Cybersecurity Awareness Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    LOG_LEVEL: str = "INFO"
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database
    DATABASE_URL: PostgresDsn
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 0
    
    # CORS Settings
    CORS_ORIGINS: List[AnyHttpUrl] = []
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
    CORS_ALLOW_HEADERS: List[str] = ["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"]
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Email Configuration
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: Optional[EmailStr] = None
    SMTP_FROM_NAME: Optional[str] = None
    SUPPORT_EMAIL: Optional[EmailStr] = None
    
    # Sentry (Error Tracking)
    SENTRY_DSN: Optional[str] = None
    
    # Redis (Optional - for caching/sessions)
    REDIS_URL: Optional[str] = None
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # External APIs
    YOUTUBE_API_KEY: Optional[str] = None
    
    # AWS Configuration (for S3)
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: Optional[str] = "us-east-1"
    AWS_S3_BUCKET: Optional[str] = None
    
    # Stripe Configuration
    STRIPE_SECRET_KEY: str
    STRIPE_PUBLISHABLE_KEY: str
    STRIPE_WEBHOOK_SECRET: str
    STRIPE_SUCCESS_URL: Optional[str] = None
    STRIPE_CANCEL_URL: Optional[str] = None
    
    # Frontend URL
    FRONTEND_URL: AnyHttpUrl
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    # Project directories
    @property
    def BASE_DIR(self) -> Path:
        return Path(__file__).parent.parent
    
    @property
    def STATIC_DIR(self) -> Path:
        return self.BASE_DIR / "static"
    
    @property
    def TEMPLATES_DIR(self) -> Path:
        return self.BASE_DIR / "templates"
    
    @property
    def UPLOAD_DIR(self) -> Path:
        return self.BASE_DIR / "uploads"


settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings