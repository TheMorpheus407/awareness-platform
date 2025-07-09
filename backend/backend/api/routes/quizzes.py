"""Quiz and assessment API routes."""

from typing import List, Dict, Any
from datetime import datetime
import random

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func

from api.dependencies.auth import get_current_active_user
from db.session import get_db
from models import (
    User, UserRole, Lesson, Quiz, QuizQuestion, QuizAttempt, QuizAnswer,
    CourseEnrollment, LessonProgress, ProgressStatus
)
from schemas.course import (
    QuizCreate, QuizUpdate, QuizPublic, QuizInDB,
    QuizQuestionCreate, QuizQuestionUpdate, QuizQuestionInDB,
    QuizAttemptCreate, QuizAttemptSubmit, QuizAttemptResult,
    QuizAnswerSubmit
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


def get_quiz_or_404(db: Session, quiz_id: int) -> Quiz:
    """Get quiz by ID or raise 404."""
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    return quiz


def get_enrollment_for_quiz(
    db: Session,
    user_id: int,
    quiz: Quiz
) -> CourseEnrollment:
    """Get enrollment for quiz's course."""
    course_id = quiz.lesson.module.course_id
    
    enrollment = db.query(CourseEnrollment).filter(
        and_(
            CourseEnrollment.user_id == user_id,
            CourseEnrollment.course_id == course_id
        )
    ).first()
    
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Enrollment required to access this quiz"
        )
    
    return enrollment


def check_quiz_attempts(
    db: Session,
    user_id: int,
    quiz_id: int,
    max_attempts: int = None
) -> int:
    """Check if user can attempt quiz and return attempt number."""
    attempt_count = db.query(func.count(QuizAttempt.id)).filter(
        and_(
            QuizAttempt.user_id == user_id,
            QuizAttempt.quiz_id == quiz_id,
            QuizAttempt.submitted_at.isnot(None)
        )
    ).scalar() or 0
    
    if max_attempts and attempt_count >= max_attempts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum attempts ({max_attempts}) reached"
        )
    
    return attempt_count + 1


def calculate_quiz_score(
    answers: List[QuizAnswer],
    questions: List[QuizQuestion]
) -> Dict[str, Any]:
    """Calculate quiz score and statistics."""
    total_points = sum(q.points for q in questions if not q.is_bonus)
    bonus_points = sum(q.points for q in questions if q.is_bonus)
    earned_points = 0
    earned_bonus = 0
    questions_correct = 0
    
    question_map = {q.id: q for q in questions}
    
    for answer in answers:
        question = question_map.get(answer.question_id)
        if not question:
            continue
        
        # Check answer correctness
        is_correct = False
        points_earned = 0
        
        if question.question_type == "multiple_choice":
            is_correct = answer.answer == question.correct_answer
        elif question.question_type == "true_false":
            is_correct = str(answer.answer).lower() == str(question.correct_answer).lower()
        elif question.question_type == "multiple_select":
            if isinstance(answer.answer, list) and isinstance(question.correct_answer, list):
                is_correct = set(answer.answer) == set(question.correct_answer)
                # Partial credit if enabled
                if question.partial_credit and not is_correct:
                    correct_set = set(question.correct_answer)
                    answer_set = set(answer.answer)
                    correct_selections = correct_set.intersection(answer_set)
                    wrong_selections = answer_set - correct_set
                    partial_ratio = (len(correct_selections) - len(wrong_selections)) / len(correct_set)
                    if partial_ratio > 0:
                        points_earned = question.points * partial_ratio
        elif question.question_type == "text":
            # Simple text matching (could be enhanced with fuzzy matching)
            is_correct = str(answer.answer).strip().lower() == str(question.correct_answer).strip().lower()
        
        # Update answer record
        answer.is_correct = is_correct
        
        if is_correct:
            points_earned = question.points
            questions_correct += 1
        elif points_earned == 0 and question.negative_points > 0:
            points_earned = -question.negative_points
        
        answer.points_earned = points_earned
        
        # Add to totals
        if question.is_bonus:
            earned_bonus += max(0, points_earned)
        else:
            earned_points += points_earned
    
    # Calculate percentage score
    score_percentage = (earned_points / total_points * 100) if total_points > 0 else 0
    score_percentage = max(0, min(100, score_percentage))  # Clamp to 0-100
    
    return {
        "score": score_percentage,
        "earned_points": earned_points,
        "total_points": total_points,
        "bonus_points": earned_bonus,
        "questions_correct": questions_correct,
        "questions_total": len(questions)
    }


