"""Course management routes - simplified implementation."""

from typing import Optional, List, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from sqlalchemy.orm import selectinload

from api.dependencies.auth import get_current_active_user, require_company_admin
from api.dependencies.common import get_db, get_pagination_params
from models.user import User, UserRole
from models.course import Module, Lesson, UserLessonProgress
from schemas.base import PaginatedResponse
from services.course_service import CourseService
from services.quiz_service import QuizService
from services.progress_service import ProgressService
from services.gamification_service import GamificationService
from core.exceptions import NotFoundError, ValidationError, PermissionError
from core.logging import logger

router = APIRouter()


@router.get("/", response_model=List[dict])
async def list_courses(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    pagination: tuple[int, int] = Depends(get_pagination_params),
    search: Optional[str] = Query(None, description="Search in title or description"),
    category: Optional[str] = Query(None, description="Filter by category"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty"),
    is_published: Optional[bool] = Query(True, description="Filter by published status"),
) -> List[dict]:
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
    course_service = CourseService(db)
    
    # Get courses
    courses = await course_service.search_courses(
        search_term=search,
        category=category,
        difficulty=difficulty,
        is_published=is_published,
        limit=limit,
        offset=offset
    )
    
    # Format response
    return [
        {
            "id": course.id,
            "title": course.title,
            "description": course.description,
            "category": course.category,
            "difficulty": course.difficulty_level,
            "duration_hours": course.duration_minutes // 60,
            "is_published": course.is_active,
            "created_at": course.created_at.isoformat(),
            "tags": course.tags,
        }
        for course in courses
    ]


@router.post("/", response_model=dict)
async def create_course(
    course_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_company_admin),
) -> dict:
    """
    Create new course (admin only).
    
    Args:
        course_data: Course creation data
        db: Database session
        current_user: Current authenticated user (must be admin)
        
    Returns:
        Created course
    """
    course_service = CourseService(db)
    
    try:
        # Create course
        course = await course_service.create_course(
            title=course_data.get("title"),
            description=course_data.get("description", ""),
            category=course_data.get("category"),
            difficulty=course_data.get("difficulty", "beginner"),
            duration_hours=course_data.get("duration_hours", 1),
            created_by_id=current_user.id,
            is_published=course_data.get("is_published", False),
            tags=course_data.get("tags", []),
            prerequisites=course_data.get("prerequisites", [])
        )
        
        return {
            "id": course.id,
            "title": course.title,
            "description": course.description,
            "category": course.category,
            "difficulty": course.difficulty_level,
            "duration_hours": course.duration_minutes // 60,
            "is_published": course.is_active,
            "created_at": course.created_at.isoformat(),
            "tags": course.tags,
            "prerequisites": course.prerequisites
        }
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{course_id}", response_model=dict)
async def get_course(
    course_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
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
    course_service = CourseService(db)
    progress_service = ProgressService(db)
    
    # Get course
    course = await course_service.get_course(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
        
    # Check if course is published or user is admin
    if not course.is_active and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Course is not published")
        
    # Get user's progress if enrolled
    user_progress = await progress_service.get_user_course_progress(
        current_user.id, course_id
    )
    
    # Get modules with lessons
    modules = []
    for module in course.modules:
        lessons = [
            {
                "id": lesson.id,
                "title": lesson.title,
                "description": lesson.description,
                "content_type": lesson.content_type,
                "duration_minutes": lesson.duration_minutes,
                "order_index": lesson.order_index,
                "is_required": lesson.is_required
            }
            for lesson in module.lessons if lesson.is_active
        ]
        
        modules.append({
            "id": module.id,
            "title": module.title,
            "description": module.description,
            "order_index": module.order_index,
            "duration_minutes": module.duration_minutes,
            "lessons": lessons,
            "lesson_count": len(lessons)
        })
    
    return {
        "id": course.id,
        "title": course.title,
        "description": course.description,
        "category": course.category,
        "difficulty": course.difficulty_level,
        "duration_hours": course.duration_minutes // 60,
        "is_published": course.is_active,
        "tags": course.tags,
        "prerequisites": course.prerequisites,
        "modules": modules,
        "has_quiz": course.has_quiz,
        "enrolled": user_progress is not None,
        "progress": {
            "status": user_progress.status if user_progress else "not_enrolled",
            "percentage": user_progress.progress_percentage if user_progress else 0,
            "completed_at": user_progress.completed_at.isoformat() if user_progress and user_progress.completed_at else None
        } if user_progress else None
    }


@router.patch("/{course_id}", response_model=dict)
async def update_course(
    course_id: UUID,
    course_update: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_company_admin),
) -> dict:
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
    course_service = CourseService(db)
    
    try:
        # Update course
        course = await course_service.update_course(course_id, course_update)
        
        return {
            "id": course.id,
            "title": course.title,
            "description": course.description,
            "category": course.category,
            "difficulty": course.difficulty_level,
            "duration_hours": course.duration_minutes // 60,
            "is_published": course.is_active,
            "updated_at": course.updated_at.isoformat(),
            "tags": course.tags
        }
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Course not found")
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


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
    course_service = CourseService(db)
    
    try:
        await course_service.delete_course(course_id)
        return {"message": "Course deleted successfully"}
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Course not found")


@router.post("/{course_id}/modules", response_model=dict)
async def create_module(
    course_id: UUID,
    module_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_company_admin),
) -> dict:
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
    course_service = CourseService(db)
    
    # Verify course exists
    course = await course_service.get_course(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
        
    # Create module
    module = Module(
        course_id=course_id,
        title=module_data.get("title"),
        description=module_data.get("description", ""),
        order_index=module_data.get("order_index", 0),
        duration_minutes=module_data.get("duration_minutes", 30),
        is_required=module_data.get("is_required", True)
    )
    
    db.add(module)
    await db.commit()
    await db.refresh(module)
    
    return {
        "id": module.id,
        "course_id": module.course_id,
        "title": module.title,
        "description": module.description,
        "order_index": module.order_index,
        "duration_minutes": module.duration_minutes,
        "is_required": module.is_required,
        "created_at": module.created_at.isoformat()
    }


@router.post("/{course_id}/modules/{module_id}/lessons", response_model=dict)
async def create_lesson(
    course_id: UUID,
    module_id: UUID,
    lesson_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_company_admin),
) -> dict:
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
    # Verify module exists
    result = await db.execute(
        select(Module).where(
            and_(
                Module.id == module_id,
                Module.course_id == course_id
            )
        )
    )
    module = result.scalar_one_or_none()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
        
    # Create lesson
    lesson = Lesson(
        module_id=module_id,
        title=lesson_data.get("title"),
        description=lesson_data.get("description", ""),
        content_type=lesson_data.get("content_type", "text"),
        content_url=lesson_data.get("content_url"),
        content_markdown=lesson_data.get("content_markdown"),
        order_index=lesson_data.get("order_index", 0),
        duration_minutes=lesson_data.get("duration_minutes", 10),
        interactive_elements=lesson_data.get("interactive_elements"),
        resources=lesson_data.get("resources"),
        is_required=lesson_data.get("is_required", True)
    )
    
    db.add(lesson)
    await db.commit()
    await db.refresh(lesson)
    
    return {
        "id": lesson.id,
        "module_id": lesson.module_id,
        "title": lesson.title,
        "description": lesson.description,
        "content_type": lesson.content_type,
        "order_index": lesson.order_index,
        "duration_minutes": lesson.duration_minutes,
        "is_required": lesson.is_required,
        "created_at": lesson.created_at.isoformat()
    }


