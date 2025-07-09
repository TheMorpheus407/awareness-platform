"""
Course and training-related schemas for the application.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import Field, field_validator

from .base import BaseSchema, TimestampMixin, UUIDMixin


class CourseDifficulty(str, Enum):
    """Course difficulty levels."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class CourseProgressStatus(str, Enum):
    """Course progress status."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class CourseLanguage(str, Enum):
    """Available course languages."""

    DE = "de"
    EN = "en"
    FR = "fr"
    IT = "it"


class Course(BaseSchema, UUIDMixin):
    """Course response schema."""

    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., max_length=1000)
    duration_minutes: int = Field(..., gt=0, le=480)
    difficulty: CourseDifficulty
    tags: List[str] = Field(default_factory=list, max_length=20)
    compliance_tags: List[str] = Field(
        default_factory=list,
        description="Compliance frameworks this course covers",
    )
    available_languages: List[CourseLanguage] = Field(
        default_factory=lambda: [CourseLanguage.DE]
    )
    is_mandatory: bool = Field(False)
    is_active: bool = Field(True)
    passing_score: int = Field(80, ge=0, le=100)
    max_attempts: int = Field(3, ge=1, le=10)
    certificate_available: bool = Field(True)
    prerequisites: List[UUID] = Field(
        default_factory=list,
        description="Course IDs that must be completed first",
    )

    @field_validator("tags", "compliance_tags")
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        """Ensure tags are unique and lowercase."""
        return list(set(tag.lower().strip() for tag in v if tag.strip()))


class QuizOption(BaseSchema):
    """Quiz question option."""

    id: str = Field(..., min_length=1, max_length=10)
    text: str = Field(..., min_length=1, max_length=500)


class QuizQuestion(BaseSchema):
    """Quiz question schema."""

    id: str = Field(..., min_length=1, max_length=50)
    question: str = Field(..., min_length=1, max_length=1000)
    options: List[QuizOption] = Field(..., min_length=2, max_length=6)
    correct_answer_id: Optional[str] = Field(
        None, description="Hidden in responses, only for internal use"
    )
    explanation: Optional[str] = Field(
        None, max_length=500, description="Explanation shown after answering"
    )
    points: int = Field(1, ge=1, le=10)

    @field_validator("options")
    @classmethod
    def validate_options(cls, v: List[QuizOption]) -> List[QuizOption]:
        """Ensure option IDs are unique."""
        ids = [opt.id for opt in v]
        if len(ids) != len(set(ids)):
            raise ValueError("Option IDs must be unique")
        return v


class CourseDetail(Course):
    """Detailed course information."""

    youtube_video_id: Optional[str] = Field(None, max_length=20)
    content_markdown: str = Field(..., description="Course content in Markdown")
    quiz_questions: List[QuizQuestion] = Field(
        default_factory=list,
        description="Quiz questions (without correct answers in response)",
    )
    estimated_reading_time_minutes: int = Field(10, ge=1)
    resources: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Additional resources with title and URL",
    )
    created_at: datetime
    updated_at: Optional[datetime]

    @field_validator("quiz_questions")
    @classmethod
    def hide_correct_answers(cls, v: List[QuizQuestion]) -> List[QuizQuestion]:
        """Remove correct answers from questions for security."""
        for question in v:
            question.correct_answer_id = None
        return v


class AssignedCourse(Course):
    """Course with assignment information."""

    assigned_at: datetime
    assigned_by: Optional[UUID] = Field(None, description="User who assigned the course")
    due_date: Optional[datetime] = None
    status: CourseProgressStatus = Field(CourseProgressStatus.NOT_STARTED)
    progress_percentage: float = Field(0.0, ge=0, le=100)
    quiz_score: Optional[float] = Field(None, ge=0, le=100)
    attempts_used: int = Field(0, ge=0)
    completed_at: Optional[datetime] = None
    certificate_id: Optional[UUID] = None

    @field_validator("progress_percentage", "quiz_score")
    @classmethod
    def round_percentages(cls, v: Optional[float]) -> Optional[float]:
        """Round percentages to 2 decimal places."""
        return round(v, 2) if v is not None else None


class CourseProgress(BaseSchema):
    """Course progress tracking."""

    course_id: UUID
    user_id: UUID
    status: CourseProgressStatus = Field(CourseProgressStatus.NOT_STARTED)
    started_at: Optional[datetime] = None
    last_accessed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    video_progress_seconds: int = Field(0, ge=0)
    video_total_seconds: int = Field(0, ge=0)
    video_completion_percentage: float = Field(0.0, ge=0, le=100)
    content_sections_completed: List[str] = Field(default_factory=list)
    quiz_attempts: int = Field(0, ge=0)
    best_quiz_score: Optional[float] = Field(None, ge=0, le=100)
    time_spent_minutes: int = Field(0, ge=0)

    @field_validator("video_completion_percentage", "best_quiz_score")
    @classmethod
    def round_percentages(cls, v: Optional[float]) -> Optional[float]:
        """Round percentages to 2 decimal places."""
        return round(v, 2) if v is not None else None


class ProgressUpdate(BaseSchema):
    """Schema for updating course progress."""

    video_progress_seconds: int = Field(..., ge=0)
    content_section_completed: Optional[str] = Field(
        None, description="ID of completed content section"
    )


class QuizAnswer(BaseSchema):
    """Quiz answer submission."""

    question_id: str = Field(..., min_length=1)
    answer_id: str = Field(..., min_length=1)


class QuizFeedback(BaseSchema):
    """Feedback for a quiz answer."""

    question_id: str
    correct: bool
    selected_answer_id: str
    correct_answer_id: str
    explanation: Optional[str] = None
    points_earned: int = Field(0, ge=0)


class QuizResult(BaseSchema):
    """Quiz result response."""

    score: float = Field(..., ge=0, le=100)
    passed: bool
    passing_score: float = Field(..., ge=0, le=100)
    correct_answers: int = Field(..., ge=0)
    total_questions: int = Field(..., gt=0)
    points_earned: int = Field(..., ge=0)
    total_points: int = Field(..., gt=0)
    feedback: List[QuizFeedback] = Field(default_factory=list)
    attempt_number: int = Field(..., ge=1)
    can_retry: bool = Field(True)
    certificate_id: Optional[UUID] = Field(
        None, description="Certificate ID if passed and available"
    )

    @field_validator("score", "passing_score")
    @classmethod
    def round_scores(cls, v: float) -> float:
        """Round scores to 2 decimal places."""
        return round(v, 2)


class CourseEnrollment(BaseSchema):
    """Course enrollment record."""

    id: UUID
    course_id: UUID
    user_id: UUID
    enrolled_at: datetime
    enrolled_by: Optional[UUID] = None
    due_date: Optional[datetime] = None
    is_mandatory: bool = False
    completion_reminder_sent: bool = False


class CourseCertificate(BaseSchema):
    """Course completion certificate."""

    id: UUID
    user_id: UUID
    course_id: UUID
    issued_at: datetime
    certificate_number: str
    validation_code: str
    pdf_url: Optional[str] = None
    expires_at: Optional[datetime] = None


class CourseStatistics(BaseSchema):
    """Course statistics and analytics."""

    course_id: UUID
    total_enrollments: int = Field(0, ge=0)
    active_learners: int = Field(0, ge=0)
    completion_rate: float = Field(0.0, ge=0, le=100)
    average_score: float = Field(0.0, ge=0, le=100)
    average_time_to_complete_hours: float = Field(0.0, ge=0)
    failure_rate: float = Field(0.0, ge=0, le=100)
    satisfaction_rating: Optional[float] = Field(None, ge=1, le=5)