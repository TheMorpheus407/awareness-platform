"""Course-related schemas."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, validator

from models.course import ContentType, DifficultyLevel, CourseStatus, ProgressStatus


# Enums (re-export for convenience)
__all__ = [
    "ContentType",
    "DifficultyLevel", 
    "CourseStatus",
    "ProgressStatus",
    # Course schemas
    "CourseBase",
    "CourseCreate",
    "CourseUpdate",
    "CourseInDB",
    "CoursePublic",
    "CourseDetail",
    # Module schemas
    "ModuleBase",
    "ModuleCreate",
    "ModuleUpdate",
    "ModuleInDB",
    "ModulePublic",
    # Lesson schemas
    "LessonBase",
    "LessonCreate",
    "LessonUpdate",
    "LessonInDB",
    "LessonPublic",
    "LessonDetail",
    # Content schemas
    "CourseContentBase",
    "CourseContentCreate",
    "CourseContentUpdate",
    "CourseContentInDB",
    # Quiz schemas
    "QuizBase",
    "QuizCreate",
    "QuizUpdate",
    "QuizInDB",
    "QuizPublic",
    "QuizQuestionBase",
    "QuizQuestionCreate",
    "QuizQuestionUpdate",
    "QuizQuestionInDB",
    "QuizAttemptCreate",
    "QuizAttemptSubmit",
    "QuizAttemptResult",
    "QuizAnswerSubmit",
    # Enrollment schemas
    "CourseEnrollmentCreate",
    "CourseEnrollmentInDB",
    "CourseEnrollmentPublic",
    # Progress schemas
    "LessonProgressUpdate",
    "LessonProgressInDB",
    "ModuleProgressInDB",
    "CourseProgressSummary",
    # Review schemas
    "CourseReviewCreate",
    "CourseReviewUpdate",
    "CourseReviewInDB",
    # Announcement schemas
    "CourseAnnouncementCreate",
    "CourseAnnouncementUpdate",
    "CourseAnnouncementInDB",
]


# Base schemas
class CourseBase(BaseModel):
    """Base course schema."""
    title: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    short_description: Optional[str] = Field(None, max_length=500)
    category: str = Field(..., min_length=1, max_length=100)
    difficulty_level: DifficultyLevel = DifficultyLevel.BEGINNER
    duration_minutes: int = Field(0, ge=0)
    thumbnail_url: Optional[str] = None
    preview_video_url: Optional[str] = None
    language: str = Field("de", min_length=2, max_length=10)
    available_languages: List[str] = []
    tags: List[str] = []
    prerequisites: List[int] = []
    learning_objectives: List[str] = []
    target_audience: Optional[str] = None
    is_free: bool = False
    price: Optional[float] = Field(None, ge=0)
    meta_title: Optional[str] = Field(None, max_length=255)
    meta_description: Optional[str] = Field(None, max_length=500)
    compliance_standards: List[str] = []
    validity_days: Optional[int] = Field(None, ge=1)
    scorm_package_url: Optional[str] = None
    scorm_version: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CourseCreate(CourseBase):
    """Schema for creating a course."""
    pass


class CourseUpdate(BaseModel):
    """Schema for updating a course."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    slug: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    short_description: Optional[str] = Field(None, max_length=500)
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    difficulty_level: Optional[DifficultyLevel] = None
    duration_minutes: Optional[int] = Field(None, ge=0)
    status: Optional[CourseStatus] = None
    thumbnail_url: Optional[str] = None
    preview_video_url: Optional[str] = None
    language: Optional[str] = Field(None, min_length=2, max_length=10)
    available_languages: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    prerequisites: Optional[List[int]] = None
    learning_objectives: Optional[List[str]] = None
    target_audience: Optional[str] = None
    is_free: Optional[bool] = None
    price: Optional[float] = Field(None, ge=0)
    meta_title: Optional[str] = Field(None, max_length=255)
    meta_description: Optional[str] = Field(None, max_length=500)
    compliance_standards: Optional[List[str]] = None
    validity_days: Optional[int] = Field(None, ge=1)
    scorm_package_url: Optional[str] = None
    scorm_version: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CourseInDB(CourseBase):
    """Course schema for database."""
    id: int
    status: CourseStatus
    published_at: Optional[datetime] = None
    enrolled_count: int = 0
    completion_count: int = 0
    average_rating: Optional[float] = None
    rating_count: int = 0
    certificate_template_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class CoursePublic(BaseModel):
    """Public course schema (listing)."""
    id: int
    title: str
    slug: str
    short_description: Optional[str] = None
    category: str
    difficulty_level: DifficultyLevel
    duration_minutes: int
    thumbnail_url: Optional[str] = None
    language: str
    tags: List[str] = []
    is_free: bool
    price: Optional[float] = None
    enrolled_count: int
    average_rating: Optional[float] = None
    rating_count: int

    model_config = ConfigDict(from_attributes=True)


