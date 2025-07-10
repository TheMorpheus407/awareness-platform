"""Course management routes."""

from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, or_, and_
from sqlalchemy.orm import selectinload, joinedload

from api.dependencies.auth import get_current_active_user, require_company_admin
from api.dependencies.common import get_db, get_pagination_params
from models.course import Course, UserCourseProgress
from models.user import User, UserRole
from schemas.course import (
    Course as CourseSchema,
    CourseDetail,
    CourseEnrollment,
    CourseProgress,
)

router = APIRouter()


@router.get("/", response_model=CourseListResponse)
async def list_courses(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    pagination: tuple[int, int] = Depends(get_pagination_params),
    search: Optional[str] = Query(None, description="Search in title or description"),
    category: Optional[str] = Query(None, description="Filter by category"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty"),
    is_published: Optional[bool] = Query(True, description="Filter by published status"),
) -> CourseListResponse:
    """
    List available courses.
    
    Args:
        db: Database session
        current_user: Current authenticated user
        pagination: Offset and limit
        search: Search term
        category: Filter by category
        difficulty: Filter by difficulty
        is_published: Filter by published status
        
    Returns:
        Paginated list of courses
    """
    offset, limit = pagination
    
    # Base query
    query = select(Course)
    
    # Non-admin users can only see published courses
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPERUSER]:
        query = query.where(Course.is_published == True)
    elif is_published is not None:
        query = query.where(Course.is_published == is_published)
    
    # Apply search filter
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Course.title.ilike(search_term),
                Course.description.ilike(search_term),
            )
        )
    
    # Apply category filter
    if category:
        query = query.where(Course.category == category)
    
    # Apply difficulty filter
    if difficulty:
        query = query.where(Course.difficulty == difficulty)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination and ordering
    query = query.order_by(Course.order_index, Course.created_at).offset(offset).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    courses = result.scalars().all()
    
    return CourseListResponse(
        items=courses,
        total=total,
        page=(offset // limit) + 1,
        size=limit,
        pages=(total + limit - 1) // limit,
    )


@router.post("/", response_model=CourseSchema)
async def create_course(
    course_data: CourseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_company_admin),
) -> Course:
    """
    Create new course (admin only).
    
    Args:
        course_data: Course creation data
        db: Database session
        current_user: Current authenticated user (must be admin)
        
    Returns:
        Created course
    """
    # Create course
    course = Course(**course_data.model_dump())
    db.add(course)
    await db.commit()
    await db.refresh(course)
    
    return course


@router.get("/{course_id}", response_model=CourseWithModules)
async def get_course(
    course_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Course:
    """
    Get course by ID with modules.
    
    Args:
        course_id: Course ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Course details with modules
        
    Raises:
        HTTPException: If course not found or no access
    """
    # Get course with modules
    result = await db.execute(
        select(Course)
        .options(
            selectinload(Course.modules).selectinload(Module.lessons)
        )
        .where(Course.id == course_id)
    )
    course = result.scalar_one_or_none()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Check access permissions
    if not course.is_published and current_user.role not in [UserRole.ADMIN, UserRole.SUPERUSER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Course is not published"
        )
    
    return course


@router.patch("/{course_id}", response_model=CourseSchema)
async def update_course(
    course_id: UUID,
    course_update: CourseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_company_admin),
) -> Course:
    """
    Update course (admin only).
    
    Args:
        course_id: Course ID
        course_update: Course update data
        db: Database session
        current_user: Current authenticated user (must be admin)
        
    Returns:
        Updated course
        
    Raises:
        HTTPException: If course not found
    """
    # Get course
    result = await db.execute(
        select(Course).where(Course.id == course_id)
    )
    course = result.scalar_one_or_none()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Update course fields
    update_data = course_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(course, field, value)
    
    await db.commit()
    await db.refresh(course)
    
    return course


