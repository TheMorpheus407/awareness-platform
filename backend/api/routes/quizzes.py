"""Quiz management and submission routes."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.dependencies.auth import get_current_active_user
from api.dependencies.common import get_pagination_params
from core.cache import cache
from core.logging import logger
from db.session import get_db
from models.course import Quiz, QuizQuestion, UserCourseProgress
from models.user import User
from schemas.course import (
    QuizAnswer,
    QuizCreate,
    QuizDetail,
    QuizQuestion as QuizQuestionSchema,
    QuizResponse,
    QuizResult,
    QuizSubmission,
    QuizUpdate,
)

router = APIRouter()


@router.get("/{quiz_id}", response_model=QuizDetail)
async def get_quiz(
    quiz_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> QuizDetail:
    """Get quiz details with questions."""
    # Get quiz with questions
    result = await db.execute(
        select(Quiz)
        .options(selectinload(Quiz.questions))
        .where(Quiz.id == quiz_id)
    )
    quiz = result.scalar_one_or_none()
    
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    # Check if user has access to this quiz (enrolled in course)
    progress = await db.execute(
        select(UserCourseProgress).where(
            UserCourseProgress.user_id == current_user.id,
            UserCourseProgress.course_id == quiz.course_id,
        )
    )
    if not progress.scalar_one_or_none():
        raise HTTPException(
            status_code=403,
            detail="You must be enrolled in the course to access this quiz"
        )
    
    # Convert to schema, hiding correct answers
    questions = []
    for q in sorted(quiz.questions, key=lambda x: x.order_index):
        question_data = QuizQuestionSchema(
            id=q.id,
            question=q.question_text,
            question_type=q.question_type,
            options=q.options,
            points=q.points,
            order_index=q.order_index,
        )
        questions.append(question_data)
    
    return QuizDetail(
        id=quiz.id,
        course_id=quiz.course_id,
        title=quiz.title,
        description=quiz.description or "",
        passing_score=quiz.passing_score,
        time_limit_minutes=quiz.time_limit_minutes,
        max_attempts=quiz.max_attempts,
        is_required=quiz.is_required,
        questions=questions,
        total_points=sum(q.points for q in quiz.questions),
        question_count=len(quiz.questions),
    )


@router.post("/{quiz_id}/submit", response_model=QuizResult)
async def submit_quiz(
    quiz_id: int,
    submission: QuizSubmission,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> QuizResult:
    """Submit quiz answers and get results."""
    # Get quiz with questions
    result = await db.execute(
        select(Quiz)
        .options(selectinload(Quiz.questions))
        .where(Quiz.id == quiz_id)
    )
    quiz = result.scalar_one_or_none()
    
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    # Check enrollment and attempts
    progress = await db.execute(
        select(UserCourseProgress).where(
            UserCourseProgress.user_id == current_user.id,
            UserCourseProgress.course_id == quiz.course_id,
        )
    )
    progress = progress.scalar_one_or_none()
    
    if not progress:
        raise HTTPException(
            status_code=403,
            detail="You must be enrolled in the course to take this quiz"
        )
    
    # TODO: Check attempt count against quiz.max_attempts
    
    # Grade the quiz
    total_points = 0
    earned_points = 0
    feedback = []
    
    # Create answer lookup
    answer_map = {str(a.question_id): a.answer_id for a in submission.answers}
    
    for question in quiz.questions:
        total_points += question.points
        
        user_answer = answer_map.get(str(question.id))
        correct = False
        
        if user_answer:
            # Check if answer is correct
            if question.question_type == "true_false":
                correct = user_answer == question.correct_answer
            elif question.question_type == "multiple_choice":
                correct = user_answer == question.correct_answer
            elif question.question_type == "text":
                # Simple text comparison (could be enhanced)
                correct = (
                    user_answer.lower().strip() == 
                    question.correct_answer.lower().strip()
                )
            
            if correct:
                earned_points += question.points
        
        feedback.append({
            "question_id": str(question.id),
            "correct": correct,
            "explanation": question.explanation if not correct else None,
        })
    
    # Calculate score
    score = (earned_points / total_points * 100) if total_points > 0 else 0
    passed = score >= quiz.passing_score
    
    # Update course progress if passed and quiz is required
    if passed and quiz.is_required:
        # TODO: Update course progress percentage
        logger.info(
            f"User {current_user.id} passed required quiz {quiz_id} "
            f"with score {score}%"
        )
    
    # TODO: Store quiz attempt in database
    
    return QuizResult(
        quiz_id=quiz_id,
        score=round(score, 2),
        passed=passed,
        passing_score=quiz.passing_score,
        correct_answers=sum(1 for f in feedback if f["correct"]),
        total_questions=len(quiz.questions),
        earned_points=earned_points,
        total_points=total_points,
        feedback=feedback,
        completion_time_seconds=submission.time_spent_seconds,
    )


@router.get("/course/{course_id}", response_model=list[QuizResponse])
async def get_course_quizzes(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[QuizResponse]:
    """Get all quizzes for a course."""
    # Check enrollment
    progress = await db.execute(
        select(UserCourseProgress).where(
            UserCourseProgress.user_id == current_user.id,
            UserCourseProgress.course_id == course_id,
        )
    )
    if not progress.scalar_one_or_none():
        raise HTTPException(
            status_code=403,
            detail="You must be enrolled in the course to view its quizzes"
        )
    
    # Get quizzes
    result = await db.execute(
        select(Quiz)
        .where(Quiz.course_id == course_id)
        .order_by(Quiz.created_at)
    )
    quizzes = result.scalars().all()
    
    # TODO: Add user's attempt information
    return [
        QuizResponse(
            id=quiz.id,
            course_id=quiz.course_id,
            title=quiz.title,
            description=quiz.description,
            passing_score=quiz.passing_score,
            time_limit_minutes=quiz.time_limit_minutes,
            max_attempts=quiz.max_attempts,
            is_required=quiz.is_required,
            question_count=len(quiz.questions) if quiz.questions else 0,
            # TODO: Add these fields from quiz attempts
            attempts_made=0,
            best_score=None,
            last_attempt_date=None,
            is_passed=False,
        )
        for quiz in quizzes
    ]


@router.post("/", response_model=QuizResponse)
async def create_quiz(
    quiz_data: QuizCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> QuizResponse:
    """Create a new quiz (admin only)."""
    if current_user.role not in ["company_admin", "system_admin"]:
        raise HTTPException(
            status_code=403,
            detail="Only administrators can create quizzes"
        )
    
    # Create quiz
    quiz = Quiz(
        course_id=quiz_data.course_id,
        title=quiz_data.title,
        description=quiz_data.description,
        passing_score=quiz_data.passing_score,
        time_limit_minutes=quiz_data.time_limit_minutes,
        max_attempts=quiz_data.max_attempts,
        is_required=quiz_data.is_required,
    )
    db.add(quiz)
    await db.flush()
    
    # Add questions
    for idx, q_data in enumerate(quiz_data.questions):
        question = QuizQuestion(
            quiz_id=quiz.id,
            question_text=q_data.question,
            question_type=q_data.question_type,
            options=q_data.options,
            correct_answer=q_data.correct_answer,
            explanation=q_data.explanation,
            points=q_data.points,
            order_index=idx,
        )
        db.add(question)
    
    await db.commit()
    await db.refresh(quiz)
    
    # Clear cache
    await cache.delete(f"quiz:{quiz.id}")
    await cache.delete(f"course_quizzes:{quiz.course_id}")
    
    return QuizResponse(
        id=quiz.id,
        course_id=quiz.course_id,
        title=quiz.title,
        description=quiz.description,
        passing_score=quiz.passing_score,
        time_limit_minutes=quiz.time_limit_minutes,
        max_attempts=quiz.max_attempts,
        is_required=quiz.is_required,
        question_count=len(quiz_data.questions),
        attempts_made=0,
        best_score=None,
        last_attempt_date=None,
        is_passed=False,
    )


@router.put("/{quiz_id}", response_model=QuizResponse)
async def update_quiz(
    quiz_id: int,
    quiz_data: QuizUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> QuizResponse:
    """Update quiz details (admin only)."""
    if current_user.role not in ["company_admin", "system_admin"]:
        raise HTTPException(
            status_code=403,
            detail="Only administrators can update quizzes"
        )
    
    # Get quiz
    result = await db.execute(
        select(Quiz).where(Quiz.id == quiz_id)
    )
    quiz = result.scalar_one_or_none()
    
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    # Update fields
    update_data = quiz_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(quiz, field, value)
    
    await db.commit()
    await db.refresh(quiz)
    
    # Clear cache
    await cache.delete(f"quiz:{quiz_id}")
    await cache.delete(f"course_quizzes:{quiz.course_id}")
    
    return QuizResponse(
        id=quiz.id,
        course_id=quiz.course_id,
        title=quiz.title,
        description=quiz.description,
        passing_score=quiz.passing_score,
        time_limit_minutes=quiz.time_limit_minutes,
        max_attempts=quiz.max_attempts,
        is_required=quiz.is_required,
        question_count=len(quiz.questions) if quiz.questions else 0,
        attempts_made=0,
        best_score=None,
        last_attempt_date=None,
        is_passed=False,
    )


@router.delete("/{quiz_id}", status_code=204)
async def delete_quiz(
    quiz_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """Delete a quiz (admin only)."""
    if current_user.role not in ["company_admin", "system_admin"]:
        raise HTTPException(
            status_code=403,
            detail="Only administrators can delete quizzes"
        )
    
    # Get quiz
    result = await db.execute(
        select(Quiz).where(Quiz.id == quiz_id)
    )
    quiz = result.scalar_one_or_none()
    
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    # Delete quiz (cascades to questions)
    await db.delete(quiz)
    await db.commit()
    
    # Clear cache
    await cache.delete(f"quiz:{quiz_id}")
    await cache.delete(f"course_quizzes:{quiz.course_id}")