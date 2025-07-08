"""Course-related models."""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from enum import Enum

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, JSON, Float, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import relationship
import sqlalchemy as sa
import uuid

from .base import Base

if TYPE_CHECKING:
    from .user import User
    from .company import Company


class ContentType(str, Enum):
    """Content type enumeration."""
    VIDEO = "video"
    DOCUMENT = "document"
    PRESENTATION = "presentation"
    INTERACTIVE = "interactive"
    SCORM = "scorm"
    EXTERNAL_LINK = "external_link"
    TEXT = "text"
    QUIZ = "quiz"


class DifficultyLevel(str, Enum):
    """Course difficulty levels."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class CourseStatus(str, Enum):
    """Course status."""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ProgressStatus(str, Enum):
    """Progress status for courses, modules, and lessons."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class Course(Base):
    """Course model for training content."""
    
    __tablename__ = "courses"
    
    # Basic information
    title = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    short_description = Column(String(500), nullable=True)
    category = Column(String(100), nullable=False, index=True)
    difficulty_level = Column(SQLEnum(DifficultyLevel), nullable=False, default=DifficultyLevel.BEGINNER)
    duration_minutes = Column(Integer, nullable=False, default=0)
    
    # Status and publishing
    status = Column(SQLEnum(CourseStatus), nullable=False, default=CourseStatus.DRAFT)
    published_at = Column(DateTime, nullable=True)
    
    # Media and content
    thumbnail_url = Column(String(500), nullable=True)
    preview_video_url = Column(String(500), nullable=True)
    language = Column(String(10), nullable=False, default="de")
    available_languages = Column(ARRAY(String), nullable=True, default=[])
    
    # Metadata
    tags = Column(ARRAY(String), nullable=True, default=[])
    prerequisites = Column(ARRAY(Integer), nullable=True, default=[])  # List of course IDs
    learning_objectives = Column(ARRAY(String), nullable=True, default=[])
    target_audience = Column(Text, nullable=True)
    
    # Pricing and access
    is_free = Column(Boolean, default=False, nullable=False)
    price = Column(Float, nullable=True)
    
    # SEO and marketing
    meta_title = Column(String(255), nullable=True)
    meta_description = Column(String(500), nullable=True)
    
    # Statistics
    enrolled_count = Column(Integer, nullable=False, default=0)
    completion_count = Column(Integer, nullable=False, default=0)
    average_rating = Column(Float, nullable=True)
    rating_count = Column(Integer, nullable=False, default=0)
    
    # Compliance and certification
    compliance_standards = Column(ARRAY(String), nullable=True, default=[])  # ISO, GDPR, etc.
    certificate_template_id = Column(Integer, nullable=True)
    validity_days = Column(Integer, nullable=True)  # Certificate validity period
    
    # SCORM support
    scorm_package_url = Column(String(500), nullable=True)
    scorm_version = Column(String(50), nullable=True)
    
    # Relationships
    modules = relationship("Module", back_populates="course", cascade="all, delete-orphan", order_by="Module.order_index")
    enrollments = relationship("CourseEnrollment", back_populates="course")
    reviews = relationship("CourseReview", back_populates="course")
    announcements = relationship("CourseAnnouncement", back_populates="course")
    analytics = relationship("CourseAnalytics", back_populates="course")
    
    def __repr__(self) -> str:
        return f"<Course {self.title}>"


class Module(Base):
    """Module model - courses are organized into modules."""
    
    __tablename__ = "modules"
    
    # Basic information
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Order and organization
    order_index = Column(Integer, nullable=False)
    duration_minutes = Column(Integer, nullable=False, default=0)
    
    # Relationships
    course = relationship("Course", back_populates="modules")
    lessons = relationship("Lesson", back_populates="module", cascade="all, delete-orphan", order_by="Lesson.order_index")
    
    # Unique constraint
    __table_args__ = (
        sa.UniqueConstraint('course_id', 'slug', name='uq_course_module_slug'),
    )
    
    def __repr__(self) -> str:
        return f"<Module {self.title}>"


