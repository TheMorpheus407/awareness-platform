"""Quiz management and submission routes."""

import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from api.dependencies.auth import get_current_active_user
from api.dependencies.common import get_db, get_pagination_params
from core.exceptions import ValidationError
from models.user import User
from models.course import Course, Quiz, QuizQuestion, UserCourseProgress
from schemas.course import (
    QuizQuestion as QuizQuestionSchema,
    QuizAnswer,
    QuizResult,
    QuizFeedback,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/course/{course_id}")
async def get_course_quiz(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Get quiz for a specific course.
    
    Args:
        course_id: Course ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Quiz details with questions (without correct answers)
        
    Raises:
        HTTPException: If course or quiz not found
    """
    # Get course with quiz
    stmt = select(Course).where(Course.id == course_id)
    result = await db.execute(stmt)
    course = result.scalar_one_or_none()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Get quiz for the course
    stmt = select(Quiz).where(Quiz.course_id == course_id)
    result = await db.execute(stmt)
    quiz = result.scalar_one_or_none()
    
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No quiz available for this course"
        )
    
    # Get quiz questions
    stmt = select(QuizQuestion).where(
        QuizQuestion.quiz_id == quiz.id
    ).order_by(QuizQuestion.order_index)
    result = await db.execute(stmt)
    questions = result.scalars().all()
    
    # Get user's progress
    stmt = select(UserCourseProgress).where(
        UserCourseProgress.user_id == current_user.id,
        UserCourseProgress.course_id == course_id
    )
    result = await db.execute(stmt)
    progress = result.scalar_one_or_none()
    
    # Prepare questions (hide correct answers)
    quiz_questions = []
    for q in questions:
        quiz_questions.append({
            "id": str(q.id),
            "question": q.question_text,
            "question_type": q.question_type,
            "options": q.options if q.question_type == "multiple_choice" else None,
            "points": q.points,
        })
    
    return {
        "quiz_id": quiz.id,
        "course_id": course_id,
        "title": quiz.title,
        "passing_score": quiz.passing_score,
        "time_limit_minutes": quiz.time_limit_minutes,
        "max_attempts": quiz.max_attempts,
        "attempts_used": getattr(progress, "quiz_attempts", 0) if progress else 0,
        "can_attempt": (
            quiz.max_attempts is None or
            getattr(progress, "quiz_attempts", 0) < quiz.max_attempts
        ),
        "total_questions": len(questions),
        "total_points": sum(q.points for q in questions),
        "questions": quiz_questions,
    }


@router.post("/course/{course_id}/submit")
async def submit_quiz(
    course_id: int,
    answers: List[QuizAnswer],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> QuizResult:
    """
    Submit quiz answers and get results.
    
    Args:
        course_id: Course ID
        answers: List of quiz answers
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Quiz results with score and feedback
        
    Raises:
        HTTPException: If quiz not found or max attempts exceeded
    """
    # Get quiz for the course
    stmt = select(Quiz).where(Quiz.course_id == course_id)
    result = await db.execute(stmt)
    quiz = result.scalar_one_or_none()
    
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No quiz available for this course"
        )
    
    # Get or create user progress
    stmt = select(UserCourseProgress).where(
        UserCourseProgress.user_id == current_user.id,
        UserCourseProgress.course_id == course_id
    )
    result = await db.execute(stmt)
    progress = result.scalar_one_or_none()
    
    if not progress:
        # Create progress record
        progress = UserCourseProgress(
            user_id=current_user.id,
            course_id=course_id,
            company_id=current_user.company_id,
            status="in_progress",
            started_at=datetime.utcnow(),
        )
        db.add(progress)
        await db.flush()
    
    # Check max attempts
    if quiz.max_attempts and hasattr(progress, 'quiz_attempts'):
        if progress.quiz_attempts >= quiz.max_attempts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Maximum attempts ({quiz.max_attempts}) exceeded"
            )
    
    # Get quiz questions
    stmt = select(QuizQuestion).where(QuizQuestion.quiz_id == quiz.id)
    result = await db.execute(stmt)
    questions = result.scalars().all()
    
    # Create answer lookup
    answer_map = {ans.question_id: ans.answer_id for ans in answers}
    
    # Calculate score
    correct_answers = 0
    total_points = 0
    points_earned = 0
    feedback_list = []
    
    for question in questions:
        total_points += question.points
        user_answer = answer_map.get(str(question.id))
        
        is_correct = False
        if user_answer:
            if question.question_type == "multiple_choice":
                # For multiple choice, check if answer matches
                is_correct = user_answer == question.correct_answer
            elif question.question_type == "true_false":
                # For true/false questions
                is_correct = user_answer.lower() == question.correct_answer.lower()
            # For other types, might need different handling
            
            if is_correct:
                correct_answers += 1
                points_earned += question.points
        
        # Add feedback
        feedback_list.append(QuizFeedback(
            question_id=str(question.id),
            correct=is_correct,
            selected_answer_id=user_answer or "",
            correct_answer_id=question.correct_answer,
            explanation=question.explanation if not is_correct else None,
            points_earned=question.points if is_correct else 0,
        ))
    
    # Calculate percentage score
    score = (points_earned / total_points * 100) if total_points > 0 else 0
    passed = score >= quiz.passing_score
    
    # Update progress
    if hasattr(progress, 'quiz_attempts'):
        progress.quiz_attempts = getattr(progress, 'quiz_attempts', 0) + 1
    
    # Update best score if this is better
    if not hasattr(progress, 'best_quiz_score') or score > getattr(progress, 'best_quiz_score', 0):
        if hasattr(progress, 'best_quiz_score'):
            progress.best_quiz_score = score
    
    # If passed and course completed, mark as completed
    if passed and progress.progress_percentage >= 100:
        progress.status = "completed"
        progress.completed_at = datetime.utcnow()
        progress.certificate_issued = True
    
    await db.commit()
    
    # Prepare result
    can_retry = (
        not passed and
        (quiz.max_attempts is None or
         getattr(progress, 'quiz_attempts', 0) < quiz.max_attempts)
    )
    
    certificate_id = None
    if passed and progress.status == "completed":
        certificate_id = f"CERT-{current_user.id:04d}-{course_id:04d}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    
    return QuizResult(
        score=round(score, 2),
        passed=passed,
        passing_score=float(quiz.passing_score),
        correct_answers=correct_answers,
        total_questions=len(questions),
        points_earned=points_earned,
        total_points=total_points,
        feedback=feedback_list,
        attempt_number=getattr(progress, 'quiz_attempts', 1),
        can_retry=can_retry,
        certificate_id=certificate_id,
    )


@router.get("/user/history")
async def get_user_quiz_history(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    course_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Get user's quiz attempt history.
    
    Args:
        page: Page number
        size: Page size
        course_id: Optional filter by course
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Paginated list of quiz attempts
    """
    offset, limit = get_pagination_params(page, size)
    
    # Build query
    stmt = select(UserCourseProgress, Course, Quiz).join(
        Course, UserCourseProgress.course_id == Course.id
    ).join(
        Quiz, Quiz.course_id == Course.id
    ).where(
        UserCourseProgress.user_id == current_user.id,
    )
    
    if course_id:
        stmt = stmt.where(UserCourseProgress.course_id == course_id)
    
    # Get total count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    result = await db.execute(count_stmt)
    total = result.scalar()
    
    # Get paginated results
    stmt = stmt.offset(offset).limit(limit).order_by(UserCourseProgress.updated_at.desc())
    result = await db.execute(stmt)
    attempts = result.all()
    
    # Format results
    items = []
    for progress, course, quiz in attempts:
        if hasattr(progress, 'quiz_attempts') and progress.quiz_attempts > 0:
            items.append({
                "course_id": course.id,
                "course_title": course.title,
                "quiz_title": quiz.title,
                "attempts": getattr(progress, 'quiz_attempts', 0),
                "best_score": getattr(progress, 'best_quiz_score', 0),
                "passing_score": quiz.passing_score,
                "passed": getattr(progress, 'best_quiz_score', 0) >= quiz.passing_score,
                "last_attempt_at": progress.updated_at,
                "certificate_available": progress.certificate_issued,
            })
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size,
    }


@router.get("/statistics")
async def get_quiz_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Get user's overall quiz statistics.
    
    Args:
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        User's quiz performance statistics
    """
    # Get all user's quiz attempts
    stmt = select(UserCourseProgress, Quiz).join(
        Quiz, Quiz.course_id == UserCourseProgress.course_id
    ).where(
        UserCourseProgress.user_id == current_user.id,
    )
    
    result = await db.execute(stmt)
    progress_records = result.all()
    
    # Calculate statistics
    total_quizzes_attempted = 0
    total_quizzes_passed = 0
    total_attempts = 0
    scores = []
    
    for progress, quiz in progress_records:
        if hasattr(progress, 'quiz_attempts') and progress.quiz_attempts > 0:
            total_quizzes_attempted += 1
            total_attempts += progress.quiz_attempts
            
            best_score = getattr(progress, 'best_quiz_score', 0)
            if best_score > 0:
                scores.append(best_score)
                if best_score >= quiz.passing_score:
                    total_quizzes_passed += 1
    
    # Calculate averages
    average_score = sum(scores) / len(scores) if scores else 0
    pass_rate = (total_quizzes_passed / total_quizzes_attempted * 100) if total_quizzes_attempted > 0 else 0
    average_attempts = total_attempts / total_quizzes_attempted if total_quizzes_attempted > 0 else 0
    
    return {
        "total_quizzes_attempted": total_quizzes_attempted,
        "total_quizzes_passed": total_quizzes_passed,
        "total_attempts": total_attempts,
        "average_score": round(average_score, 2),
        "pass_rate": round(pass_rate, 2),
        "average_attempts_per_quiz": round(average_attempts, 2),
        "highest_score": max(scores) if scores else 0,
        "lowest_score": min(scores) if scores else 0,
    }


@router.post("/reset/{course_id}")
async def reset_quiz_attempts(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Reset quiz attempts for a course (admin only).
    
    Args:
        course_id: Course ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If not authorized or course not found
    """
    # Check if user is admin
    if current_user.role not in ["admin", "superuser"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can reset quiz attempts"
        )
    
    # Get user progress
    stmt = select(UserCourseProgress).where(
        UserCourseProgress.user_id == current_user.id,
        UserCourseProgress.course_id == course_id
    )
    result = await db.execute(stmt)
    progress = result.scalar_one_or_none()
    
    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No progress found for this course"
        )
    
    # Reset quiz attempts
    if hasattr(progress, 'quiz_attempts'):
        progress.quiz_attempts = 0
    if hasattr(progress, 'best_quiz_score'):
        progress.best_quiz_score = 0
    
    await db.commit()
    
    return {"message": "Quiz attempts reset successfully"}


