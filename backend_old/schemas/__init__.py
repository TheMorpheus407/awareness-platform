"""Schemas package."""

from .user import (
    UserCreate, UserUpdate, UserResponse, UserInDB,
    UserLogin, Token, TokenPayload
)
from .company import (
    CompanyCreate, CompanyUpdate, CompanyResponse, CompanyInDB
)
from .course import (
    CourseCreate, CourseUpdate, CourseInDB as CourseResponse,
    ModuleCreate, ModuleUpdate, ModuleInDB as ModuleResponse,
    LessonCreate, LessonUpdate, LessonInDB as LessonResponse,
    CourseContentCreate as ContentCreate, CourseContentUpdate as ContentUpdate, CourseContentInDB as ContentResponse,
    CourseEnrollmentCreate as EnrollmentCreate, CourseEnrollmentInDB as EnrollmentResponse,
    QuizCreate, QuizUpdate, QuizInDB as QuizResponse,
    QuizQuestionCreate, QuizQuestionInDB as QuizQuestionResponse,
    QuizAttemptCreate, QuizAttemptResult as QuizAttemptResponse,
    QuizAnswerSubmit as QuizAnswerCreate
)
from .analytics import (
    AnalyticsEventCreate, AnalyticsEventResponse,
    DashboardMetrics, CourseAnalyticsResponse,
    UserEngagementResponse, RevenueAnalyticsResponse,
    PhishingAnalyticsResponse, RealtimeMetricResponse,
    AnalyticsExportRequest, AnalyticsDateRange
)
from .phishing import (
    CampaignStatus, TemplateDifficulty, TemplateCategory,
    PhishingTemplateCreate, PhishingTemplateUpdate, PhishingTemplateResponse,
    PhishingCampaignCreate, PhishingCampaignUpdate, PhishingCampaignResponse,
    PhishingResultCreate, PhishingResultUpdate, PhishingResultResponse,
    PhishingTrackingEvent, PhishingReportRequest,
    CampaignAnalytics, ComplianceReport, TemplateLibraryFilter,
    CampaignTargetGroup, CampaignSettings
)

__all__ = [
    # User schemas
    "UserCreate", "UserUpdate", "UserResponse", "UserInDB",
    "UserLogin", "Token", "TokenPayload",
    
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
    "AnalyticsExportRequest", "AnalyticsDateRange",
    
    # Phishing schemas
    "CampaignStatus", "TemplateDifficulty", "TemplateCategory",
    "PhishingTemplateCreate", "PhishingTemplateUpdate", "PhishingTemplateResponse",
    "PhishingCampaignCreate", "PhishingCampaignUpdate", "PhishingCampaignResponse",
    "PhishingResultCreate", "PhishingResultUpdate", "PhishingResultResponse",
    "PhishingTrackingEvent", "PhishingReportRequest",
    "CampaignAnalytics", "ComplianceReport", "TemplateLibraryFilter",
    "CampaignTargetGroup", "CampaignSettings"
]