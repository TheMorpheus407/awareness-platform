# Backend Spezifikation - Cybersecurity Awareness Platform API
**Version 1.0 | Python FastAPI Application**

## 1. Technologie-Stack

### 1.1 Core Dependencies
```toml
# pyproject.toml
[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.109.0"
uvicorn = "^0.25.0"
pydantic = "^2.5.0"
sqlalchemy = "^2.0.0"
alembic = "^1.13.0"
psycopg2-binary = "^2.9.0"
python-jose = "^3.3.0"
passlib = "^1.7.4"
python-multipart = "^0.0.6"
celery = "^5.3.0"
redis = "^5.0.0"
httpx = "^0.25.0"
boto3 = "^1.34.0"
reportlab = "^4.0.0"
jinja2 = "^3.1.0"
python-dateutil = "^2.8.0"
pytz = "^2023.3"
```

### 1.2 Development Dependencies
```toml
[tool.poetry.dev-dependencies]
pytest = "^7.4.0"
pytest-asyncio = "^0.21.0"
pytest-cov = "^4.1.0"
black = "^23.12.0"
ruff = "^0.1.0"
mypy = "^1.8.0"
pre-commit = "^3.6.0"
```

## 2. Projektstruktur

```
app/
├── api/
│   ├── v1/
│   │   ├── endpoints/
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   ├── companies.py
│   │   │   ├── courses.py
│   │   │   ├── phishing.py
│   │   │   ├── reports.py
│   │   │   └── admin.py
│   │   └── router.py
│   └── dependencies.py
│
├── core/
│   ├── config.py
│   ├── security.py
│   ├── database.py
│   └── exceptions.py
│
├── models/
│   ├── base.py
│   ├── company.py
│   ├── user.py
│   ├── course.py
│   ├── phishing.py
│   └── audit.py
│
├── schemas/
│   ├── auth.py
│   ├── user.py
│   ├── course.py
│   ├── phishing.py
│   └── report.py
│
├── services/
│   ├── auth_service.py
│   ├── user_service.py
│   ├── course_service.py
│   ├── phishing_service.py
│   ├── report_service.py
│   ├── email_service.py
│   └── compliance_service.py
│
├── tasks/
│   ├── celery_app.py
│   ├── email_tasks.py
│   ├── report_tasks.py
│   └── phishing_tasks.py
│
├── utils/
│   ├── validators.py
│   ├── formatters.py
│   ├── pdf_generator.py
│   └── youtube_api.py
│
├── migrations/
│   └── alembic/
│
├── templates/
│   ├── emails/
│   └── reports/
│
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_courses.py
│   └── test_phishing.py
│
├── main.py
└── __init__.py
```

## 3. Core Configuration

### 3.1 Settings (core/config.py)
```python
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "CyberSec Awareness Platform"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # API
    API_V1_STR: str = "/api/v1"
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    
    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 40
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # Email
    SMTP_HOST: str
    SMTP_PORT: int = 587
    SMTP_USER: str
    SMTP_PASSWORD: str
    EMAIL_FROM: str = "noreply@cybersec-platform.de"
    
    # YouTube
    YOUTUBE_API_KEY: str
    
    # Storage
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    S3_BUCKET_NAME: Optional[str] = None
    
    class Config:
        env_file = ".env"

settings = Settings()
```

## 4. Database Models

### 4.1 Base Model
```python
# models/base.py
from sqlalchemy import Column, DateTime, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from uuid import uuid4

Base = declarative_base()

class BaseModel(Base):
    __abstract__ = True
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

### 4.2 Company Model
```python
# models/company.py
from sqlalchemy import Column, String, Integer, JSON, Enum
from .base import BaseModel
import enum

class CompanySize(enum.Enum):
    SMALL = "small"  # < 50
    MEDIUM = "medium"  # 50-250
    LARGE = "large"  # 250-1000
    ENTERPRISE = "enterprise"  # > 1000

class Company(BaseModel):
    __tablename__ = "companies"
    
    name = Column(String, nullable=False)
    domain = Column(String, unique=True, nullable=False)
    industry = Column(String)
    size = Column(Enum(CompanySize))
    
    # Compliance Profile
    compliance_requirements = Column(JSON, default=list)
    # ["nis2", "dsgvo", "iso27001", "tisax", "bait"]
    
    # Settings
    settings = Column(JSON, default=dict)
    # {
    #   "phishing_frequency": "monthly",
    #   "reminder_days": [3, 7, 14],
    #   "auto_assign_courses": true,
    #   "language": "de"
    # }
    
    # Subscription
    subscription_tier = Column(String, default="trial")
    subscription_valid_until = Column(DateTime)
    
    # Relationships
    users = relationship("User", back_populates="company")
    courses = relationship("CompanyCourse", back_populates="company")
    phishing_campaigns = relationship("PhishingCampaign", back_populates="company")
