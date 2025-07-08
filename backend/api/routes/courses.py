"""Course management API routes."""

from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import and_, or_, func

from backend.core.auth import get_current_active_user
from backend.core.database import get_db
from backend.models import (
    User, UserRole, Course, Module, Lesson, CourseContent,
    CourseEnrollment, ModuleProgress, LessonProgress,
    CourseStatus, ProgressStatus
)
from backend.schemas.course import (
    CourseCreate, CourseUpdate, CoursePublic, CourseDetail,
    ModuleCreate, ModuleUpdate, ModulePublic,
    LessonCreate, LessonUpdate, LessonPublic, LessonDetail,
    CourseContentCreate, CourseContentUpdate, CourseContentInDB,
    CourseEnrollmentCreate, CourseEnrollmentPublic,
    CourseProgressSummary
)

router = APIRouter()


# Helper functions
def check_admin_or_instructor(current_user: User) -> None:
    """Check if user is admin or instructor."""
    if current_user.role not in [UserRole.ADMIN, UserRole.INSTRUCTOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )


def get_course_or_404(db: Session, course_id: int) -> Course:
    """Get course by ID or raise 404."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    return course


def get_module_or_404(db: Session, module_id: int) -> Module:
    """Get module by ID or raise 404."""
    module = db.query(Module).filter(Module.id == module_id).first()
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found"
        )
    return module


def get_lesson_or_404(db: Session, lesson_id: int) -> Lesson:
    """Get lesson by ID or raise 404."""
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )
    return lesson


def get_enrollment_or_none(
    db: Session,
    user_id: int,
    course_id: int
) -> Optional[CourseEnrollment]:
    """Get enrollment for user and course."""
    return db.query(CourseEnrollment).filter(
        and_(
            CourseEnrollment.user_id == user_id,
            CourseEnrollment.course_id == course_id
        )
    ).first()


# Course endpoints
@router.get("/", response_model=List[CoursePublic])
def list_courses(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    language: Optional[str] = None,
    difficulty: Optional[str] = None,
    search: Optional[str] = None,
    only_enrolled: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List available courses with filters."""
    query = db.query(Course).filter(
        Course.status == CourseStatus.PUBLISHED
    )
    
    # Apply filters
    if category:
        query = query.filter(Course.category == category)
    if language:
        query = query.filter(Course.language == language)
    if difficulty:
        query = query.filter(Course.difficulty_level == difficulty)
    if search:
        query = query.filter(
            or_(
                Course.title.ilike(f"%{search}%"),
                Course.description.ilike(f"%{search}%"),
                Course.tags.any(search)
            )
        )
    
    # Filter by enrollment
    if only_enrolled:
        query = query.join(CourseEnrollment).filter(
            CourseEnrollment.user_id == current_user.id
        )
    
    # Order by popularity and recency
    query = query.order_by(
        Course.enrolled_count.desc(),
        Course.published_at.desc()
    )
    
    courses = query.offset(skip).limit(limit).all()
    return courses


