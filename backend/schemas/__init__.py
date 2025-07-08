"""Schemas package."""

from .user import (
    UserCreate, UserUpdate, UserResponse, UserInDB,
    PasswordChange, TokenResponse, LoginRequest
)
from .company import (
    CompanyCreate, CompanyUpdate, CompanyResponse, CompanyInDB
)
from .course import (
    CourseCreate, CourseUpdate, CourseResponse,
    ModuleCreate, ModuleUpdate, ModuleResponse,
    LessonCreate, LessonUpdate, LessonResponse,
    ContentCreate, ContentUpdate, ContentResponse,
    EnrollmentCreate, EnrollmentResponse,
    QuizCreate, QuizUpdate, QuizResponse,
    QuizQuestionCreate, QuizQuestionResponse,
    QuizAttemptCreate, QuizAttemptResponse,
    QuizAnswerCreate
)
from .analytics import (
    AnalyticsEventCreate, AnalyticsEventResponse,
    DashboardMetrics, CourseAnalyticsResponse,
    UserEngagementResponse, RevenueAnalyticsResponse,
    PhishingAnalyticsResponse, RealtimeMetricResponse,
    AnalyticsExportRequest, AnalyticsDateRange
)

__all__ = [
    # User schemas
    "UserCreate", "UserUpdate", "UserResponse", "UserInDB",
    "PasswordChange", "TokenResponse", "LoginRequest",
    
    # Company schemas
    "CompanyCreate", "CompanyUpdate", "CompanyResponse", "CompanyInDB",
    
    # Course schemas
    "CourseCreate", "CourseUpdate", "CourseResponse",
    "ModuleCreate", "ModuleUpdate", "ModuleResponse",
    "LessonCreate", "LessonUpdate", "LessonResponse",
    "ContentCreate", "ContentUpdate", "ContentResponse",
    "EnrollmentCreate", "EnrollmentResponse",
    "QuizCreate", "QuizUpdate", "QuizResponse",
    "QuizQuestionCreate", "QuizQuestionResponse",
    "QuizAttemptCreate", "QuizAttemptResponse",
    "QuizAnswerCreate",
    
    # Analytics schemas
    "AnalyticsEventCreate", "AnalyticsEventResponse",
    "DashboardMetrics", "CourseAnalyticsResponse",
    "UserEngagementResponse", "RevenueAnalyticsResponse",
    "PhishingAnalyticsResponse", "RealtimeMetricResponse",
    "AnalyticsExportRequest", "AnalyticsDateRange"
]