```

### 4.3 User Model
```python
# models/user.py
from sqlalchemy import Column, String, Boolean, ForeignKey, Float, Enum
from sqlalchemy.orm import relationship
from .base import BaseModel
import enum

class UserRole(enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    EMPLOYEE = "employee"

class User(BaseModel):
    __tablename__ = "users"
    
    # Authentication
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Profile
    first_name = Column(String)
    last_name = Column(String)
    role = Column(Enum(UserRole), default=UserRole.EMPLOYEE)
    department = Column(String)
    
    # Company
    company_id = Column(String, ForeignKey("companies.id"))
    company = relationship("Company", back_populates="users")
    
    # Security Metrics
    risk_score = Column(Float, default=0.0)  # 0-100
    last_training_date = Column(DateTime)
    phishing_click_rate = Column(Float, default=0.0)
    
    # 2FA
    totp_secret = Column(String)
    totp_enabled = Column(Boolean, default=False)
    
    # Relationships
    course_progress = relationship("UserCourseProgress", back_populates="user")
    phishing_results = relationship("PhishingResult", back_populates="user")
```

### 4.4 Course Model
```python
# models/course.py
from sqlalchemy import Column, String, Integer, JSON, Boolean, Text
from .base import BaseModel

class Course(BaseModel):
    __tablename__ = "courses"
    
    title = Column(String, nullable=False)
    description = Column(Text)
    duration_minutes = Column(Integer, default=10)
    difficulty = Column(String)  # "beginner", "intermediate", "advanced"
    
    # Content
    youtube_video_id = Column(String)
    content_markdown = Column(Text)
    
    # Quiz
    quiz_questions = Column(JSON)
    # [{
    #   "id": "q1",
    #   "question": "Was ist Phishing?",
    #   "options": ["A", "B", "C", "D"],
    #   "correct_answer": "B",
    #   "explanation": "..."
    # }]
    
    passing_score = Column(Integer, default=80)
    
    # Metadata
    tags = Column(JSON, default=list)
    compliance_tags = Column(JSON, default=list)
    target_roles = Column(JSON, default=list)
    
    # Localization
    available_languages = Column(JSON, default=["de"])
    
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user_progress = relationship("UserCourseProgress", back_populates="course")
```

### 4.5 Phishing Models
```python
# models/phishing.py
from sqlalchemy import Column, String, ForeignKey, Boolean, DateTime, JSON, Enum
from sqlalchemy.orm import relationship
from .base import BaseModel
import enum

class CampaignStatus(enum.Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"

class PhishingTemplate(BaseModel):
    __tablename__ = "phishing_templates"
    
    name = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    sender_name = Column(String)
    sender_email = Column(String)
    html_content = Column(Text)
    difficulty = Column(String)  # "easy", "medium", "hard"
    category = Column(String)  # "credential", "attachment", "link"
    
    # Indicators to highlight in training
    red_flags = Column(JSON, default=list)

class PhishingCampaign(BaseModel):
    __tablename__ = "phishing_campaigns"
    
    name = Column(String, nullable=False)
    company_id = Column(String, ForeignKey("companies.id"))
    template_id = Column(String, ForeignKey("phishing_templates.id"))
    
    status = Column(Enum(CampaignStatus), default=CampaignStatus.DRAFT)
    scheduled_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Target Configuration
    target_groups = Column(JSON, default=list)  # ["all", "department:IT", "role:manager"]
    excluded_users = Column(JSON, default=list)
    
    # Settings
    landing_page_url = Column(String)
    track_duration_days = Column(Integer, default=7)
    
    # Relationships
    company = relationship("Company", back_populates="phishing_campaigns")
    template = relationship("PhishingTemplate")
    results = relationship("PhishingResult", back_populates="campaign")

class PhishingResult(BaseModel):
    __tablename__ = "phishing_results"
    
    campaign_id = Column(String, ForeignKey("phishing_campaigns.id"))
    user_id = Column(String, ForeignKey("users.id"))
    
    # Tracking
    email_sent_at = Column(DateTime)
    email_opened_at = Column(DateTime)
    link_clicked_at = Column(DateTime)
    data_submitted_at = Column(DateTime)
    reported_at = Column(DateTime)
    
    # Additional Data
    ip_address = Column(String)
    user_agent = Column(String)
    
    # Training
    training_completed = Column(Boolean, default=False)
    training_completed_at = Column(DateTime)
    
    # Relationships
    campaign = relationship("PhishingCampaign", back_populates="results")
    user = relationship("User", back_populates="phishing_results")
```

## 5. API Endpoints

### 5.1 Authentication Endpoints
```python
# api/v1/endpoints/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

router = APIRouter()

@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/register", response_model=UserResponse)
async def register(
    register_data: UserRegister,
    db: Session = Depends(get_db)
):
    """
    Register new company and admin user
    """
    # Check if company domain already exists
    # Create company
    # Create admin user
    # Send verification email
    pass

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token
    """
    pass

@router.post("/verify-email/{token}")
async def verify_email(token: str, db: Session = Depends(get_db)):
    """
    Verify user email address
    """
    pass

@router.post("/forgot-password")
async def forgot_password(
    email: EmailStr,
    db: Session = Depends(get_db)
):
    """
    Send password reset email
    """
    pass

@router.post("/reset-password")
async def reset_password(
    token: str,
    new_password: str,
    db: Session = Depends(get_db)
):
    """
    Reset password using token
    """
    pass
```

### 5.2 User Management Endpoints
```python
# api/v1/endpoints/users.py
@router.get("/", response_model=List[UserResponse])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    department: Optional[str] = None,
    role: Optional[UserRole] = None,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get all users in company with filtering
    """
    pass

@router.post("/bulk", response_model=BulkUserResponse)
async def create_bulk_users(
    file: UploadFile = File(...),
    send_invites: bool = True,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Bulk create users from CSV file
    Expected columns: email, first_name, last_name, department, role
    """
    pass

@router.get("/me", response_model=UserDetailResponse)
async def get_current_user_details(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user details including progress and risk score
    """
    pass

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Update user information
    """
    pass

@router.delete("/{user_id}")
async def deactivate_user(
    user_id: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Deactivate user (soft delete)
    """
    pass
```

### 5.3 Course Endpoints
```python
# api/v1/endpoints/courses.py
@router.get("/", response_model=List[CourseResponse])
async def get_available_courses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all available courses for current user based on role and compliance
    """
    pass

@router.get("/assigned", response_model=List[AssignedCourseResponse])
async def get_assigned_courses(
    status: Optional[str] = None,  # "pending", "in_progress", "completed"
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get courses assigned to current user
    """
    pass

@router.post("/{course_id}/start", response_model=CourseProgressResponse)
async def start_course(
    course_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Start a course and track progress
    """
    pass

@router.post("/{course_id}/progress", response_model=CourseProgressResponse)
async def update_progress(
    course_id: str,
    progress_data: ProgressUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update course progress (video watched percentage)
    """
    pass

@router.post("/{course_id}/quiz", response_model=QuizResultResponse)
async def submit_quiz(
    course_id: str,
    quiz_answers: List[QuizAnswer],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit quiz answers and get results
    """
    pass

@router.get("/{course_id}/certificate", response_model=CertificateResponse)
async def get_certificate(
    course_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get certificate for completed course
    """
    pass
```

### 5.4 Phishing Simulation Endpoints
```python
# api/v1/endpoints/phishing.py
@router.get("/templates", response_model=List[PhishingTemplateResponse])
async def get_phishing_templates(
    difficulty: Optional[str] = None,
    category: Optional[str] = None,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get available phishing templates
    """
    pass

@router.post("/campaigns", response_model=CampaignResponse)
async def create_campaign(
    campaign_data: CampaignCreate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Create new phishing campaign
    """
    pass

@router.get("/campaigns", response_model=List[CampaignResponse])
async def get_campaigns(
    status: Optional[CampaignStatus] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get all campaigns for company
    """
    pass

@router.post("/campaigns/{campaign_id}/launch")
async def launch_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Launch scheduled campaign immediately
    """
    pass

@router.get("/campaigns/{campaign_id}/results", response_model=CampaignResultsResponse)
async def get_campaign_results(
    campaign_id: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get detailed campaign results
    """
    pass

# Public endpoint for tracking
@router.get("/track/{tracking_id}")
async def track_click(
    tracking_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Track phishing link click (public endpoint)
    """
    pass

@router.post("/report/{tracking_id}")
async def report_phishing(
    tracking_id: str,
    db: Session = Depends(get_db)
):
    """
    Report email as phishing (positive action)
    """
    pass
```

### 5.5 Reporting Endpoints
```python
# api/v1/endpoints/reports.py
@router.get("/compliance/{report_type}", response_model=ComplianceReportResponse)
async def generate_compliance_report(
    report_type: str,  # "nis2", "dsgvo", "iso27001", etc.
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    format: str = "json",  # "json", "pdf", "csv"
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Generate compliance report
    """
    pass

@router.get("/dashboard/executive", response_model=ExecutiveDashboardResponse)
async def get_executive_dashboard(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get executive dashboard data
    """
    pass

@router.get("/analytics/risk-trends", response_model=RiskTrendsResponse)
async def get_risk_trends(
    timeframe: str = "monthly",  # "daily", "weekly", "monthly"
    months: int = 12,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get risk score trends over time
    """
    pass

@router.post("/export/audit-log")
async def export_audit_log(
    export_config: AuditLogExport,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Export audit log for compliance
    """
    pass
```

## 6. Background Tasks (Celery)

### 6.1 Celery Configuration
```python
# tasks/celery_app.py
from celery import Celery
from core.config import settings

celery_app = Celery(
    "cybersec_awareness",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "tasks.email_tasks",
        "tasks.report_tasks",
        "tasks.phishing_tasks"
    ]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Berlin",
    enable_utc=True,
    beat_schedule={
        "send-course-reminders": {
            "task": "tasks.email_tasks.send_course_reminders",
            "schedule": crontab(hour=9, minute=0),  # Daily at 9 AM
        },
        "check-phishing-campaigns": {
            "task": "tasks.phishing_tasks.check_scheduled_campaigns",
            "schedule": crontab(minute="*/15"),  # Every 15 minutes
        },
        "generate-weekly-reports": {
            "task": "tasks.report_tasks.generate_weekly_reports",
            "schedule": crontab(hour=6, minute=0, day_of_week=1),  # Monday 6 AM
        },
        "update-risk-scores": {
            "task": "tasks.report_tasks.update_risk_scores",
            "schedule": crontab(hour=2, minute=0),  # Daily at 2 AM
        },
    },
)
```

### 6.2 Email Tasks
```python
# tasks/email_tasks.py
@celery_app.task
def send_course_invitation(user_id: str, course_id: str):
    """Send course invitation email"""
    pass

@celery_app.task
def send_course_reminder(user_id: str, course_id: str, days_until_due: int):
    """Send course reminder email"""
    pass

@celery_app.task
def send_phishing_campaign_email(campaign_id: str, user_id: str):
    """Send individual phishing simulation email"""
    pass

@celery_app.task
def send_certificate_email(user_id: str, course_id: str, certificate_url: str):
    """Send certificate completion email"""
    pass
```

## 7. Security Implementation

### 7.1 JWT Token Management
```python
# core/security.py
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(subject: str, expires_delta: Optional[timedelta] = None):
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(token: str, token_type: str = "access"):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != token_type:
            return None
        return payload.get("sub")
    except JWTError:
        return None
```

### 7.2 Permission System
```python
# api/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    user_id = verify_token(token)
    if user_id is None:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    
    return user

async def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user
```

## 8. Services Layer

### 8.1 Compliance Service
```python
# services/compliance_service.py
class ComplianceService:
    def __init__(self, db: Session):
        self.db = db
    
    def check_nis2_compliance(self, company_id: str) -> ComplianceStatus:
        """
        Check if company meets NIS-2 requirements:
        - Management training completed
        - All employees trained within last year
        - Phishing tests conducted quarterly
        """
        pass
    
    def generate_dsgvo_report(self, company_id: str, date_range: DateRange) -> dict:
        """
        Generate DSGVO compliance report:
        - Training completion rates
        - Data handling awareness scores
        - Incident response training status
        """
        pass
    
    def calculate_compliance_score(self, company_id: str) -> float:
        """
        Calculate overall compliance score (0-100)
        """
        pass
```

### 8.2 Risk Calculation Service
```python
# services/risk_service.py
class RiskCalculationService:
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_user_risk_score(self, user_id: str) -> float:
        """
        Calculate individual risk score based on:
        - Phishing test performance (40%)
        - Training completion (30%)
        - Time since last training (20%)
        - Role risk factor (10%)
        """
        pass
    
    def calculate_department_risk(self, company_id: str, department: str) -> float:
        """
        Calculate average risk for department
        """
        pass
    
    def identify_high_risk_users(self, company_id: str, threshold: float = 70.0) -> List[User]:
        """
        Identify users with risk score above threshold
        """
        pass
```

## 9. YouTube Integration

### 9.1 YouTube API Service
```python
# utils/youtube_api.py
import httpx
from typing import Optional

class YouTubeService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.googleapis.com/youtube/v3"
    
    async def get_video_details(self, video_id: str) -> dict:
        """Get video duration and metadata"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/videos",
                params={
                    "id": video_id,
                    "part": "contentDetails,snippet",
                    "key": self.api_key
                }
            )
            return response.json()
    
    async def validate_video_availability(self, video_id: str) -> bool:
        """Check if video is available and embeddable"""
        pass
```

## 10. Testing

### 10.1 Test Configuration
```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    SessionLocal = sessionmaker(bind=connection)
    session = SessionLocal()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
```

### 10.2 Example Tests
```python
# tests/test_auth.py
def test_register_company(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "company_name": "Test Company",
            "company_domain": "test.com",
            "admin_email": "admin@test.com",
            "admin_password": "SecurePass123!",
            "admin_first_name": "Test",
            "admin_last_name": "Admin"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["company"]["domain"] == "test.com"
    assert data["user"]["email"] == "admin@test.com"

def test_login(client, test_user):
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user.email,
            "password": "testpass123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
```

## 11. Database Migrations

### 11.1 Alembic Setup
```python
# alembic.ini configuration
[alembic]
script_location = migrations
prepend_sys_path = .
sqlalchemy.url = postgresql://user:password@localhost/cybersec_db

# migrations/env.py
from app.models import Base
target_metadata = Base.metadata
```

### 11.2 Initial Migration
```bash
# Create initial migration
alembic revision --autogenerate -m "Initial schema"

# Apply migrations
alembic upgrade head
```

## 12. Deployment Configuration

### 12.1 Production Settings
```python
# Docker environment variables
DATABASE_URL=postgresql://user:password@db:5432/cybersec_db
REDIS_URL=redis://redis:6379/0
SECRET_KEY=your-production-secret-key
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=noreply@cybersec-platform.de
SMTP_PASSWORD=your-smtp-password
YOUTUBE_API_KEY=your-youtube-api-key
```

### 12.2 Gunicorn Configuration
```python
# gunicorn.conf.py
bind = "0.0.0.0:8000"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
max_requests = 1000
max_requests_jitter = 50
timeout = 120
keepalive = 5
accesslog = "-"
errorlog = "-"
loglevel = "info"
```

## 13. Monitoring and Logging

### 13.1 Structured Logging
```python
# core/logging.py
import logging
import json
from datetime import datetime

class StructuredFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        if hasattr(record, "user_id"):
            log_obj["user_id"] = record.user_id
        if hasattr(record, "company_id"):
            log_obj["company_id"] = record.company_id
        
        return json.dumps(log_obj)
```

### 13.2 Audit Logging
```python
# models/audit.py
class AuditLog(BaseModel):
    __tablename__ = "audit_logs"
    
    user_id = Column(String, ForeignKey("users.id"))
    company_id = Column(String, ForeignKey("companies.id"))
    action = Column(String, nullable=False)  # "login", "course_completed", etc.
    resource_type = Column(String)  # "course", "user", "report"
    resource_id = Column(String)
    ip_address = Column(String)
    user_agent = Column(String)
    metadata = Column(JSON)
```

## 14. API Documentation

### 14.1 OpenAPI Configuration
```python
# main.py
app = FastAPI(
    title="CyberSec Awareness Platform API",
    description="Comprehensive cybersecurity awareness training platform",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)
```

### 14.2 Response Models
```python
# schemas/base.py
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class BaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int
```

## 15. Performance Optimization

### 15.1 Database Optimization
- Connection pooling with SQLAlchemy
- Proper indexing on frequently queried columns
- Eager loading for relationships
- Query optimization with explain analyze

### 15.2 Caching Strategy
- Redis for session management
- Cache frequently accessed data (course lists, templates)
- Cache invalidation on updates
- Response caching for reports

### 15.3 API Rate Limiting
```python
# middleware/rate_limit.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Apply to endpoints
@router.get("/", dependencies=[Depends(RateLimiter(times=100, hours=1))])
```