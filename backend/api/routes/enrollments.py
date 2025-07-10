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

router = APIRouter()


@router.post("/", response_model=CourseEnrollmentSchema)
async def enroll_in_course(
    enrollment_data: CourseEnrollmentCreate,
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


@router.get("/my-courses", response_model=CourseEnrollmentListResponse)
async def get_my_enrollments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    pagination: tuple[int, int] = Depends(get_pagination_params),
    status: Optional[str] = Query(None, regex="^(active|completed)$"),
) -> CourseEnrollmentListResponse:
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
    
    return CourseEnrollmentListResponse(
        items=enrollments,
        total=total,
        page=(offset // limit) + 1,
        size=limit,
        pages=(total + limit - 1) // limit,
    )


@router.get("/course/{course_id}/users", response_model=List[User])
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


@router.post("/lessons/{lesson_id}/progress", response_model=LessonProgressSchema)
async def update_lesson_progress(
    lesson_id: UUID,
    progress_data: LessonProgressUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> LessonProgress:
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
    # Check if lesson exists and get course ID
    lesson_result = await db.execute(
        select(Lesson)
        .options(selectinload(Lesson.module))
        .where(Lesson.id == lesson_id)
    )
    lesson = lesson_result.scalar_one_or_none()
    
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )
    
    # Check if user is enrolled in the course
    enrollment_result = await db.execute(
        select(CourseEnrollment).where(
            and_(
                CourseEnrollment.course_id == lesson.module.course_id,
                CourseEnrollment.user_id == current_user.id,
            )
        )
    )
    enrollment = enrollment_result.scalar_one_or_none()
    
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enrolled in this course"
        )
    
    # Get or create lesson progress
    progress_result = await db.execute(
        select(LessonProgress).where(
            and_(
                LessonProgress.lesson_id == lesson_id,
                LessonProgress.user_id == current_user.id,
            )
        )
    )
    progress = progress_result.scalar_one_or_none()
    
    if not progress:
        progress = LessonProgress(
            lesson_id=lesson_id,
            user_id=current_user.id,
            enrollment_id=enrollment.id,
        )
        db.add(progress)
    
    # Update progress
    if progress_data.is_completed is not None:
        progress.is_completed = progress_data.is_completed
        if progress_data.is_completed and not progress.completed_at:
            progress.completed_at = datetime.utcnow()
    
    if progress_data.time_spent is not None:
        progress.time_spent = (progress.time_spent or 0) + progress_data.time_spent
    
    if progress_data.quiz_score is not None:
        progress.quiz_score = progress_data.quiz_score
    
    await db.commit()
    await db.refresh(progress)
    
    # Check if course is completed
    await _check_course_completion(db, enrollment)
    
    return progress


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


async def _check_course_completion(db: AsyncSession, enrollment: CourseEnrollment) -> None:
    """
    Check if all lessons in a course are completed and update enrollment.
    
    Args:
        db: Database session
        enrollment: Course enrollment to check
    """
    # Get total lessons in course
    total_lessons_result = await db.execute(
        select(func.count(Lesson.id))
        .join(Module)
        .where(Module.course_id == enrollment.course_id)
    )
    total_lessons = total_lessons_result.scalar()
    
    # Get completed lessons
    completed_lessons_result = await db.execute(
        select(func.count(LessonProgress.id))
        .join(Lesson)
        .join(Module)
        .where(
            and_(
                Module.course_id == enrollment.course_id,
                LessonProgress.user_id == enrollment.user_id,
                LessonProgress.is_completed == True,
            )
        )
    )
    completed_lessons = completed_lessons_result.scalar()
    
    # Update enrollment if course is completed
    if total_lessons > 0 and completed_lessons >= total_lessons:
        if not enrollment.completed_at:
            enrollment.completed_at = datetime.utcnow()
            await db.commit()