class CourseDetail(CourseInDB):
    """Detailed course schema with modules."""
    modules: List["ModulePublic"] = []
    enrollment_status: Optional["CourseEnrollmentPublic"] = None
    can_enroll: bool = True
    enrollment_message: Optional[str] = None


# Module schemas
class ModuleBase(BaseModel):
    """Base module schema."""
    title: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    order_index: int = Field(..., ge=0)
    duration_minutes: int = Field(0, ge=0)

    model_config = ConfigDict(from_attributes=True)


class ModuleCreate(ModuleBase):
    """Schema for creating a module."""
    course_id: int


class ModuleUpdate(BaseModel):
    """Schema for updating a module."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    slug: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    order_index: Optional[int] = Field(None, ge=0)
    duration_minutes: Optional[int] = Field(None, ge=0)

    model_config = ConfigDict(from_attributes=True)


class ModuleInDB(ModuleBase):
    """Module schema for database."""
    id: int
    course_id: int
    created_at: datetime
    updated_at: datetime


class ModulePublic(ModuleBase):
    """Public module schema."""
    id: int
    lessons: List["LessonPublic"] = []
    progress: Optional["ModuleProgressInDB"] = None


# Lesson schemas
class LessonBase(BaseModel):
    """Base lesson schema."""
    title: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    order_index: int = Field(..., ge=0)
    duration_minutes: int = Field(0, ge=0)
    content_type: ContentType = ContentType.VIDEO
    is_preview: bool = False

    model_config = ConfigDict(from_attributes=True)


class LessonCreate(LessonBase):
    """Schema for creating a lesson."""
    module_id: int


class LessonUpdate(BaseModel):
    """Schema for updating a lesson."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    slug: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    order_index: Optional[int] = Field(None, ge=0)
    duration_minutes: Optional[int] = Field(None, ge=0)
    content_type: Optional[ContentType] = None
    is_preview: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


class LessonInDB(LessonBase):
    """Lesson schema for database."""
    id: int
    module_id: int
    created_at: datetime
    updated_at: datetime


class LessonPublic(LessonBase):
    """Public lesson schema."""
    id: int
    has_quiz: bool = False
    is_completed: bool = False
    is_locked: bool = False
    progress: Optional["LessonProgressInDB"] = None


class LessonDetail(LessonInDB):
    """Detailed lesson schema with content."""
    content_items: List["CourseContentInDB"] = []
    quiz: Optional["QuizPublic"] = None
    progress: Optional["LessonProgressInDB"] = None
    next_lesson: Optional["LessonPublic"] = None
    previous_lesson: Optional["LessonPublic"] = None


# Content schemas
class CourseContentBase(BaseModel):
    """Base course content schema."""
    title: str = Field(..., min_length=1, max_length=255)
    content_type: ContentType
    order_index: int = Field(0, ge=0)
    content_url: Optional[str] = None
    external_id: Optional[str] = None
    duration_seconds: Optional[int] = Field(None, ge=0)
    file_size_bytes: Optional[int] = Field(None, ge=0)
    mime_type: Optional[str] = None
    metadata: Dict[str, Any] = {}
    transcript: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CourseContentCreate(CourseContentBase):
    """Schema for creating course content."""
    lesson_id: int