@router.get("/leaderboard")
async def get_quiz_leaderboard(
    course_id: Optional[int] = None,
    time_period: Optional[str] = Query("all", regex="^(all|month|week)$"),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Get quiz leaderboard for company.
    
    Args:
        course_id: Optional filter by course
        time_period: Time period filter (all, month, week)
        limit: Number of top users to return
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Leaderboard with top performers
    """
    # Base query - only users from same company
    stmt = select(
        UserCourseProgress.user_id,
        User.first_name,
        User.last_name,
        func.count(UserCourseProgress.id).label("quizzes_completed"),
        func.avg(UserCourseProgress.progress_percentage).label("avg_score"),
    ).join(
        User, UserCourseProgress.user_id == User.id
    ).where(
        User.company_id == current_user.company_id,
        UserCourseProgress.status == "completed",
    )
    
    # Apply time filter
    if time_period == "month":
        from datetime import timedelta
        stmt = stmt.where(
            UserCourseProgress.completed_at >= datetime.utcnow() - timedelta(days=30)
        )
    elif time_period == "week":
        from datetime import timedelta
        stmt = stmt.where(
            UserCourseProgress.completed_at >= datetime.utcnow() - timedelta(days=7)
        )
    
    # Apply course filter
    if course_id:
        stmt = stmt.where(UserCourseProgress.course_id == course_id)
    
    # Group and order
    stmt = stmt.group_by(
        UserCourseProgress.user_id,
        User.first_name,
        User.last_name
    ).order_by(
        func.avg(UserCourseProgress.progress_percentage).desc()
    ).limit(limit)
    
    result = await db.execute(stmt)
    leaderboard = result.all()
    
    # Format results
    items = []
    rank = 1
    for user_id, first_name, last_name, quizzes_completed, avg_score in leaderboard:
        items.append({
            "rank": rank,
            "user_id": user_id,
            "name": f"{first_name} {last_name}",
            "quizzes_completed": quizzes_completed,
            "average_score": round(float(avg_score or 0), 2),
            "is_current_user": user_id == current_user.id,
        })
        rank += 1
    
    # Get current user's rank if not in top
    current_user_in_top = any(item["is_current_user"] for item in items)
    current_user_rank = None
    
    if not current_user_in_top:
        # Query for current user's rank
        subquery = select(
            UserCourseProgress.user_id,
            func.avg(UserCourseProgress.progress_percentage).label("avg_score"),
        ).join(
            User, UserCourseProgress.user_id == User.id
        ).where(
            User.company_id == current_user.company_id,
            UserCourseProgress.status == "completed",
        ).group_by(UserCourseProgress.user_id).subquery()
        
        stmt = select(func.count()).select_from(subquery).where(
            subquery.c.avg_score > select(subquery.c.avg_score).where(
                subquery.c.user_id == current_user.id
            ).scalar_subquery()
        )
        
        result = await db.execute(stmt)
        rank_above = result.scalar() or 0
        current_user_rank = rank_above + 1
    
    return {
        "leaderboard": items,
        "current_user_rank": current_user_rank,
        "time_period": time_period,
        "course_filter": course_id,
    }