class Lesson(Base):
    """Lesson model - modules contain lessons."""
    
    __tablename__ = "lessons"
    
    # Basic information
    module_id = Column(Integer, ForeignKey("modules.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Order and organization
    order_index = Column(Integer, nullable=False)
    duration_minutes = Column(Integer, nullable=False, default=0)
    
    # Content
    content_type = Column(SQLEnum(ContentType), nullable=False, default=ContentType.VIDEO)
    is_preview = Column(Boolean, default=False, nullable=False)  # Can be viewed without enrollment
    
    # Relationships
    module = relationship("Module", back_populates="lessons")
    content_items = relationship("CourseContent", back_populates="lesson", cascade="all, delete-orphan")
    quiz = relationship("Quiz", back_populates="lesson", uselist=False)
    progress_records = relationship("LessonProgress", back_populates="lesson")
    
    # Unique constraint
    __table_args__ = (
        sa.UniqueConstraint('module_id', 'slug', name='uq_module_lesson_slug'),
    )
    
    def __repr__(self) -> str:
        return f"<Lesson {self.title}>"


class CourseContent(Base):
    """Course content items - videos, documents, etc."""
    
    __tablename__ = "course_content"
    
    # Basic information
    lesson_id = Column(Integer, ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    content_type = Column(SQLEnum(ContentType), nullable=False)
    order_index = Column(Integer, nullable=False, default=0)
    
    # Content location
    content_url = Column(String(500), nullable=True)  # S3 URL, YouTube URL, etc.
    external_id = Column(String(255), nullable=True)  # YouTube ID, Vimeo ID, etc.
    
    # Content metadata
    duration_seconds = Column(Integer, nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    
    # Additional data
    metadata = Column(JSON, nullable=True, default={})  # Flexible storage for content-specific data
    transcript = Column(Text, nullable=True)  # For videos
    
    # Relationships
    lesson = relationship("Lesson", back_populates="content_items")
    
    def __repr__(self) -> str:
        return f"<CourseContent {self.title}>"


class Quiz(Base):
    """Quiz model for course assessments."""
    
    __tablename__ = "quizzes"
    
    # Basic information
    lesson_id = Column(Integer, ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True, unique=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    instructions = Column(Text, nullable=True)
    
    # Quiz settings
    passing_score = Column(Integer, nullable=False, default=70)
    time_limit_minutes = Column(Integer, nullable=True)
    max_attempts = Column(Integer, nullable=True)
    is_required = Column(Boolean, nullable=False, default=True)
    randomize_questions = Column(Boolean, nullable=False, default=False)
    randomize_answers = Column(Boolean, nullable=False, default=False)
    show_correct_answers = Column(Boolean, nullable=False, default=True)
    
    # Relationships
    lesson = relationship("Lesson", back_populates="quiz")
    questions = relationship("QuizQuestion", back_populates="quiz", cascade="all, delete-orphan", order_by="QuizQuestion.order_index")
    attempts = relationship("QuizAttempt", back_populates="quiz")
    
    def __repr__(self) -> str:
        return f"<Quiz {self.title}>"


class QuizQuestion(Base):
    """Quiz question model."""
    
    __tablename__ = "quiz_questions"
    
    # Basic information
    quiz_id = Column(Integer, ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False, index=True)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50), nullable=False)  # multiple_choice, true_false, text, multiple_select
    
    # Question data
    options = Column(JSON, nullable=True)  # For multiple choice questions
    correct_answer = Column(JSON, nullable=False)  # Can be string or array for multiple select
    explanation = Column(Text, nullable=True)
    hint = Column(Text, nullable=True)
    
    # Scoring
    points = Column(Integer, nullable=False, default=1)
    negative_points = Column(Integer, nullable=False, default=0)  # For wrong answers
    partial_credit = Column(Boolean, nullable=False, default=False)
    
    # Organization
    order_index = Column(Integer, nullable=False)
    is_bonus = Column(Boolean, nullable=False, default=False)
    
    # Media
    image_url = Column(String(500), nullable=True)
    video_url = Column(String(500), nullable=True)
    
    # Relationships
    quiz = relationship("Quiz", back_populates="questions")
    answers = relationship("QuizAnswer", back_populates="question")
    
    def __repr__(self) -> str:
        return f"<QuizQuestion {self.id}>"


class CourseEnrollment(Base):
    """Course enrollment tracking."""
    
    __tablename__ = "course_enrollments"
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Enrollment data
    enrolled_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # For time-limited access
    
    # Progress tracking
    status = Column(SQLEnum(ProgressStatus), nullable=False, default=ProgressStatus.NOT_STARTED, index=True)
    progress_percentage = Column(Float, nullable=False, default=0.0)
    last_accessed_at = Column(DateTime, nullable=True)
    
    # Completion data
    completed_at = Column(DateTime, nullable=True)
    completion_certificate_id = Column(UUID(as_uuid=True), nullable=True, default=uuid.uuid4)
    certificate_issued_at = Column(DateTime, nullable=True)
    certificate_expires_at = Column(DateTime, nullable=True)
    
    # Tracking
    time_spent_seconds = Column(Integer, nullable=False, default=0)
    lessons_completed = Column(Integer, nullable=False, default=0)
    lessons_total = Column(Integer, nullable=False, default=0)
    
    # Relationships
    user = relationship("User", backref="course_enrollments")
    course = relationship("Course", back_populates="enrollments")
    company = relationship("Company", backref="course_enrollments")
    module_progress = relationship("ModuleProgress", back_populates="enrollment", cascade="all, delete-orphan")
    lesson_progress = relationship("LessonProgress", back_populates="enrollment", cascade="all, delete-orphan")
    
    # Unique constraint
    __table_args__ = (
        sa.UniqueConstraint('user_id', 'course_id', name='uq_user_course_enrollment'),
    )
    
    def __repr__(self) -> str:
        return f"<CourseEnrollment user={self.user_id} course={self.course_id} status={self.status}>"


class ModuleProgress(Base):
    """Module progress tracking."""
    
    __tablename__ = "module_progress"
    
    # Foreign keys
    enrollment_id = Column(Integer, ForeignKey("course_enrollments.id", ondelete="CASCADE"), nullable=False, index=True)
    module_id = Column(Integer, ForeignKey("modules.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Progress data
    status = Column(SQLEnum(ProgressStatus), nullable=False, default=ProgressStatus.NOT_STARTED)
    progress_percentage = Column(Float, nullable=False, default=0.0)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Tracking
    time_spent_seconds = Column(Integer, nullable=False, default=0)
    lessons_completed = Column(Integer, nullable=False, default=0)
    lessons_total = Column(Integer, nullable=False, default=0)
    
    # Relationships
    enrollment = relationship("CourseEnrollment", back_populates="module_progress")
    module = relationship("Module")
    
    # Unique constraint
    __table_args__ = (
        sa.UniqueConstraint('enrollment_id', 'module_id', name='uq_enrollment_module'),
    )
    
    def __repr__(self) -> str:
        return f"<ModuleProgress enrollment={self.enrollment_id} module={self.module_id}>"


class LessonProgress(Base):
    """Lesson progress tracking."""
    
    __tablename__ = "lesson_progress"
    
    # Foreign keys
    enrollment_id = Column(Integer, ForeignKey("course_enrollments.id", ondelete="CASCADE"), nullable=False, index=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Progress data
    status = Column(SQLEnum(ProgressStatus), nullable=False, default=ProgressStatus.NOT_STARTED)
    progress_percentage = Column(Float, nullable=False, default=0.0)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    last_position_seconds = Column(Integer, nullable=True)  # For video resume
    
    # Tracking
    time_spent_seconds = Column(Integer, nullable=False, default=0)
    view_count = Column(Integer, nullable=False, default=0)
    
    # Relationships
    enrollment = relationship("CourseEnrollment", back_populates="lesson_progress")
    lesson = relationship("Lesson", back_populates="progress_records")
    
    # Unique constraint
    __table_args__ = (
        sa.UniqueConstraint('enrollment_id', 'lesson_id', name='uq_enrollment_lesson'),
    )
    
    def __repr__(self) -> str:
        return f"<LessonProgress enrollment={self.enrollment_id} lesson={self.lesson_id}>"


class QuizAttempt(Base):
    """Quiz attempt tracking."""
    
    __tablename__ = "quiz_attempts"
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False, index=True)
    enrollment_id = Column(Integer, ForeignKey("course_enrollments.id", ondelete="CASCADE"), nullable=False)
    
    # Attempt data
    attempt_number = Column(Integer, nullable=False)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    submitted_at = Column(DateTime, nullable=True)
    time_spent_seconds = Column(Integer, nullable=True)
    
    # Scoring
    score = Column(Float, nullable=True)
    passed = Column(Boolean, nullable=True)
    questions_answered = Column(Integer, nullable=False, default=0)
    questions_correct = Column(Integer, nullable=False, default=0)
    
    # Relationships
    user = relationship("User", backref="quiz_attempts")
    quiz = relationship("Quiz", back_populates="attempts")
    enrollment = relationship("CourseEnrollment", backref="quiz_attempts")
    answers = relationship("QuizAnswer", back_populates="attempt", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<QuizAttempt user={self.user_id} quiz={self.quiz_id} score={self.score}>"


class QuizAnswer(Base):
    """Individual quiz answer tracking."""
    
    __tablename__ = "quiz_answers"
    
    # Foreign keys
    attempt_id = Column(Integer, ForeignKey("quiz_attempts.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("quiz_questions.id", ondelete="CASCADE"), nullable=False)
    
    # Answer data
    answer = Column(JSON, nullable=True)  # User's answer
    is_correct = Column(Boolean, nullable=True)
    points_earned = Column(Float, nullable=False, default=0)
    time_spent_seconds = Column(Integer, nullable=True)
    
    # Relationships
    attempt = relationship("QuizAttempt", back_populates="answers")
    question = relationship("QuizQuestion", back_populates="answers")
    
    # Unique constraint
    __table_args__ = (
        sa.UniqueConstraint('attempt_id', 'question_id', name='uq_attempt_question'),
    )
    
    def __repr__(self) -> str:
        return f"<QuizAnswer attempt={self.attempt_id} question={self.question_id}>"


class CourseReview(Base):
    """Course reviews and ratings."""
    
    __tablename__ = "course_reviews"
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    enrollment_id = Column(Integer, ForeignKey("course_enrollments.id", ondelete="CASCADE"), nullable=False)
    
    # Review data
    rating = Column(Integer, nullable=False)  # 1-5 stars
    title = Column(String(255), nullable=True)
    comment = Column(Text, nullable=True)
    
    # Metadata
    is_verified = Column(Boolean, nullable=False, default=True)  # Completed the course
    helpful_count = Column(Integer, nullable=False, default=0)
    
    # Relationships
    user = relationship("User", backref="course_reviews")
    course = relationship("Course", back_populates="reviews")
    enrollment = relationship("CourseEnrollment", backref="review", uselist=False)
    
    # Unique constraint
    __table_args__ = (
        sa.UniqueConstraint('user_id', 'course_id', name='uq_user_course_review'),
    )
    
    def __repr__(self) -> str:
        return f"<CourseReview user={self.user_id} course={self.course_id} rating={self.rating}>"


class CourseAnnouncement(Base):
    """Course announcements from instructors."""
    
    __tablename__ = "course_announcements"
    
    # Foreign keys
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Announcement data
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    is_pinned = Column(Boolean, nullable=False, default=False)
    
    # Relationships
    course = relationship("Course", back_populates="announcements")
    author = relationship("User", backref="course_announcements")
    
    def __repr__(self) -> str:
        return f"<CourseAnnouncement {self.title}>"


# Keep the old model for backward compatibility during migration
UserCourseProgress = CourseEnrollment