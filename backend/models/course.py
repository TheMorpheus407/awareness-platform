"""Course, Quiz, and Progress tracking models."""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY, JSON

from .base import BaseModel

if TYPE_CHECKING:
    from .user import User
    from .company import Company


class Course(BaseModel):
    """Course model for training content."""
    
    __tablename__ = "courses"
    
    # Basic Information
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=False, index=True)
    difficulty_level = Column(String(50), nullable=False)  # beginner, intermediate, advanced
    duration_minutes = Column(Integer, nullable=False)
    
    # Content
    youtube_video_id = Column(String(50), nullable=True)
    content_type = Column(String(50), nullable=False, server_default='video')  # video, text, interactive
    language = Column(String(10), nullable=False, server_default='de')
    
    # Metadata
    tags = Column(ARRAY(String), nullable=True)
    prerequisites = Column(ARRAY(Integer), nullable=True)  # IDs of prerequisite courses
    
    # Status
    is_active = Column(Boolean, nullable=False, server_default=text('true'), index=True)
    
    # Relationships
    modules: List["Module"] = relationship(
        "Module",
        back_populates="course",
        cascade="all, delete-orphan",
        order_by="Module.order_index"
    )
    quizzes: List["Quiz"] = relationship(
        "Quiz",
        back_populates="course",
        cascade="all, delete-orphan"
    )
    user_progress: List["UserCourseProgress"] = relationship(
        "UserCourseProgress",
        back_populates="course",
        cascade="all, delete-orphan"
    )
    
    @property
    def has_quiz(self) -> bool:
        """Check if course has at least one quiz."""
        return len(self.quizzes) > 0
    
    @property
    def required_quiz_count(self) -> int:
        """Get count of required quizzes."""
        return len([q for q in self.quizzes if q.is_required])
    
    def get_prerequisite_courses(self) -> List[int]:
        """Get list of prerequisite course IDs."""
        return self.prerequisites or []
    
    def __repr__(self) -> str:
        """String representation of Course."""
        return f"<Course {self.title} ({self.category})>"


