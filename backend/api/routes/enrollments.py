"""Course enrollment routes."""

from typing import Optional, List
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from api.dependencies.auth import get_current_active_user, require_company_admin
from api.dependencies.common import get_db, get_pagination_params
from models.course import Course, UserCourseProgress
from models.user import User, UserRole
from schemas.course import (
    CourseEnrollment,
    CourseProgress,
)
from schemas.user import User as UserSchema

router = APIRouter()


@router.post("/", response_model=CourseEnrollment)
async def enroll_in_course(
    enrollment_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> CourseEnrollment:
    """
    Enroll user in a course.
    
    Args:
        enrollment_data: Enrollment data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Created enrollment
        
    Raises:
        HTTPException: If course not found or already enrolled
    """
    # Check if course exists and is published
    course_result = await db.execute(
        select(Course).where(
            and_(
                Course.id == enrollment_data.course_id,
                Course.is_published == True,
            )
        )
    )
    course = course_result.scalar_one_or_none()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found or not available"
        )
    
    # Check if already enrolled
    existing_result = await db.execute(
        select(CourseEnrollment).where(
            and_(
                CourseEnrollment.course_id == enrollment_data.course_id,
                CourseEnrollment.user_id == current_user.id,
            )
        )
    )
    if existing_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already enrolled in this course"
        )
    
    # Create enrollment
    enrollment = CourseEnrollment(
        course_id=enrollment_data.course_id,
        user_id=current_user.id,
        enrolled_at=datetime.utcnow(),
    )
    db.add(enrollment)
    await db.commit()
    await db.refresh(enrollment)
    
    return enrollment


@router.get("/my-courses", response_model=List[CourseEnrollment])
async def get_my_enrollments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    pagination: tuple[int, int] = Depends(get_pagination_params),
    status: Optional[str] = Query(None, regex="^(active|completed)$"),
) -> List[CourseEnrollment]:
    """
    Get current user's course enrollments.
    
    Args:
        db: Database session
        current_user: Current authenticated user
        pagination: Offset and limit
        status: Filter by status (active/completed)
        
    Returns:
        Paginated list of enrollments
    """
    offset, limit = pagination
    
    # Base query
    query = select(CourseEnrollment).options(
        selectinload(CourseEnrollment.course)
    ).where(
        CourseEnrollment.user_id == current_user.id
    )
    
    # Apply status filter
    if status == "completed":
        query = query.where(CourseEnrollment.completed_at.isnot(None))
    elif status == "active":
        query = query.where(CourseEnrollment.completed_at.is_(None))
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination and ordering
    query = query.order_by(CourseEnrollment.enrolled_at.desc()).offset(offset).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    enrollments = result.scalars().all()
    
    return enrollments


@router.get("/course/{course_id}/users", response_model=List[UserSchema])
async def get_course_enrollments(
    course_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_company_admin),
) -> List[User]:
    """
    Get users enrolled in a course (admin only).
    
    Args:
        course_id: Course ID
        db: Database session
        current_user: Current authenticated user (must be admin)
        
    Returns:
        List of enrolled users
    """
    # Get enrolled users from the same company
    result = await db.execute(
        select(User)
        .join(CourseEnrollment)
        .where(
            and_(
                CourseEnrollment.course_id == course_id,
                User.company_id == current_user.company_id,
            )
        )
        .order_by(CourseEnrollment.enrolled_at)
    )
    users = result.scalars().all()
    
    return users


@router.post("/lessons/{lesson_id}/progress", response_model=dict)
async def update_lesson_progress(
    lesson_id: UUID,
    progress_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Update lesson progress.
    
    Args:
        lesson_id: Lesson ID
        progress_data: Progress update data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Updated lesson progress
        
    Raises:
        HTTPException: If lesson not found or not enrolled
    """
    # Lesson progress functionality not implemented
    return {"message": "Lesson progress functionality not implemented"}


@router.delete("/{enrollment_id}")
async def unenroll_from_course(
    enrollment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Unenroll from a course.
    
    Args:
        enrollment_id: Enrollment ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If enrollment not found or no access
    """
    # Get enrollment
    result = await db.execute(
        select(CourseEnrollment).where(
            and_(
                CourseEnrollment.id == enrollment_id,
                CourseEnrollment.user_id == current_user.id,
            )
        )
    )
    enrollment = result.scalar_one_or_none()
    
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enrollment not found"
        )
    
    # Delete enrollment and related progress
    await db.delete(enrollment)
    await db.commit()
    
    return {"message": "Successfully unenrolled from course"}


async def _check_course_completion(db: AsyncSession, enrollment: dict) -> None:
    """
    Check if all lessons in a course are completed and update enrollment.
    
    Args:
        db: Database session
        enrollment: Course enrollment to check
    """
    # Course completion check not implemented
    pass