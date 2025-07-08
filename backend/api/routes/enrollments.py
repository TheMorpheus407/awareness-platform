"""Course enrollment and progress tracking API routes."""

from typing import List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func

from backend.core.auth import get_current_active_user
from backend.core.database import get_db
from backend.models import (
    User, Course, Module, Lesson, CourseEnrollment,
    ModuleProgress, LessonProgress, CourseStatus, ProgressStatus
)
from backend.schemas.course import (
    CourseEnrollmentCreate, CourseEnrollmentPublic,
    CourseProgressSummary, LessonProgressUpdate,
    LessonProgressInDB, ModuleProgressInDB
)

router = APIRouter()


# Helper functions
def get_course_or_404(db: Session, course_id: int) -> Course:
    """Get course by ID or raise 404."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    return course


def get_enrollment_or_404(
    db: Session,
    user_id: int,
    course_id: int
) -> CourseEnrollment:
    """Get enrollment or raise 404."""
    enrollment = db.query(CourseEnrollment).filter(
        and_(
            CourseEnrollment.user_id == user_id,
            CourseEnrollment.course_id == course_id
        )
    ).first()
    
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enrollment not found"
        )
    
    return enrollment


def calculate_module_progress(
    db: Session,
    enrollment_id: int,
    module_id: int
) -> None:
    """Calculate and update module progress based on lesson progress."""
    # Get all lessons in module
    lessons = db.query(Lesson).filter(Lesson.module_id == module_id).all()
    if not lessons:
        return
    
    # Get lesson progress
    lesson_progress_list = db.query(LessonProgress).filter(
        and_(
            LessonProgress.enrollment_id == enrollment_id,
            LessonProgress.lesson_id.in_([l.id for l in lessons])
        )
    ).all()
    
    # Calculate progress
    total_lessons = len(lessons)
    completed_lessons = sum(
        1 for lp in lesson_progress_list
        if lp.status == ProgressStatus.COMPLETED
    )
    progress_percentage = (completed_lessons / total_lessons) * 100
    
    # Update or create module progress
    module_progress = db.query(ModuleProgress).filter(
        and_(
            ModuleProgress.enrollment_id == enrollment_id,
            ModuleProgress.module_id == module_id
        )
    ).first()
    
    if not module_progress:
        module_progress = ModuleProgress(
            enrollment_id=enrollment_id,
            module_id=module_id,
            lessons_total=total_lessons
        )
        db.add(module_progress)
    
    module_progress.lessons_completed = completed_lessons
    module_progress.progress_percentage = progress_percentage
    
    # Update status
    if completed_lessons == 0:
        module_progress.status = ProgressStatus.NOT_STARTED
    elif completed_lessons < total_lessons:
        module_progress.status = ProgressStatus.IN_PROGRESS
        if not module_progress.started_at:
            module_progress.started_at = datetime.utcnow()
    else:
        module_progress.status = ProgressStatus.COMPLETED
        if not module_progress.completed_at:
            module_progress.completed_at = datetime.utcnow()
    
    # Update time spent
    total_time = sum(lp.time_spent_seconds for lp in lesson_progress_list)
    module_progress.time_spent_seconds = total_time


def calculate_course_progress(
    db: Session,
    enrollment: CourseEnrollment
) -> None:
    """Calculate and update course progress based on module progress."""
    # Get all modules in course
    modules = db.query(Module).filter(Module.course_id == enrollment.course_id).all()
    if not modules:
        return
    
    # Get all lessons in course
    lesson_count = db.query(func.count(Lesson.id)).join(Module).filter(
        Module.course_id == enrollment.course_id
    ).scalar() or 0
    
    # Get completed lessons
    completed_lessons = db.query(func.count(LessonProgress.id)).filter(
        and_(
            LessonProgress.enrollment_id == enrollment.id,
            LessonProgress.status == ProgressStatus.COMPLETED
        )
    ).scalar() or 0
    
    # Update enrollment
    enrollment.lessons_total = lesson_count
    enrollment.lessons_completed = completed_lessons
    enrollment.progress_percentage = (completed_lessons / lesson_count * 100) if lesson_count > 0 else 0
    
    # Update status
    if completed_lessons == 0:
        enrollment.status = ProgressStatus.NOT_STARTED
    elif completed_lessons < lesson_count:
        enrollment.status = ProgressStatus.IN_PROGRESS
    else:
        enrollment.status = ProgressStatus.COMPLETED
        if not enrollment.completed_at:
            enrollment.completed_at = datetime.utcnow()
            
            # Generate certificate if course has validity days
            course = enrollment.course
            if course.validity_days:
                enrollment.certificate_issued_at = datetime.utcnow()
                enrollment.certificate_expires_at = datetime.utcnow() + timedelta(days=course.validity_days)


# Enrollment endpoints
@router.post("/enroll", response_model=CourseEnrollmentPublic)
def enroll_in_course(
    enrollment_in: CourseEnrollmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Enroll current user in a course."""
    course = get_course_or_404(db, enrollment_in.course_id)
    
    # Check if course is published
    if course.status != CourseStatus.PUBLISHED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Course is not available for enrollment"
        )
    
    # Check if already enrolled
    existing = db.query(CourseEnrollment).filter(
        and_(
            CourseEnrollment.user_id == current_user.id,
            CourseEnrollment.course_id == course.id
        )
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already enrolled in this course"
        )
    
    # Check access rights
    if not course.is_free:
        # TODO: Check subscription/payment
        pass
    
    # Count total lessons
    lesson_count = db.query(func.count(Lesson.id)).join(Module).filter(
        Module.course_id == course.id
    ).scalar() or 0
    
    # Create enrollment
    enrollment = CourseEnrollment(
        user_id=current_user.id,
        course_id=course.id,
        company_id=current_user.company_id,
        lessons_total=lesson_count
    )
    
    # Update course enrollment count
    course.enrolled_count += 1
    
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    
    # Convert to public schema
    enrollment_dict = enrollment.__dict__.copy()
    enrollment_dict["certificate_available"] = False
    
    return CourseEnrollmentPublic.model_validate(enrollment_dict)