class Quiz(BaseModel):
    """Quiz model for course assessments."""
    
    __tablename__ = "quizzes"
    
    # Foreign Keys
    course_id = Column(Integer, ForeignKey('courses.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Quiz Information
    title = Column(String(255), nullable=False)
    passing_score = Column(Integer, nullable=False, server_default=text('70'))
    time_limit_minutes = Column(Integer, nullable=True)
    max_attempts = Column(Integer, nullable=True)
    is_required = Column(Boolean, nullable=False, server_default=text('true'))
    
    # Relationships
    course: "Course" = relationship("Course", back_populates="quizzes")
    questions: List["QuizQuestion"] = relationship(
        "QuizQuestion",
        back_populates="quiz",
        cascade="all, delete-orphan",
        order_by="QuizQuestion.order_index"
    )
    
    @property
    def total_points(self) -> int:
        """Calculate total possible points for the quiz."""
        return sum(q.points for q in self.questions)
    
    @property
    def question_count(self) -> int:
        """Get number of questions in the quiz."""
        return len(self.questions)
    
    def calculate_score(self, answers: dict) -> tuple[int, int]:
        """
        Calculate score based on provided answers.
        Returns tuple of (score, total_points).
        """
        score = 0
        for question in self.questions:
            if str(question.id) in answers:
                if answers[str(question.id)] == question.correct_answer:
                    score += question.points
        return score, self.total_points
    
    def __repr__(self) -> str:
        """String representation of Quiz."""
        return f"<Quiz {self.title} (Course: {self.course_id})>"


class QuizQuestion(BaseModel):
    """Quiz question model."""
    
    __tablename__ = "quiz_questions"
    
    # Foreign Keys
    quiz_id = Column(Integer, ForeignKey('quizzes.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Question Information
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50), nullable=False)  # multiple_choice, true_false, text
    options = Column(JSON, nullable=True)  # For multiple choice questions
    correct_answer = Column(Text, nullable=False)
    explanation = Column(Text, nullable=True)
    points = Column(Integer, nullable=False, server_default=text('1'))
    order_index = Column(Integer, nullable=False)
    
    # Relationships
    quiz: "Quiz" = relationship("Quiz", back_populates="questions")
    
    @property
    def is_multiple_choice(self) -> bool:
        """Check if question is multiple choice."""
        return self.question_type == 'multiple_choice'
    
    @property
    def is_true_false(self) -> bool:
        """Check if question is true/false."""
        return self.question_type == 'true_false'
    
    @property
    def is_text(self) -> bool:
        """Check if question is text/essay type."""
        return self.question_type == 'text'
    
    def __repr__(self) -> str:
        """String representation of QuizQuestion."""
        return f"<QuizQuestion {self.id} (Quiz: {self.quiz_id})>"


class UserCourseProgress(BaseModel):
    """User course progress tracking model."""
    
    __tablename__ = "user_course_progress"
    __table_args__ = (
        UniqueConstraint('user_id', 'course_id', name='uq_user_course'),
    )
    
    # Foreign Keys
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey('courses.id', ondelete='CASCADE'), nullable=False)
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Progress Information
    status = Column(String(50), nullable=False, server_default='not_started', index=True)  # not_started, in_progress, completed
    progress_percentage = Column(Integer, nullable=False, server_default=text('0'))
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Certificate
    certificate_issued = Column(Boolean, nullable=False, server_default=text('false'))
    certificate_url = Column(String(500), nullable=True)
    
    # Relationships
    user: "User" = relationship("User", back_populates="course_progress")
    course: "Course" = relationship("Course", back_populates="user_progress")
    company: "Company" = relationship("Company", back_populates="user_course_progress")
    
    @property
    def is_completed(self) -> bool:
        """Check if course is completed."""
        return self.status == 'completed'
    
    @property
    def is_in_progress(self) -> bool:
        """Check if course is in progress."""
        return self.status == 'in_progress'
    
    @property
    def is_not_started(self) -> bool:
        """Check if course has not been started."""
        return self.status == 'not_started'
    
    def start_course(self) -> None:
        """Mark course as started."""
        if self.status == 'not_started':
            self.status = 'in_progress'
            self.started_at = datetime.utcnow()
    
    def complete_course(self) -> None:
        """Mark course as completed."""
        self.status = 'completed'
        self.progress_percentage = 100
        self.completed_at = datetime.utcnow()
    
    def update_progress(self, percentage: int) -> None:
        """Update course progress percentage."""
        self.progress_percentage = max(0, min(100, percentage))
        if self.progress_percentage == 100:
            self.complete_course()
        elif self.progress_percentage > 0 and self.status == 'not_started':
            self.start_course()
    
    def __repr__(self) -> str:
        """String representation of UserCourseProgress."""
        return f"<UserCourseProgress User:{self.user_id} Course:{self.course_id} ({self.status})>"


class Module(BaseModel):
    """Module model for course structure."""
    
    __tablename__ = "modules"
    
    # Foreign Keys
    course_id = Column(Integer, ForeignKey('courses.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Module Information
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    order_index = Column(Integer, nullable=False)
    duration_minutes = Column(Integer, nullable=False, server_default=text('30'))
    
    # Status
    is_active = Column(Boolean, nullable=False, server_default=text('true'))
    is_required = Column(Boolean, nullable=False, server_default=text('true'))
    
    # Relationships
    course: "Course" = relationship("Course", back_populates="modules")
    lessons: List["Lesson"] = relationship(
        "Lesson",
        back_populates="module",
        cascade="all, delete-orphan",
        order_by="Lesson.order_index"
    )
    
    @property
    def lesson_count(self) -> int:
        """Get number of lessons in the module."""
        return len(self.lessons)
    
    @property
    def total_duration(self) -> int:
        """Calculate total duration including all lessons."""
        return self.duration_minutes + sum(lesson.duration_minutes for lesson in self.lessons)
    
    def __repr__(self) -> str:
        """String representation of Module."""
        return f"<Module {self.title} (Course: {self.course_id})>"


class Lesson(BaseModel):
    """Lesson model for module content."""
    
    __tablename__ = "lessons"
    
    # Foreign Keys
    module_id = Column(Integer, ForeignKey('modules.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Lesson Information
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    content_type = Column(String(50), nullable=False)  # video, text, interactive, mixed
    content_url = Column(String(500), nullable=True)  # For video/external content
    content_markdown = Column(Text, nullable=True)  # For text content
    order_index = Column(Integer, nullable=False)
    duration_minutes = Column(Integer, nullable=False, server_default=text('10'))
    
    # Interactive Elements
    interactive_elements = Column(JSON, nullable=True)  # JSON structure for interactive content
    resources = Column(JSON, nullable=True)  # Additional resources (downloads, links)
    
    # Status
    is_active = Column(Boolean, nullable=False, server_default=text('true'))
    is_required = Column(Boolean, nullable=False, server_default=text('true'))
    
    # Relationships
    module: "Module" = relationship("Module", back_populates="lessons")
    
    @property
    def is_video(self) -> bool:
        """Check if lesson is video content."""
        return self.content_type == 'video'
    
    @property
    def is_text(self) -> bool:
        """Check if lesson is text content."""
        return self.content_type == 'text'
    
    @property
    def is_interactive(self) -> bool:
        """Check if lesson has interactive elements."""
        return self.content_type == 'interactive' or bool(self.interactive_elements)
    
    def __repr__(self) -> str:
        """String representation of Lesson."""
        return f"<Lesson {self.title} (Module: {self.module_id})>"


class UserLessonProgress(BaseModel):
    """Track user progress for individual lessons."""
    
    __tablename__ = "user_lesson_progress"
    __table_args__ = (
        UniqueConstraint('user_id', 'lesson_id', name='uq_user_lesson'),
    )
    
    # Foreign Keys
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    lesson_id = Column(Integer, ForeignKey('lessons.id', ondelete='CASCADE'), nullable=False)
    module_id = Column(Integer, ForeignKey('modules.id', ondelete='CASCADE'), nullable=False)
    course_id = Column(Integer, ForeignKey('courses.id', ondelete='CASCADE'), nullable=False)
    
    # Progress Information
    status = Column(String(50), nullable=False, server_default='not_started')  # not_started, in_progress, completed
    progress_percentage = Column(Integer, nullable=False, server_default=text('0'))
    time_spent_seconds = Column(Integer, nullable=False, server_default=text('0'))
    
    # Video Progress
    video_progress_seconds = Column(Integer, nullable=True)
    video_total_seconds = Column(Integer, nullable=True)
    
    # Interactive Progress
    interactions_completed = Column(JSON, nullable=True)  # Track completed interactive elements
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    last_accessed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user: "User" = relationship("User", back_populates="lesson_progress")
    lesson: "Lesson" = relationship("Lesson")
    
    def mark_complete(self) -> None:
        """Mark lesson as completed."""
        self.status = 'completed'
        self.progress_percentage = 100
        self.completed_at = datetime.utcnow()
    
    def update_video_progress(self, current_seconds: int, total_seconds: int) -> None:
        """Update video watching progress."""
        self.video_progress_seconds = current_seconds
        self.video_total_seconds = total_seconds
        percentage = int((current_seconds / total_seconds) * 100) if total_seconds > 0 else 0
        self.progress_percentage = min(100, percentage)
        self.last_accessed_at = datetime.utcnow()
        
        if percentage >= 90:  # Consider completed at 90%
            self.mark_complete()
    
    def __repr__(self) -> str:
        """String representation of UserLessonProgress."""
        return f"<UserLessonProgress User:{self.user_id} Lesson:{self.lesson_id} ({self.status})>"


class Badge(BaseModel):
    """Badge model for gamification."""
    
    __tablename__ = "badges"
    
    # Badge Information
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=False)
    icon_url = Column(String(500), nullable=True)
    badge_type = Column(String(50), nullable=False)  # completion, streak, score, special
    
    # Requirements
    requirements = Column(JSON, nullable=False)  # JSON structure defining earning criteria
    points_value = Column(Integer, nullable=False, server_default=text('10'))
    
    # Status
    is_active = Column(Boolean, nullable=False, server_default=text('true'))
    
    # Relationships
    user_badges: List["UserBadge"] = relationship(
        "UserBadge",
        back_populates="badge",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        """String representation of Badge."""
        return f"<Badge {self.name} ({self.badge_type})>"


class UserBadge(BaseModel):
    """User earned badges tracking."""
    
    __tablename__ = "user_badges"
    __table_args__ = (
        UniqueConstraint('user_id', 'badge_id', name='uq_user_badge'),
    )
    
    # Foreign Keys
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    badge_id = Column(Integer, ForeignKey('badges.id', ondelete='CASCADE'), nullable=False)
    
    # Earning Information
    earned_at = Column(DateTime(timezone=True), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    earned_for = Column(JSON, nullable=True)  # Context of how badge was earned
    points_awarded = Column(Integer, nullable=False)
    
    # Relationships
    user: "User" = relationship("User", back_populates="badges")
    badge: "Badge" = relationship("Badge", back_populates="user_badges")
    
    def __repr__(self) -> str:
        """String representation of UserBadge."""
        return f"<UserBadge User:{self.user_id} Badge:{self.badge_id}>"


class UserPoints(BaseModel):
    """Track user points for gamification."""
    
    __tablename__ = "user_points"
    
    # Foreign Keys
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)
    
    # Points Information
    total_points = Column(Integer, nullable=False, server_default=text('0'))
    current_level = Column(Integer, nullable=False, server_default=text('1'))
    points_to_next_level = Column(Integer, nullable=False, server_default=text('100'))
    
    # Statistics
    courses_completed = Column(Integer, nullable=False, server_default=text('0'))
    perfect_quizzes = Column(Integer, nullable=False, server_default=text('0'))
    current_streak_days = Column(Integer, nullable=False, server_default=text('0'))
    longest_streak_days = Column(Integer, nullable=False, server_default=text('0'))
    last_activity_date = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user: "User" = relationship("User", back_populates="points", uselist=False)
    
    def add_points(self, points: int, reason: str) -> tuple[int, bool]:
        """
        Add points and check for level up.
        Returns (new_level, leveled_up).
        """
        self.total_points += points
        leveled_up = False
        
        # Check for level up (100 points per level, increasing by 50 each level)
        while self.total_points >= self.points_to_next_level:
            self.current_level += 1
            self.points_to_next_level += 50 * self.current_level
            leveled_up = True
        
        return self.current_level, leveled_up
    
    def update_streak(self, activity_date: datetime) -> None:
        """Update streak based on activity date."""
        if self.last_activity_date:
            days_diff = (activity_date.date() - self.last_activity_date.date()).days
            if days_diff == 1:
                self.current_streak_days += 1
            elif days_diff > 1:
                self.current_streak_days = 1
        else:
            self.current_streak_days = 1
        
        self.longest_streak_days = max(self.longest_streak_days, self.current_streak_days)
        self.last_activity_date = activity_date
    
    def __repr__(self) -> str:
        """String representation of UserPoints."""
        return f"<UserPoints User:{self.user_id} Points:{self.total_points} Level:{self.current_level}>"


class Certificate(BaseModel):
    """Certificate model for course completion."""
    
    __tablename__ = "certificates"
    __table_args__ = (
        UniqueConstraint('user_id', 'course_id', name='uq_user_course_certificate'),
    )
    
    # Foreign Keys
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey('courses.id', ondelete='CASCADE'), nullable=False)
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'), nullable=False)
    
    # Certificate Information
    certificate_number = Column(String(50), nullable=False, unique=True)
    verification_code = Column(String(100), nullable=False, unique=True)
    issued_at = Column(DateTime(timezone=True), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Course Performance
    completion_date = Column(DateTime(timezone=True), nullable=False)
    final_score = Column(Integer, nullable=False)  # Quiz score percentage
    time_spent_hours = Column(Integer, nullable=False)
    
    # File Information
    pdf_url = Column(String(500), nullable=True)
    pdf_generated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user: "User" = relationship("User", back_populates="certificates")
    course: "Course" = relationship("Course")
    company: "Company" = relationship("Company")
    
    def is_valid(self) -> bool:
        """Check if certificate is still valid."""
        if self.expires_at:
            return datetime.utcnow() < self.expires_at
        return True
    
    def __repr__(self) -> str:
        """String representation of Certificate."""
        return f"<Certificate {self.certificate_number} User:{self.user_id} Course:{self.course_id}>"