"""Course management service for creating and managing training content."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.course import Course
from models.user import User
from core.logging import logger
from core.exceptions import ValidationError, NotFoundError


class CourseService:
    """Service for managing courses."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def search_courses(
        self,
        search_term: Optional[str] = None,
        category: Optional[str] = None,
        difficulty: Optional[str] = None,
        is_published: Optional[bool] = True,
        limit: int = 10,
        offset: int = 0
    ) -> List[Course]:
        """Search and filter courses."""
        query = select(Course)
        
        # Apply filters
        filters = []
        if is_published is not None:
            filters.append(Course.is_active == is_published)
            
        if category:
            filters.append(Course.category == category)
            
        if difficulty:
            filters.append(Course.difficulty_level == difficulty)
            
        if search_term:
            search_filter = or_(
                Course.title.ilike(f"%{search_term}%"),
                Course.description.ilike(f"%{search_term}%")
            )
            filters.append(search_filter)
            
        if filters:
            query = query.where(and_(*filters))
            
        # Apply pagination
        query = query.offset(offset).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars())
        
    async def create_course(
        self,
        title: str,
        description: str,
        category: str,
        difficulty: str,
        duration_hours: int,
        created_by_id: int,
        is_published: bool = False,
        tags: Optional[List[str]] = None,
        prerequisites: Optional[List[int]] = None,
    ) -> Course:
        """Create a new course."""
        # Validate difficulty
        valid_difficulties = ["beginner", "intermediate", "advanced"]
        if difficulty not in valid_difficulties:
            raise ValidationError(f"Invalid difficulty. Must be one of: {valid_difficulties}")
            
        # Create course - map fields to actual model
        course = Course(
            title=title,
            description=description,
            category=category,
            difficulty_level=difficulty,  # Map to actual field name
            duration_minutes=duration_hours * 60,  # Convert hours to minutes
            is_active=is_published,  # Map to actual field name
            tags=tags or [],
            prerequisites=prerequisites or [],
        )
        
        self.db.add(course)
        await self.db.commit()
        await self.db.refresh(course)
        
        logger.info(f"Created course: {course.id} - {course.title}")
        return course
        
    async def get_course(self, course_id: int) -> Optional[Course]:
        """Get course by ID."""
        result = await self.db.execute(
            select(Course).where(Course.id == course_id)
        )
        return result.scalar_one_or_none()
        
    async def update_course(
        self,
        course_id: int,
        updates: Dict[str, Any]
    ) -> Course:
        """Update course details."""
        course = await self.get_course(course_id)
        if not course:
            raise NotFoundError("Course not found")
            
        # Map update fields
        field_mapping = {
            "difficulty": "difficulty_level",
            "duration_hours": "duration_minutes",
            "is_published": "is_active"
        }
        
        # Update fields
        for field, value in updates.items():
            mapped_field = field_mapping.get(field, field)
            
            # Convert duration hours to minutes
            if field == "duration_hours":
                value = value * 60
                
            if hasattr(course, mapped_field):
                setattr(course, mapped_field, value)
                
        course.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(course)
        
        return course
        
    async def delete_course(self, course_id: int) -> bool:
        """Delete a course."""
        course = await self.get_course(course_id)
        if not course:
            raise NotFoundError("Course not found")
            
        await self.db.delete(course)
        await self.db.commit()
        
        logger.info(f"Deleted course: {course_id}")
        return True