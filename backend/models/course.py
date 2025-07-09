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