@router.post("/", response_model=CoursePublic)
def create_course(
    course_in: CourseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new course (admin/instructor only)."""
    check_admin_or_instructor(current_user)
    
    # Check if slug is unique
    existing = db.query(Course).filter(Course.slug == course_in.slug).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Course with this slug already exists"
        )
    
    # Create course
    course = Course(**course_in.model_dump())
    course.created_by_id = current_user.id
    
    db.add(course)
    db.commit()
    db.refresh(course)
    
    return course


@router.get("/{course_id}", response_model=CourseDetail)
def get_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get course details with modules and enrollment status."""
    course = get_course_or_404(db, course_id)
    
    # Load modules with lessons
    course = db.query(Course).options(
        joinedload(Course.modules).joinedload(Module.lessons)
    ).filter(Course.id == course_id).first()
    
    # Get enrollment status
    enrollment = get_enrollment_or_none(db, current_user.id, course_id)
    
    # Check if user can enroll
    can_enroll = True
    enrollment_message = None
    
    if enrollment:
        can_enroll = False
        enrollment_message = "Already enrolled"
    elif course.is_free:
        can_enroll = True
    else:
        # Check if user's company has access
        # TODO: Implement subscription checks
        can_enroll = True
    
    # Prepare response
    course_dict = course.__dict__.copy()
    course_dict["enrollment_status"] = CourseEnrollmentPublic.model_validate(enrollment) if enrollment else None
    course_dict["can_enroll"] = can_enroll
    course_dict["enrollment_message"] = enrollment_message
    
    # Add progress info to modules and lessons if enrolled
    if enrollment:
        for module in course.modules:
            module_progress = db.query(ModuleProgress).filter(
                and_(
                    ModuleProgress.enrollment_id == enrollment.id,
                    ModuleProgress.module_id == module.id
                )
            ).first()
            module.progress = module_progress
            
            for lesson in module.lessons:
                lesson_progress = db.query(LessonProgress).filter(
                    and_(
                        LessonProgress.enrollment_id == enrollment.id,
                        LessonProgress.lesson_id == lesson.id
                    )
                ).first()
                lesson.progress = lesson_progress
                lesson.is_completed = lesson_progress and lesson_progress.status == ProgressStatus.COMPLETED
                lesson.is_locked = False  # TODO: Implement prerequisite logic
                lesson.has_quiz = bool(lesson.quiz)
    
    return CourseDetail.model_validate(course_dict)


@router.put("/{course_id}", response_model=CoursePublic)
def update_course(
    course_id: int,
    course_in: CourseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update course details (admin/instructor only)."""
    check_admin_or_instructor(current_user)
    
    course = get_course_or_404(db, course_id)
    
    # Update fields
    update_data = course_in.model_dump(exclude_unset=True)
    
    # Handle status changes
    if "status" in update_data and update_data["status"] == CourseStatus.PUBLISHED:
        if not course.published_at:
            update_data["published_at"] = datetime.utcnow()
    
    for field, value in update_data.items():
        setattr(course, field, value)
    
    course.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(course)
    
    return course


@router.delete("/{course_id}")
def delete_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a course (admin only)."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete courses"
        )
    
    course = get_course_or_404(db, course_id)
    
    # Check if course has enrollments
    enrollment_count = db.query(CourseEnrollment).filter(
        CourseEnrollment.course_id == course_id
    ).count()
    
    if enrollment_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete course with {enrollment_count} enrollments"
        )
    
    db.delete(course)
    db.commit()
    
    return {"message": "Course deleted successfully"}


# Module endpoints
@router.post("/{course_id}/modules", response_model=ModulePublic)
def create_module(
    course_id: int,
    module_in: ModuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new module in a course (admin/instructor only)."""
    check_admin_or_instructor(current_user)
    
    course = get_course_or_404(db, course_id)
    
    # Check if slug is unique within course
    existing = db.query(Module).filter(
        and_(
            Module.course_id == course_id,
            Module.slug == module_in.slug
        )
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Module with this slug already exists in the course"
        )
    
    # Create module
    module = Module(**module_in.model_dump())
    module.course_id = course_id
    
    # Update course duration
    course.duration_minutes += module.duration_minutes
    
    db.add(module)
    db.commit()
    db.refresh(module)
    
    return module


@router.put("/modules/{module_id}", response_model=ModulePublic)
def update_module(
    module_id: int,
    module_in: ModuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update module details (admin/instructor only)."""
    check_admin_or_instructor(current_user)
    
    module = get_module_or_404(db, module_id)
    
    # Update fields
    update_data = module_in.model_dump(exclude_unset=True)
    
    # Update course duration if module duration changed
    if "duration_minutes" in update_data:
        course = module.course
        duration_diff = update_data["duration_minutes"] - module.duration_minutes
        course.duration_minutes += duration_diff
    
    for field, value in update_data.items():
        setattr(module, field, value)
    
    module.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(module)
    
    return module


@router.delete("/modules/{module_id}")
def delete_module(
    module_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a module (admin/instructor only)."""
    check_admin_or_instructor(current_user)
    
    module = get_module_or_404(db, module_id)
    
    # Update course duration
    course = module.course
    course.duration_minutes -= module.duration_minutes
    
    # Reorder remaining modules
    db.query(Module).filter(
        and_(
            Module.course_id == module.course_id,
            Module.order_index > module.order_index
        )
    ).update({"order_index": Module.order_index - 1})
    
    db.delete(module)
    db.commit()
    
    return {"message": "Module deleted successfully"}


# Lesson endpoints
@router.post("/modules/{module_id}/lessons", response_model=LessonPublic)
def create_lesson(
    module_id: int,
    lesson_in: LessonCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new lesson in a module (admin/instructor only)."""
    check_admin_or_instructor(current_user)
    
    module = get_module_or_404(db, module_id)
    
    # Check if slug is unique within module
    existing = db.query(Lesson).filter(
        and_(
            Lesson.module_id == module_id,
            Lesson.slug == lesson_in.slug
        )
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lesson with this slug already exists in the module"
        )
    
    # Create lesson
    lesson = Lesson(**lesson_in.model_dump())
    lesson.module_id = module_id
    
    # Update module and course duration
    module.duration_minutes += lesson.duration_minutes
    module.course.duration_minutes += lesson.duration_minutes
    
    # Update lesson counts for enrollments
    db.query(CourseEnrollment).filter(
        CourseEnrollment.course_id == module.course_id
    ).update({"lessons_total": CourseEnrollment.lessons_total + 1})
    
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    
    return lesson


@router.get("/lessons/{lesson_id}", response_model=LessonDetail)
def get_lesson(
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get lesson details with content."""
    lesson = get_lesson_or_404(db, lesson_id)
    
    # Check if user has access
    module = lesson.module
    course = module.course
    
    enrollment = get_enrollment_or_none(db, current_user.id, course.id)
    
    if not lesson.is_preview and not enrollment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Enrollment required to access this lesson"
        )
    
    # Load content and quiz
    lesson = db.query(Lesson).options(
        joinedload(Lesson.content_items),
        joinedload(Lesson.quiz)
    ).filter(Lesson.id == lesson_id).first()
    
    # Get progress if enrolled
    if enrollment:
        lesson_progress = db.query(LessonProgress).filter(
            and_(
                LessonProgress.enrollment_id == enrollment.id,
                LessonProgress.lesson_id == lesson_id
            )
        ).first()
        lesson.progress = lesson_progress
    
    # Get next and previous lessons
    next_lesson = db.query(Lesson).filter(
        and_(
            Lesson.module_id == module.id,
            Lesson.order_index == lesson.order_index + 1
        )
    ).first()
    
    if not next_lesson and module.order_index < db.query(func.max(Module.order_index)).filter(
        Module.course_id == course.id
    ).scalar():
        # Get first lesson of next module
        next_module = db.query(Module).filter(
            and_(
                Module.course_id == course.id,
                Module.order_index == module.order_index + 1
            )
        ).first()
        if next_module:
            next_lesson = db.query(Lesson).filter(
                and_(
                    Lesson.module_id == next_module.id,
                    Lesson.order_index == 0
                )
            ).first()
    
    previous_lesson = db.query(Lesson).filter(
        and_(
            Lesson.module_id == module.id,
            Lesson.order_index == lesson.order_index - 1
        )
    ).first()
    
    if not previous_lesson and module.order_index > 0:
        # Get last lesson of previous module
        previous_module = db.query(Module).filter(
            and_(
                Module.course_id == course.id,
                Module.order_index == module.order_index - 1
            )
        ).first()
        if previous_module:
            max_order = db.query(func.max(Lesson.order_index)).filter(
                Lesson.module_id == previous_module.id
            ).scalar()
            if max_order is not None:
                previous_lesson = db.query(Lesson).filter(
                    and_(
                        Lesson.module_id == previous_module.id,
                        Lesson.order_index == max_order
                    )
                ).first()
    
    # Prepare response
    lesson_dict = lesson.__dict__.copy()
    lesson_dict["next_lesson"] = LessonPublic.model_validate(next_lesson) if next_lesson else None
    lesson_dict["previous_lesson"] = LessonPublic.model_validate(previous_lesson) if previous_lesson else None
    
    return LessonDetail.model_validate(lesson_dict)


@router.put("/lessons/{lesson_id}", response_model=LessonPublic)
def update_lesson(
    lesson_id: int,
    lesson_in: LessonUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update lesson details (admin/instructor only)."""
    check_admin_or_instructor(current_user)
    
    lesson = get_lesson_or_404(db, lesson_id)
    
    # Update fields
    update_data = lesson_in.model_dump(exclude_unset=True)
    
    # Update durations if changed
    if "duration_minutes" in update_data:
        module = lesson.module
        course = module.course
        duration_diff = update_data["duration_minutes"] - lesson.duration_minutes
        module.duration_minutes += duration_diff
        course.duration_minutes += duration_diff
    
    for field, value in update_data.items():
        setattr(lesson, field, value)
    
    lesson.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(lesson)
    
    return lesson


@router.delete("/lessons/{lesson_id}")
def delete_lesson(
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a lesson (admin/instructor only)."""
    check_admin_or_instructor(current_user)
    
    lesson = get_lesson_or_404(db, lesson_id)
    
    # Update durations
    module = lesson.module
    course = module.course
    module.duration_minutes -= lesson.duration_minutes
    course.duration_minutes -= lesson.duration_minutes
    
    # Update lesson counts for enrollments
    db.query(CourseEnrollment).filter(
        CourseEnrollment.course_id == course.id
    ).update({"lessons_total": CourseEnrollment.lessons_total - 1})
    
    # Reorder remaining lessons
    db.query(Lesson).filter(
        and_(
            Lesson.module_id == module.id,
            Lesson.order_index > lesson.order_index
        )
    ).update({"order_index": Lesson.order_index - 1})
    
    db.delete(lesson)
    db.commit()
    
    return {"message": "Lesson deleted successfully"}


# Content endpoints
@router.post("/lessons/{lesson_id}/content", response_model=CourseContentInDB)
def create_content(
    lesson_id: int,
    content_in: CourseContentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Add content to a lesson (admin/instructor only)."""
    check_admin_or_instructor(current_user)
    
    lesson = get_lesson_or_404(db, lesson_id)
    
    # Create content
    content = CourseContent(**content_in.model_dump())
    content.lesson_id = lesson_id
    
    db.add(content)
    db.commit()
    db.refresh(content)
    
    return content


@router.put("/content/{content_id}", response_model=CourseContentInDB)
def update_content(
    content_id: int,
    content_in: CourseContentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update content details (admin/instructor only)."""
    check_admin_or_instructor(current_user)
    
    content = db.query(CourseContent).filter(CourseContent.id == content_id).first()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    
    # Update fields
    update_data = content_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(content, field, value)
    
    content.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(content)
    
    return content


@router.delete("/content/{content_id}")
def delete_content(
    content_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete content (admin/instructor only)."""
    check_admin_or_instructor(current_user)
    
    content = db.query(CourseContent).filter(CourseContent.id == content_id).first()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    
    # Reorder remaining content
    db.query(CourseContent).filter(
        and_(
            CourseContent.lesson_id == content.lesson_id,
            CourseContent.order_index > content.order_index
        )
    ).update({"order_index": CourseContent.order_index - 1})
    
    db.delete(content)
    db.commit()
    
    return {"message": "Content deleted successfully"}


# Categories endpoint
@router.get("/categories/")
def get_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get list of available course categories with counts."""
    categories = db.query(
        Course.category,
        func.count(Course.id).label("count")
    ).filter(
        Course.status == CourseStatus.PUBLISHED
    ).group_by(Course.category).all()
    
    return [
        {"category": cat, "count": count}
        for cat, count in categories
    ]