# Quiz management endpoints
@router.post("/lessons/{lesson_id}/quiz", response_model=QuizInDB)
def create_quiz(
    lesson_id: int,
    quiz_in: QuizCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a quiz for a lesson (admin/instructor only)."""
    check_admin_or_instructor(current_user)
    
    # Check if lesson exists
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )
    
    # Check if quiz already exists
    existing = db.query(Quiz).filter(Quiz.lesson_id == lesson_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quiz already exists for this lesson"
        )
    
    # Create quiz
    quiz = Quiz(**quiz_in.model_dump())
    quiz.lesson_id = lesson_id
    
    db.add(quiz)
    db.commit()
    db.refresh(quiz)
    
    return quiz


@router.get("/quizzes/{quiz_id}", response_model=QuizPublic)
def get_quiz(
    quiz_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get quiz details (without questions)."""
    quiz = get_quiz_or_404(db, quiz_id)
    
    # Check enrollment
    enrollment = get_enrollment_for_quiz(db, current_user.id, quiz)
    
    # Get question count
    question_count = db.query(func.count(QuizQuestion.id)).filter(
        QuizQuestion.quiz_id == quiz_id
    ).scalar() or 0
    
    # Get user's attempts
    attempts = db.query(QuizAttempt).filter(
        and_(
            QuizAttempt.user_id == current_user.id,
            QuizAttempt.quiz_id == quiz_id
        )
    ).order_by(QuizAttempt.started_at.desc()).all()
    
    # Calculate remaining attempts
    attempts_remaining = None
    if quiz.max_attempts:
        completed_attempts = sum(1 for a in attempts if a.submitted_at)
        attempts_remaining = max(0, quiz.max_attempts - completed_attempts)
    
    # Get best score
    best_score = None
    last_attempt = None
    
    if attempts:
        completed_attempts = [a for a in attempts if a.submitted_at and a.score is not None]
        if completed_attempts:
            best_attempt = max(completed_attempts, key=lambda a: a.score)
            best_score = best_attempt.score
            last_attempt = QuizAttemptResult.model_validate(attempts[0])
    
    # Prepare response
    quiz_dict = quiz.__dict__.copy()
    quiz_dict["question_count"] = question_count
    quiz_dict["attempts_remaining"] = attempts_remaining
    quiz_dict["best_score"] = best_score
    quiz_dict["last_attempt"] = last_attempt
    
    return QuizPublic.model_validate(quiz_dict)


@router.put("/quizzes/{quiz_id}", response_model=QuizInDB)
def update_quiz(
    quiz_id: int,
    quiz_in: QuizUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update quiz settings (admin/instructor only)."""
    check_admin_or_instructor(current_user)
    
    quiz = get_quiz_or_404(db, quiz_id)
    
    # Update fields
    update_data = quiz_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(quiz, field, value)
    
    quiz.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(quiz)
    
    return quiz


@router.delete("/quizzes/{quiz_id}")
def delete_quiz(
    quiz_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a quiz (admin/instructor only)."""
    check_admin_or_instructor(current_user)
    
    quiz = get_quiz_or_404(db, quiz_id)
    
    # Check if quiz has attempts
    attempt_count = db.query(func.count(QuizAttempt.id)).filter(
        QuizAttempt.quiz_id == quiz_id
    ).scalar() or 0
    
    if attempt_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete quiz with {attempt_count} attempts"
        )
    
    db.delete(quiz)
    db.commit()
    
    return {"message": "Quiz deleted successfully"}


# Question management endpoints
@router.post("/quizzes/{quiz_id}/questions", response_model=QuizQuestionInDB)
def create_question(
    quiz_id: int,
    question_in: QuizQuestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Add a question to a quiz (admin/instructor only)."""
    check_admin_or_instructor(current_user)
    
    quiz = get_quiz_or_404(db, quiz_id)
    
    # Create question
    question = QuizQuestion(**question_in.model_dump())
    question.quiz_id = quiz_id
    
    db.add(question)
    db.commit()
    db.refresh(question)
    
    return question


@router.get("/quizzes/{quiz_id}/questions", response_model=List[QuizQuestionInDB])
def get_quiz_questions(
    quiz_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all questions for a quiz (admin/instructor only)."""
    check_admin_or_instructor(current_user)
    
    quiz = get_quiz_or_404(db, quiz_id)
    
    questions = db.query(QuizQuestion).filter(
        QuizQuestion.quiz_id == quiz_id
    ).order_by(QuizQuestion.order_index).all()
    
    return questions


@router.put("/questions/{question_id}", response_model=QuizQuestionInDB)
def update_question(
    question_id: int,
    question_in: QuizQuestionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a quiz question (admin/instructor only)."""
    check_admin_or_instructor(current_user)
    
    question = db.query(QuizQuestion).filter(QuizQuestion.id == question_id).first()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    
    # Update fields
    update_data = question_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(question, field, value)
    
    question.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(question)
    
    return question


@router.delete("/questions/{question_id}")
def delete_question(
    question_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a quiz question (admin/instructor only)."""
    check_admin_or_instructor(current_user)
    
    question = db.query(QuizQuestion).filter(QuizQuestion.id == question_id).first()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    
    # Reorder remaining questions
    db.query(QuizQuestion).filter(
        and_(
            QuizQuestion.quiz_id == question.quiz_id,
            QuizQuestion.order_index > question.order_index
        )
    ).update({"order_index": QuizQuestion.order_index - 1})
    
    db.delete(question)
    db.commit()
    
    return {"message": "Question deleted successfully"}


# Quiz attempt endpoints
@router.post("/quizzes/{quiz_id}/start", response_model=Dict[str, Any])
def start_quiz_attempt(
    quiz_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Start a new quiz attempt."""
    quiz = get_quiz_or_404(db, quiz_id)
    
    # Check enrollment
    enrollment = get_enrollment_for_quiz(db, current_user.id, quiz)
    
    # Check attempts
    attempt_number = check_quiz_attempts(db, current_user.id, quiz_id, quiz.max_attempts)
    
    # Check if there's an unfinished attempt
    unfinished = db.query(QuizAttempt).filter(
        and_(
            QuizAttempt.user_id == current_user.id,
            QuizAttempt.quiz_id == quiz_id,
            QuizAttempt.submitted_at.is_(None)
        )
    ).first()
    
    if unfinished:
        # Return existing attempt
        attempt = unfinished
    else:
        # Create new attempt
        attempt = QuizAttempt(
            user_id=current_user.id,
            quiz_id=quiz_id,
            enrollment_id=enrollment.id,
            attempt_number=attempt_number
        )
        db.add(attempt)
        db.commit()
        db.refresh(attempt)
    
    # Get questions
    questions = db.query(QuizQuestion).filter(
        QuizQuestion.quiz_id == quiz_id
    ).order_by(QuizQuestion.order_index).all()
    
    # Randomize if needed
    if quiz.randomize_questions:
        random.shuffle(questions)
    
    # Prepare questions for frontend (without correct answers)
    question_list = []
    for q in questions:
        q_dict = {
            "id": q.id,
            "question_text": q.question_text,
            "question_type": q.question_type,
            "options": q.options,
            "points": q.points,
            "hint": q.hint,
            "image_url": q.image_url,
            "video_url": q.video_url
        }
        
        # Randomize answer options if needed
        if quiz.randomize_answers and q.options and isinstance(q.options, list):
            q_dict["options"] = random.sample(q.options, len(q.options))
        
        question_list.append(q_dict)
    
    return {
        "attempt_id": attempt.id,
        "quiz_id": quiz.id,
        "title": quiz.title,
        "instructions": quiz.instructions,
        "passing_score": quiz.passing_score,
        "time_limit_minutes": quiz.time_limit_minutes,
        "show_correct_answers": quiz.show_correct_answers,
        "questions": question_list,
        "started_at": attempt.started_at.isoformat()
    }


@router.post("/attempts/{attempt_id}/submit", response_model=QuizAttemptResult)
def submit_quiz_attempt(
    attempt_id: int,
    submission: QuizAttemptSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Submit answers for a quiz attempt."""
    # Get attempt
    attempt = db.query(QuizAttempt).filter(
        and_(
            QuizAttempt.id == attempt_id,
            QuizAttempt.user_id == current_user.id
        )
    ).first()
    
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz attempt not found"
        )
    
    if attempt.submitted_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quiz already submitted"
        )
    
    quiz = attempt.quiz
    
    # Check time limit
    if quiz.time_limit_minutes:
        time_elapsed = (datetime.utcnow() - attempt.started_at).total_seconds() / 60
        if time_elapsed > quiz.time_limit_minutes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Time limit exceeded"
            )
    
    # Get all questions
    questions = db.query(QuizQuestion).filter(
        QuizQuestion.quiz_id == quiz.id
    ).all()
    
    # Create answer records
    answer_map = {a.question_id: a for a in submission.answers}
    answers = []
    
    for question in questions:
        answer_data = answer_map.get(question.id)
        
        answer = QuizAnswer(
            attempt_id=attempt_id,
            question_id=question.id,
            answer=answer_data.answer if answer_data else None,
            time_spent_seconds=answer_data.time_spent_seconds if answer_data else None
        )
        answers.append(answer)
        db.add(answer)
    
    # Calculate score
    score_data = calculate_quiz_score(answers, questions)
    
    # Update attempt
    attempt.submitted_at = datetime.utcnow()
    attempt.time_spent_seconds = int((attempt.submitted_at - attempt.started_at).total_seconds())
    attempt.score = score_data["score"]
    attempt.passed = score_data["score"] >= quiz.passing_score
    attempt.questions_answered = len([a for a in submission.answers if a.answer is not None])
    attempt.questions_correct = score_data["questions_correct"]
    
    # Save everything
    db.commit()
    
    # Update lesson progress if passed and required
    if quiz.is_required and attempt.passed:
        lesson_progress = db.query(LessonProgress).filter(
            and_(
                LessonProgress.enrollment_id == attempt.enrollment_id,
                LessonProgress.lesson_id == quiz.lesson_id
            )
        ).first()
        
        if lesson_progress and lesson_progress.status != ProgressStatus.COMPLETED:
            # This will trigger cascade updates to module and course progress
            from .enrollments import update_lesson_progress, LessonProgressUpdate
            
            progress_update = LessonProgressUpdate(
                status=ProgressStatus.COMPLETED,
                progress_percentage=100.0,
                completed=True
            )
            
            update_lesson_progress(
                lesson_id=quiz.lesson_id,
                progress_in=progress_update,
                db=db,
                current_user=current_user
            )
    
    # Prepare feedback
    feedback = None
    if attempt.passed:
        feedback = f"Congratulations! You passed with {score_data['score']:.1f}%"
    else:
        feedback = f"You scored {score_data['score']:.1f}%. The passing score is {quiz.passing_score}%."
        if quiz.max_attempts:
            remaining = quiz.max_attempts - attempt.attempt_number
            if remaining > 0:
                feedback += f" You have {remaining} attempt(s) remaining."
    
    # Prepare result
    result = QuizAttemptResult(
        id=attempt.id,
        quiz_id=quiz.id,
        attempt_number=attempt.attempt_number,
        started_at=attempt.started_at,
        submitted_at=attempt.submitted_at,
        time_spent_seconds=attempt.time_spent_seconds,
        score=attempt.score,
        passed=attempt.passed,
        questions_answered=attempt.questions_answered,
        questions_correct=attempt.questions_correct,
        feedback=feedback
    )
    
    return result


@router.get("/attempts/{attempt_id}/review")
def review_quiz_attempt(
    attempt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Review a completed quiz attempt with correct answers."""
    # Get attempt
    attempt = db.query(QuizAttempt).filter(
        and_(
            QuizAttempt.id == attempt_id,
            QuizAttempt.user_id == current_user.id
        )
    ).first()
    
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz attempt not found"
        )
    
    if not attempt.submitted_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quiz not yet submitted"
        )
    
    quiz = attempt.quiz
    
    if not quiz.show_correct_answers:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Review not available for this quiz"
        )
    
    # Get questions and answers
    questions = db.query(QuizQuestion).filter(
        QuizQuestion.quiz_id == quiz.id
    ).order_by(QuizQuestion.order_index).all()
    
    answers = db.query(QuizAnswer).filter(
        QuizAnswer.attempt_id == attempt_id
    ).all()
    
    answer_map = {a.question_id: a for a in answers}
    
    # Prepare review data
    review_data = []
    for q in questions:
        answer = answer_map.get(q.id)
        
        review_data.append({
            "question": {
                "id": q.id,
                "question_text": q.question_text,
                "question_type": q.question_type,
                "options": q.options,
                "correct_answer": q.correct_answer,
                "explanation": q.explanation,
                "points": q.points
            },
            "user_answer": answer.answer if answer else None,
            "is_correct": answer.is_correct if answer else False,
            "points_earned": answer.points_earned if answer else 0
        })
    
    return {
        "attempt_id": attempt.id,
        "quiz_title": quiz.title,
        "score": attempt.score,
        "passed": attempt.passed,
        "questions": review_data
    }