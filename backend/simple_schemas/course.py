"""Simplified course schemas for MVP."""
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class CourseCreate(BaseModel):
    """Course creation schema."""
    title: str
    description: Optional[str] = None
    duration_minutes: int = 30
    is_mandatory: bool = False
    status: str = "draft"


class CourseResponse(CourseCreate):
    """Course response schema."""
    id: UUID
    created_at: datetime
    updated_at: datetime


class ModuleResponse(BaseModel):
    """Module response schema."""
    id: UUID
    course_id: UUID
    title: str
    description: Optional[str] = None
    video_url: Optional[str] = None
    order_index: int
    duration_minutes: int = 10


class QuizSubmit(BaseModel):
    """Quiz submission schema."""
    module_id: UUID
    answers: List[dict]  # Simplified for MVP