"""Course-related models."""

from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
import sqlalchemy as sa

from .base import Base

if TYPE_CHECKING:
    from .user import User
    from .company import Company


class Course(Base):
    """Course model for training content."""
    
    __tablename__ = "courses"
    
    # Basic information
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=False, index=True)
    difficulty_level = Column(String(50), nullable=False)  # beginner, intermediate, advanced
    duration_minutes = Column(Integer, nullable=False)
    
    # Content
    youtube_video_id = Column(String(50), nullable=True)
    content_type = Column(String(50), nullable=False, default="video")  # video, text, interactive
    language = Column(String(10), nullable=False, default="de")
    
    # Metadata
    tags = Column(ARRAY(String), nullable=True)
    prerequisites = Column(ARRAY(Integer), nullable=True)  # List of course IDs
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    
    # Relationships
    quizzes = relationship("Quiz", back_populates="course", cascade="all, delete-orphan")
    progress_records = relationship("UserCourseProgress", back_populates="course")
    
    def __repr__(self) -> str:
        return f"<Course {self.title}>"


class Quiz(Base):
    """Quiz model for course assessments."""
    
    __tablename__ = "quizzes"
    
    # Basic information
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    passing_score = Column(Integer, nullable=False, default=70)
    time_limit_minutes = Column(Integer, nullable=True)
    max_attempts = Column(Integer, nullable=True)
    is_required = Column(Boolean, nullable=False, default=True)
    
    # Relationships
    course = relationship("Course", back_populates="quizzes")
    questions = relationship("QuizQuestion", back_populates="quiz", cascade="all, delete-orphan", order_by="QuizQuestion.order_index")
    
    def __repr__(self) -> str:
        return f"<Quiz {self.title}>"


class QuizQuestion(Base):
    """Quiz question model."""
    
    __tablename__ = "quiz_questions"
    
    # Basic information
    quiz_id = Column(Integer, ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False, index=True)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50), nullable=False)  # multiple_choice, true_false, text
    
    # Question data
    options = Column(JSON, nullable=True)  # For multiple choice questions
    correct_answer = Column(Text, nullable=False)
    explanation = Column(Text, nullable=True)
    points = Column(Integer, nullable=False, default=1)
    order_index = Column(Integer, nullable=False)
    
    # Relationships
    quiz = relationship("Quiz", back_populates="questions")
    
    def __repr__(self) -> str:
        return f"<QuizQuestion {self.id}>"


class UserCourseProgress(Base):
    """User course progress tracking."""
    
    __tablename__ = "user_course_progress"
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Progress data
    status = Column(String(50), nullable=False, default="not_started", index=True)  # not_started, in_progress, completed
    progress_percentage = Column(Integer, nullable=False, default=0)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Certificate
    certificate_issued = Column(Boolean, nullable=False, default=False)
    certificate_url = Column(String(500), nullable=True)
    
    # Relationships
    user = relationship("User", backref="course_progress")
    course = relationship("Course", back_populates="progress_records")
    company = relationship("Company", backref="course_progress")
    
    # Unique constraint
    __table_args__ = (
        sa.UniqueConstraint('user_id', 'course_id', name='uq_user_course'),
    )
    
    def __repr__(self) -> str:
        return f"<UserCourseProgress user={self.user_id} course={self.course_id} status={self.status}>"