@router.get("/{course_id}/progress", response_model=dict)
async def get_course_progress(
    course_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
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
    progress_service = ProgressService(db)
    
    # Get user's progress
    progress = await progress_service.get_user_course_progress(
        current_user.id, course_id
    )
    
    if not progress:
        raise HTTPException(
            status_code=403,
            detail="You are not enrolled in this course"
        )
        
    # Get detailed analytics
    analytics = await progress_service.get_course_analytics(course_id)
    user_analytics = await progress_service.get_user_analytics(current_user.id)
    
    # Count lessons
    lesson_count_result = await db.execute(
        select(func.count(Lesson.id))
        .join(Module, Lesson.module_id == Module.id)
        .where(Module.course_id == course_id)
    )
    total_lessons = lesson_count_result.scalar() or 0
    
    completed_lessons_result = await db.execute(
        select(func.count(UserLessonProgress.id))
        .where(
            and_(
                UserLessonProgress.user_id == current_user.id,
                UserLessonProgress.course_id == course_id,
                UserLessonProgress.status == 'completed'
            )
        )
    )
    completed_lessons = completed_lessons_result.scalar() or 0
    
    return {
        "enrollment_id": progress.id,
        "course_id": course_id,
        "user_id": current_user.id,
        "status": progress.status,
        "total_lessons": total_lessons,
        "completed_lessons": completed_lessons,
        "progress_percentage": progress.progress_percentage,
        "enrolled_at": progress.created_at.isoformat(),
        "started_at": progress.started_at.isoformat() if progress.started_at else None,
        "completed_at": progress.completed_at.isoformat() if progress.completed_at else None,
        "certificate_issued": progress.certificate_issued,
        "certificate_url": progress.certificate_url,
        "time_spent_hours": user_analytics.get("total_time_hours", 0),
        "current_streak_days": user_analytics.get("current_streak_days", 0)
    }


@router.post("/{course_id}/enroll", response_model=dict)
async def enroll_in_course(
    course_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Enroll current user in a course.
    
    Args:
        course_id: Course ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Enrollment details
        
    Raises:
        HTTPException: If course not found or already enrolled
    """
    progress_service = ProgressService(db)
    
    try:
        # Enroll user
        progress = await progress_service.enroll_user(
            user_id=current_user.id,
            course_id=course_id,
            company_id=current_user.company_id
        )
        
        return {
            "enrollment_id": progress.id,
            "course_id": course_id,
            "user_id": current_user.id,
            "status": progress.status,
            "enrolled_at": progress.created_at.isoformat(),
            "message": "Successfully enrolled in course"
        }
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Enrollment error: {str(e)}")
        raise HTTPException(status_code=500, detail="Enrollment failed")


@router.post("/{course_id}/lessons/{lesson_id}/progress", response_model=dict)
async def update_lesson_progress(
    course_id: UUID,
    lesson_id: UUID,
    progress_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Update progress for a specific lesson.
    
    Args:
        course_id: Course ID
        lesson_id: Lesson ID
        progress_data: Progress update data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Updated progress details
    """
    progress_service = ProgressService(db)
    
    try:
        # Update lesson progress
        lesson_progress = await progress_service.update_lesson_progress(
            user_id=current_user.id,
            lesson_id=lesson_id,
            progress_data=progress_data
        )
        
        return {
            "lesson_id": lesson_id,
            "status": lesson_progress.status,
            "progress_percentage": lesson_progress.progress_percentage,
            "time_spent_seconds": lesson_progress.time_spent_seconds,
            "completed": lesson_progress.status == "completed",
            "last_accessed_at": lesson_progress.last_accessed_at.isoformat()
        }
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Lesson not found")
    except Exception as e:
        logger.error(f"Progress update error: {str(e)}")
        raise HTTPException(status_code=500, detail="Progress update failed")


@router.get("/{course_id}/quiz", response_model=dict)
async def get_course_quiz(
    course_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Get quiz for a course (without correct answers).
    
    Args:
        course_id: Course ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Quiz details with questions
        
    Raises:
        HTTPException: If not enrolled or quiz not found
    """
    quiz_service = QuizService(db)
    progress_service = ProgressService(db)
    
    # Check enrollment
    progress = await progress_service.get_user_course_progress(
        current_user.id, course_id
    )
    if not progress:
        raise HTTPException(
            status_code=403,
            detail="You must be enrolled in the course to access the quiz"
        )
        
    # Get quiz
    quiz = await quiz_service.get_course_quiz(course_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="This course has no quiz")
        
    # Format questions without correct answers
    questions = []
    for q in quiz.questions:
        question_data = {
            "id": q.id,
            "question_text": q.question_text,
            "question_type": q.question_type,
            "points": q.points,
            "order_index": q.order_index
        }
        
        if q.question_type == "multiple_choice":
            question_data["options"] = q.options
            
        questions.append(question_data)
        
    return {
        "quiz_id": quiz.id,
        "title": quiz.title,
        "passing_score": quiz.passing_score,
        "time_limit_minutes": quiz.time_limit_minutes,
        "max_attempts": quiz.max_attempts,
        "total_points": quiz.total_points,
        "question_count": quiz.question_count,
        "questions": questions
    }


@router.post("/{course_id}/quiz/submit", response_model=dict)
async def submit_quiz(
    course_id: UUID,
    answers: dict = Body(..., description="Quiz answers {question_id: answer}"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Submit quiz answers and get results.
    
    Args:
        course_id: Course ID
        answers: Dictionary of question_id to answer
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Quiz results with score and feedback
    """
    quiz_service = QuizService(db)
    gamification_service = GamificationService(db)
    
    # Get quiz
    quiz = await quiz_service.get_course_quiz(course_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
        
    try:
        # Submit quiz
        result = await quiz_service.submit_quiz(
            user_id=current_user.id,
            quiz_id=quiz.id,
            answers=answers
        )
        
        # Award gamification points if passed
        if result["passed"]:
            points_result = await gamification_service.award_points(
                user_id=current_user.id,
                points=gamification_service.POINTS_CONFIG["course_completion"],
                reason=f"Completed course: {course_id}",
                context={"course_id": course_id, "score": result["score"]}
            )
            
            result["gamification"] = points_result
            
        return result
        
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Quiz submission error: {str(e)}")
        raise HTTPException(status_code=500, detail="Quiz submission failed")


@router.get("/my-courses", response_model=List[dict])
async def get_my_courses(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    status: Optional[str] = Query(None, description="Filter by status"),
) -> List[dict]:
    """
    Get all courses the current user is enrolled in.
    
    Args:
        db: Database session
        current_user: Current authenticated user
        status: Optional status filter
        
    Returns:
        List of enrolled courses with progress
    """
    progress_service = ProgressService(db)
    
    # Get enrolled courses
    enrollments = await progress_service.get_user_enrolled_courses(
        current_user.id, status
    )
    
    courses = []
    for enrollment in enrollments:
        course = enrollment.course
        courses.append({
            "id": course.id,
            "title": course.title,
            "description": course.description,
            "category": course.category,
            "difficulty": course.difficulty_level,
            "duration_hours": course.duration_minutes // 60,
            "enrollment": {
                "status": enrollment.status,
                "progress_percentage": enrollment.progress_percentage,
                "enrolled_at": enrollment.created_at.isoformat(),
                "started_at": enrollment.started_at.isoformat() if enrollment.started_at else None,
                "completed_at": enrollment.completed_at.isoformat() if enrollment.completed_at else None,
                "certificate_issued": enrollment.certificate_issued
            }
        })
        
    return courses


@router.get("/gamification/my-stats", response_model=dict)
async def get_my_gamification_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Get current user's gamification statistics.
    
    Args:
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Gamification stats including points, level, badges
    """
    gamification_service = GamificationService(db)
    
    stats = await gamification_service.get_user_stats(current_user.id)
    badges = await gamification_service.get_user_badges(current_user.id)
    
    stats["badges"] = badges
    
    return stats


@router.get("/gamification/leaderboard", response_model=List[dict])
async def get_leaderboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    scope: str = Query("company", description="Leaderboard scope: company or global"),
    limit: int = Query(10, ge=1, le=100),
) -> List[dict]:
    """
    Get gamification leaderboard.
    
    Args:
        db: Database session
        current_user: Current authenticated user
        scope: Leaderboard scope (company or global)
        limit: Number of top users to return
        
    Returns:
        List of top users with points and stats
    """
    gamification_service = GamificationService(db)
    
    company_id = current_user.company_id if scope == "company" else None
    
    leaderboard = await gamification_service.get_leaderboard(
        company_id=company_id,
        limit=limit
    )
    
    return leaderboard


@router.get("/certificates/{certificate_id}", response_model=dict)
async def get_certificate(
    certificate_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Get certificate details.
    
    Args:
        certificate_id: Certificate ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Certificate details
        
    Raises:
        HTTPException: If certificate not found or no access
    """
    from models.course import Certificate
    
    # Get certificate
    result = await db.execute(
        select(Certificate)
        .where(Certificate.id == certificate_id)
        .options(
            selectinload(Certificate.user),
            selectinload(Certificate.course)
        )
    )
    certificate = result.scalar_one_or_none()
    
    if not certificate:
        raise HTTPException(status_code=404, detail="Certificate not found")
        
    # Check access (owner or admin)
    if certificate.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")
        
    return {
        "id": certificate.id,
        "certificate_number": certificate.certificate_number,
        "verification_code": certificate.verification_code,
        "user": {
            "id": certificate.user.id,
            "name": certificate.user.full_name
        },
        "course": {
            "id": certificate.course.id,
            "title": certificate.course.title
        },
        "issued_at": certificate.issued_at.isoformat(),
        "expires_at": certificate.expires_at.isoformat() if certificate.expires_at else None,
        "completion_date": certificate.completion_date.isoformat(),
        "final_score": certificate.final_score,
        "time_spent_hours": certificate.time_spent_hours,
        "is_valid": certificate.is_valid(),
        "pdf_url": certificate.pdf_url
    }