class CourseContentUpdate(BaseModel):
    """Schema for updating course content."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content_type: Optional[ContentType] = None
    order_index: Optional[int] = Field(None, ge=0)
    content_url: Optional[str] = None
    external_id: Optional[str] = None
    duration_seconds: Optional[int] = Field(None, ge=0)
    file_size_bytes: Optional[int] = Field(None, ge=0)
    mime_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    transcript: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CourseContentInDB(CourseContentBase):
    """Course content schema for database."""
    id: int
    lesson_id: int
    created_at: datetime
    updated_at: datetime


# Quiz schemas
class QuizBase(BaseModel):
    """Base quiz schema."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    instructions: Optional[str] = None
    passing_score: int = Field(70, ge=0, le=100)
    time_limit_minutes: Optional[int] = Field(None, ge=1)
    max_attempts: Optional[int] = Field(None, ge=1)
    is_required: bool = True
    randomize_questions: bool = False
    randomize_answers: bool = False
    show_correct_answers: bool = True

    model_config = ConfigDict(from_attributes=True)


class QuizCreate(QuizBase):
    """Schema for creating a quiz."""
    lesson_id: int


class QuizUpdate(BaseModel):
    """Schema for updating a quiz."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    instructions: Optional[str] = None
    passing_score: Optional[int] = Field(None, ge=0, le=100)
    time_limit_minutes: Optional[int] = Field(None, ge=1)
    max_attempts: Optional[int] = Field(None, ge=1)
    is_required: Optional[bool] = None
    randomize_questions: Optional[bool] = None
    randomize_answers: Optional[bool] = None
    show_correct_answers: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


class QuizInDB(QuizBase):
    """Quiz schema for database."""
    id: int
    lesson_id: int
    created_at: datetime
    updated_at: datetime


class QuizPublic(QuizBase):
    """Public quiz schema."""
    id: int
    question_count: int = 0
    attempts_remaining: Optional[int] = None
    best_score: Optional[float] = None
    last_attempt: Optional["QuizAttemptResult"] = None


class QuizQuestionBase(BaseModel):
    """Base quiz question schema."""
    question_text: str
    question_type: str  # multiple_choice, true_false, text, multiple_select
    options: Optional[List[Dict[str, Any]]] = None
    correct_answer: Any  # Can be string or list
    explanation: Optional[str] = None
    hint: Optional[str] = None
    points: int = Field(1, ge=0)
    negative_points: int = Field(0, ge=0)
    partial_credit: bool = False
    order_index: int = Field(..., ge=0)
    is_bonus: bool = False
    image_url: Optional[str] = None
    video_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class QuizQuestionCreate(QuizQuestionBase):
    """Schema for creating a quiz question."""
    quiz_id: int


class QuizQuestionUpdate(BaseModel):
    """Schema for updating a quiz question."""
    question_text: Optional[str] = None
    question_type: Optional[str] = None
    options: Optional[List[Dict[str, Any]]] = None
    correct_answer: Optional[Any] = None
    explanation: Optional[str] = None
    hint: Optional[str] = None
    points: Optional[int] = Field(None, ge=0)
    negative_points: Optional[int] = Field(None, ge=0)
    partial_credit: Optional[bool] = None
    order_index: Optional[int] = Field(None, ge=0)
    is_bonus: Optional[bool] = None
    image_url: Optional[str] = None
    video_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class QuizQuestionInDB(QuizQuestionBase):
    """Quiz question schema for database."""
    id: int
    quiz_id: int
    created_at: datetime
    updated_at: datetime


class QuizAttemptCreate(BaseModel):
    """Schema for creating a quiz attempt."""
    quiz_id: int
    enrollment_id: int


class QuizAnswerSubmit(BaseModel):
    """Schema for submitting a quiz answer."""
    question_id: int
    answer: Any  # Can be string, list, etc.
    time_spent_seconds: Optional[int] = None


class QuizAttemptSubmit(BaseModel):
    """Schema for submitting a quiz attempt."""
    answers: List[QuizAnswerSubmit]


class QuizAttemptResult(BaseModel):
    """Quiz attempt result schema."""
    id: int
    quiz_id: int
    attempt_number: int
    started_at: datetime
    submitted_at: Optional[datetime] = None
    time_spent_seconds: Optional[int] = None
    score: Optional[float] = None
    passed: Optional[bool] = None
    questions_answered: int = 0
    questions_correct: int = 0
    feedback: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# Enrollment schemas
class CourseEnrollmentCreate(BaseModel):
    """Schema for creating a course enrollment."""
    course_id: int
    user_id: Optional[int] = None  # Optional, can be inferred from current user
    company_id: Optional[int] = None  # Optional, can be inferred from user


class CourseEnrollmentInDB(BaseModel):
    """Course enrollment schema for database."""
    id: int
    user_id: int
    course_id: int
    company_id: int
    enrolled_at: datetime
    expires_at: Optional[datetime] = None
    status: ProgressStatus
    progress_percentage: float
    last_accessed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    completion_certificate_id: Optional[UUID] = None
    certificate_issued_at: Optional[datetime] = None
    certificate_expires_at: Optional[datetime] = None
    time_spent_seconds: int
    lessons_completed: int
    lessons_total: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CourseEnrollmentPublic(BaseModel):
    """Public course enrollment schema."""
    id: int
    course_id: int
    enrolled_at: datetime
    expires_at: Optional[datetime] = None
    status: ProgressStatus
    progress_percentage: float
    last_accessed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    certificate_available: bool = False
    certificate_id: Optional[UUID] = None
    time_spent_seconds: int
    lessons_completed: int
    lessons_total: int

    model_config = ConfigDict(from_attributes=True)


# Progress schemas
class LessonProgressUpdate(BaseModel):
    """Schema for updating lesson progress."""
    status: Optional[ProgressStatus] = None
    progress_percentage: Optional[float] = Field(None, ge=0, le=100)
    last_position_seconds: Optional[int] = Field(None, ge=0)
    completed: Optional[bool] = None


class LessonProgressInDB(BaseModel):
    """Lesson progress schema for database."""
    id: int
    enrollment_id: int
    lesson_id: int
    status: ProgressStatus
    progress_percentage: float
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    last_position_seconds: Optional[int] = None
    time_spent_seconds: int
    view_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ModuleProgressInDB(BaseModel):
    """Module progress schema for database."""
    id: int
    enrollment_id: int
    module_id: int
    status: ProgressStatus
    progress_percentage: float
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    time_spent_seconds: int
    lessons_completed: int
    lessons_total: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CourseProgressSummary(BaseModel):
    """Course progress summary schema."""
    enrollment: CourseEnrollmentPublic
    modules_completed: int
    modules_total: int
    current_module: Optional[ModulePublic] = None
    current_lesson: Optional[LessonPublic] = None
    next_lesson: Optional[LessonPublic] = None
    recent_activity: List[Dict[str, Any]] = []


# Review schemas
class CourseReviewCreate(BaseModel):
    """Schema for creating a course review."""
    course_id: int
    rating: int = Field(..., ge=1, le=5)
    title: Optional[str] = Field(None, max_length=255)
    comment: Optional[str] = None


class CourseReviewUpdate(BaseModel):
    """Schema for updating a course review."""
    rating: Optional[int] = Field(None, ge=1, le=5)
    title: Optional[str] = Field(None, max_length=255)
    comment: Optional[str] = None


class CourseReviewInDB(BaseModel):
    """Course review schema for database."""
    id: int
    user_id: int
    course_id: int
    enrollment_id: int
    rating: int
    title: Optional[str] = None
    comment: Optional[str] = None
    is_verified: bool
    helpful_count: int
    created_at: datetime
    updated_at: datetime
    user_name: Optional[str] = None  # Populated from join

    model_config = ConfigDict(from_attributes=True)


# Announcement schemas
class CourseAnnouncementCreate(BaseModel):
    """Schema for creating a course announcement."""
    course_id: int
    title: str = Field(..., min_length=1, max_length=255)
    content: str
    is_pinned: bool = False


class CourseAnnouncementUpdate(BaseModel):
    """Schema for updating a course announcement."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = None
    is_pinned: Optional[bool] = None


class CourseAnnouncementInDB(BaseModel):
    """Course announcement schema for database."""
    id: int
    course_id: int
    author_id: Optional[int] = None
    title: str
    content: str
    is_pinned: bool
    created_at: datetime
    updated_at: datetime
    author_name: Optional[str] = None  # Populated from join

    model_config = ConfigDict(from_attributes=True)


# Update forward references
CourseDetail.model_rebuild()
ModulePublic.model_rebuild()
LessonPublic.model_rebuild()
LessonDetail.model_rebuild()