@router.get("/enrollments", response_model=List[CourseEnrollmentPublic])
def get_my_enrollments(
    status: Optional[ProgressStatus] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get current user's course enrollments."""
    query = db.query(CourseEnrollment).filter(
        CourseEnrollment.user_id == current_user.id
    )
    
    if status:
        query = query.filter(CourseEnrollment.status == status)
    
    # Order by last accessed
    query = query.order_by(CourseEnrollment.last_accessed_at.desc().nullsfirst())
    
    enrollments = query.offset(skip).limit(limit).all()
    
    # Convert to public schema
    result = []
    for enrollment in enrollments:
        enrollment_dict = enrollment.__dict__.copy()
        enrollment_dict["certificate_available"] = bool(
            enrollment.status == ProgressStatus.COMPLETED and
            enrollment.certificate_issued_at
        )
        enrollment_dict["certificate_id"] = enrollment.completion_certificate_id
        result.append(CourseEnrollmentPublic.model_validate(enrollment_dict))
    
    return result


@router.get("/enrollments/{course_id}", response_model=CourseEnrollmentPublic)
def get_enrollment(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get enrollment details for a specific course."""
    enrollment = get_enrollment_or_404(db, current_user.id, course_id)
    
    enrollment_dict = enrollment.__dict__.copy()
    enrollment_dict["certificate_available"] = bool(
        enrollment.status == ProgressStatus.COMPLETED and
        enrollment.certificate_issued_at
    )
    enrollment_dict["certificate_id"] = enrollment.completion_certificate_id
    
    return CourseEnrollmentPublic.model_validate(enrollment_dict)


@router.get("/enrollments/{course_id}/progress", response_model=CourseProgressSummary)
def get_course_progress(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get detailed progress for a course."""
    enrollment = get_enrollment_or_404(db, current_user.id, course_id)
    
    # Get course with modules
    course = db.query(Course).options(
        joinedload(Course.modules)
    ).filter(Course.id == course_id).first()
    
    # Count completed modules
    modules_total = len(course.modules)
    modules_completed = db.query(func.count(ModuleProgress.id)).filter(
        and_(
            ModuleProgress.enrollment_id == enrollment.id,
            ModuleProgress.status == ProgressStatus.COMPLETED
        )
    ).scalar() or 0
    
    # Get current module and lesson
    current_lesson = db.query(Lesson).join(LessonProgress).filter(
        and_(
            LessonProgress.enrollment_id == enrollment.id,
            LessonProgress.status == ProgressStatus.IN_PROGRESS
        )
    ).order_by(LessonProgress.last_accessed_at.desc()).first()
    
    current_module = None
    if current_lesson:
        current_module = current_lesson.module
    else:
        # Find first incomplete module
        current_module = db.query(Module).join(ModuleProgress).filter(
            and_(
                ModuleProgress.enrollment_id == enrollment.id,
                ModuleProgress.status == ProgressStatus.IN_PROGRESS
            )
        ).order_by(Module.order_index).first()
    
    # Get next lesson
    next_lesson = None
    if current_lesson:
        # Try next lesson in same module
        next_lesson = db.query(Lesson).filter(
            and_(
                Lesson.module_id == current_lesson.module_id,
                Lesson.order_index == current_lesson.order_index + 1
            )
        ).first()
        
        if not next_lesson:
            # Try first lesson of next module
            next_module = db.query(Module).filter(
                and_(
                    Module.course_id == course_id,
                    Module.order_index == current_module.order_index + 1
                )
            ).first()
            if next_module:
                next_lesson = db.query(Lesson).filter(
                    and_(
                        Lesson.module_id == next_module.id,
                        Lesson.order_index == 0
                    )
                ).first()
    
    # Get recent activity
    recent_activity = []
    recent_lessons = db.query(LessonProgress).filter(
        LessonProgress.enrollment_id == enrollment.id
    ).order_by(LessonProgress.updated_at.desc()).limit(5).all()
    
    for lp in recent_lessons:
        lesson = lp.lesson
        recent_activity.append({
            "type": "lesson",
            "lesson_id": lesson.id,
            "lesson_title": lesson.title,
            "module_title": lesson.module.title,
            "status": lp.status,
            "progress_percentage": lp.progress_percentage,
            "updated_at": lp.updated_at
        })
    
    # Prepare enrollment for response
    enrollment_dict = enrollment.__dict__.copy()
    enrollment_dict["certificate_available"] = bool(
        enrollment.status == ProgressStatus.COMPLETED and
        enrollment.certificate_issued_at
    )
    enrollment_dict["certificate_id"] = enrollment.completion_certificate_id
    
    return CourseProgressSummary(
        enrollment=CourseEnrollmentPublic.model_validate(enrollment_dict),
        modules_completed=modules_completed,
        modules_total=modules_total,
        current_module=current_module,
        current_lesson=current_lesson,
        next_lesson=next_lesson,
        recent_activity=recent_activity
    )


# Progress tracking endpoints
@router.post("/lessons/{lesson_id}/progress", response_model=LessonProgressInDB)
def update_lesson_progress(
    lesson_id: int,
    progress_in: LessonProgressUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update progress for a lesson."""
    # Get lesson and check access
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )
    
    # Get enrollment
    course_id = lesson.module.course_id
    enrollment = get_enrollment_or_404(db, current_user.id, course_id)
    
    # Update last accessed
    enrollment.last_accessed_at = datetime.utcnow()
    
    # Get or create lesson progress
    lesson_progress = db.query(LessonProgress).filter(
        and_(
            LessonProgress.enrollment_id == enrollment.id,
            LessonProgress.lesson_id == lesson_id
        )
    ).first()
    
    if not lesson_progress:
        lesson_progress = LessonProgress(
            enrollment_id=enrollment.id,
            lesson_id=lesson_id
        )
        db.add(lesson_progress)
    
    # Update progress
    update_data = progress_in.model_dump(exclude_unset=True)
    
    # Handle status updates
    if "completed" in update_data and update_data["completed"]:
        update_data["status"] = ProgressStatus.COMPLETED
        update_data["progress_percentage"] = 100.0
        if not lesson_progress.completed_at:
            update_data["completed_at"] = datetime.utcnow()
        del update_data["completed"]
    
    if "status" in update_data:
        if update_data["status"] == ProgressStatus.IN_PROGRESS and not lesson_progress.started_at:
            update_data["started_at"] = datetime.utcnow()
        elif update_data["status"] == ProgressStatus.COMPLETED and not lesson_progress.completed_at:
            update_data["completed_at"] = datetime.utcnow()
            update_data["progress_percentage"] = 100.0
    
    # Update fields
    for field, value in update_data.items():
        setattr(lesson_progress, field, value)
    
    # Increment view count
    lesson_progress.view_count += 1
    
    # Update time spent (this would normally come from frontend tracking)
    if "last_position_seconds" in update_data and lesson_progress.last_position_seconds:
        time_diff = update_data["last_position_seconds"] - (lesson_progress.last_position_seconds or 0)
        if time_diff > 0:
            lesson_progress.time_spent_seconds += time_diff
    
    # Save lesson progress
    db.commit()
    db.refresh(lesson_progress)
    
    # Update module progress
    calculate_module_progress(db, enrollment.id, lesson.module_id)
    
    # Update course progress
    calculate_course_progress(db, enrollment)
    
    # Update enrollment time spent
    total_time = db.query(func.sum(LessonProgress.time_spent_seconds)).filter(
        LessonProgress.enrollment_id == enrollment.id
    ).scalar() or 0
    enrollment.time_spent_seconds = total_time
    
    db.commit()
    
    return lesson_progress


@router.post("/lessons/{lesson_id}/complete")
def mark_lesson_complete(
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Mark a lesson as completed."""
    progress_update = LessonProgressUpdate(
        status=ProgressStatus.COMPLETED,
        progress_percentage=100.0,
        completed=True
    )
    
    lesson_progress = update_lesson_progress(
        lesson_id=lesson_id,
        progress_in=progress_update,
        db=db,
        current_user=current_user
    )
    
    return {"message": "Lesson marked as completed", "progress": lesson_progress}


@router.delete("/enrollments/{course_id}")
def unenroll_from_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Unenroll from a course (if allowed)."""
    enrollment = get_enrollment_or_404(db, current_user.id, course_id)
    
    # Check if unenrollment is allowed
    if enrollment.status == ProgressStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot unenroll from completed courses"
        )
    
    # Update course enrollment count
    course = enrollment.course
    course.enrolled_count = max(0, course.enrolled_count - 1)
    
    # Delete enrollment and related progress
    db.delete(enrollment)
    db.commit()
    
    return {"message": "Successfully unenrolled from course"}