@router.delete("/{course_id}")
async def delete_course(
    course_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_company_admin),
) -> dict:
    """
    Delete course (admin only).
    
    Args:
        course_id: Course ID
        db: Database session
        current_user: Current authenticated user (must be admin)
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If course not found
    """
    # Get course
    result = await db.execute(
        select(Course).where(Course.id == course_id)
    )
    course = result.scalar_one_or_none()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Check if course has enrollments
    enrollment_count = await db.execute(
        select(func.count(CourseEnrollment.id))
        .where(CourseEnrollment.course_id == course_id)
    )
    if enrollment_count.scalar() > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete course with enrollments"
        )
    
    # Delete course
    await db.delete(course)
    await db.commit()
    
    return {"message": "Course deleted successfully"}


@router.post("/{course_id}/modules", response_model=ModuleSchema)
async def create_module(
    course_id: UUID,
    module_data: ModuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_company_admin),
) -> Module:
    """
    Create new module in course (admin only).
    
    Args:
        course_id: Course ID
        module_data: Module creation data
        db: Database session
        current_user: Current authenticated user (must be admin)
        
    Returns:
        Created module
        
    Raises:
        HTTPException: If course not found
    """
    # Check if course exists
    course_result = await db.execute(
        select(Course).where(Course.id == course_id)
    )
    if not course_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Create module
    module = Module(
        **module_data.model_dump(),
        course_id=course_id
    )
    db.add(module)
    await db.commit()
    await db.refresh(module)
    
    return module


@router.post("/{course_id}/modules/{module_id}/lessons", response_model=LessonSchema)
async def create_lesson(
    course_id: UUID,
    module_id: UUID,
    lesson_data: LessonCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_company_admin),
) -> Lesson:
    """
    Create new lesson in module (admin only).
    
    Args:
        course_id: Course ID
        module_id: Module ID
        lesson_data: Lesson creation data
        db: Database session
        current_user: Current authenticated user (must be admin)
        
    Returns:
        Created lesson
        
    Raises:
        HTTPException: If module not found
    """
    # Check if module exists and belongs to course
    module_result = await db.execute(
        select(Module).where(
            and_(
                Module.id == module_id,
                Module.course_id == course_id
            )
        )
    )
    if not module_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found in this course"
        )
    
    # Create lesson
    lesson = Lesson(
        **lesson_data.model_dump(),
        module_id=module_id
    )
    db.add(lesson)
    await db.commit()
    await db.refresh(lesson)
    
    return lesson


@router.get("/{course_id}/progress", response_model=CourseProgress)
async def get_course_progress(
    course_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> CourseProgress:
    """
    Get user's progress in a course.
    
    Args:
        course_id: Course ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Course progress details
        
    Raises:
        HTTPException: If not enrolled in course
    """
    # Check enrollment
    enrollment_result = await db.execute(
        select(CourseEnrollment)
        .where(
            and_(
                CourseEnrollment.course_id == course_id,
                CourseEnrollment.user_id == current_user.id
            )
        )
    )
    enrollment = enrollment_result.scalar_one_or_none()
    
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not enrolled in this course"
        )
    
    # Get total lessons
    total_lessons_result = await db.execute(
        select(func.count(Lesson.id))
        .join(Module)
        .where(Module.course_id == course_id)
    )
    total_lessons = total_lessons_result.scalar()
    
    # Get completed lessons
    completed_lessons_result = await db.execute(
        select(func.count(LessonProgress.id))
        .join(Lesson)
        .join(Module)
        .where(
            and_(
                Module.course_id == course_id,
                LessonProgress.user_id == current_user.id,
                LessonProgress.is_completed == True
            )
        )
    )
    completed_lessons = completed_lessons_result.scalar()
    
    # Calculate progress
    progress_percentage = (
        (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0
    )
    
    return CourseProgress(
        enrollment_id=enrollment.id,
        course_id=course_id,
        user_id=current_user.id,
        total_lessons=total_lessons,
        completed_lessons=completed_lessons,
        progress_percentage=progress_percentage,
        enrolled_at=enrollment.enrolled_at,
        completed_at=enrollment.completed_at,
        certificate_issued=enrollment.certificate_issued,
    )