"""Quiz management service for handling quiz operations."""

from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.course import (
    Quiz, QuizQuestion, UserCourseProgress, 
    Certificate, UserPoints, UserBadge, Badge
)
from models.user import User
from core.logging import logger
from core.exceptions import ValidationError, NotFoundError, PermissionError
from core.security import SecurityUtils
import secrets
import string


class QuizService:
    """Service for managing quizzes and quiz attempts."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def get_quiz(self, quiz_id: int, include_answers: bool = False) -> Optional[Quiz]:
        """Get quiz by ID with questions."""
        query = select(Quiz).where(Quiz.id == quiz_id)
        if include_answers:
            query = query.options(selectinload(Quiz.questions))
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
        
    async def get_course_quiz(self, course_id: int) -> Optional[Quiz]:
        """Get quiz for a specific course."""
        result = await self.db.execute(
            select(Quiz)
            .where(Quiz.course_id == course_id)
            .options(selectinload(Quiz.questions))
        )
        return result.scalar_one_or_none()
        
    async def create_quiz(
        self,
        course_id: int,
        title: str,
        passing_score: int = 70,
        time_limit_minutes: Optional[int] = None,
        max_attempts: Optional[int] = 3,
        is_required: bool = True
    ) -> Quiz:
        """Create a new quiz for a course."""
        quiz = Quiz(
            course_id=course_id,
            title=title,
            passing_score=passing_score,
            time_limit_minutes=time_limit_minutes,
            max_attempts=max_attempts,
            is_required=is_required
        )
        
        self.db.add(quiz)
        await self.db.commit()
        await self.db.refresh(quiz)
        
        logger.info(f"Created quiz: {quiz.id} for course: {course_id}")
        return quiz
        
    async def add_question(
        self,
        quiz_id: int,
        question_text: str,
        question_type: str,
        correct_answer: str,
        options: Optional[Dict] = None,
        explanation: Optional[str] = None,
        points: int = 1,
        order_index: int = 0
    ) -> QuizQuestion:
        """Add a question to a quiz."""
        # Validate question type
        valid_types = ["multiple_choice", "true_false", "text"]
        if question_type not in valid_types:
            raise ValidationError(f"Invalid question type. Must be one of: {valid_types}")
            
        # Validate options for multiple choice
        if question_type == "multiple_choice" and not options:
            raise ValidationError("Multiple choice questions must have options")
            
        question = QuizQuestion(
            quiz_id=quiz_id,
            question_text=question_text,
            question_type=question_type,
            options=options,
            correct_answer=correct_answer,
            explanation=explanation,
            points=points,
            order_index=order_index
        )
        
        self.db.add(question)
        await self.db.commit()
        await self.db.refresh(question)
        
        return question
        
    async def submit_quiz(
        self,
        user_id: int,
        quiz_id: int,
        answers: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Submit quiz answers and calculate results.
        
        Returns:
            Dict containing score, passed status, feedback, and certificate info
        """
        # Get quiz with questions
        quiz = await self.get_quiz(quiz_id, include_answers=True)
        if not quiz:
            raise NotFoundError("Quiz not found")
            
        # Check if user has attempts remaining
        progress = await self._get_user_progress(user_id, quiz.course_id)
        if not progress:
            raise PermissionError("User not enrolled in this course")
            
        # Calculate score
        score, total_points = quiz.calculate_score(answers)
        percentage = (score / total_points * 100) if total_points > 0 else 0
        passed = percentage >= quiz.passing_score
        
        # Generate feedback
        feedback = []
        for question in quiz.questions:
            question_id = str(question.id)
            user_answer = answers.get(question_id, "")
            is_correct = user_answer == question.correct_answer
            
            feedback.append({
                "question_id": question_id,
                "correct": is_correct,
                "user_answer": user_answer,
                "correct_answer": question.correct_answer if not is_correct else None,
                "explanation": question.explanation if not is_correct else None,
                "points_earned": question.points if is_correct else 0
            })
            
        # Update progress if passed
        certificate_id = None
        if passed:
            progress.complete_course()
            await self.db.commit()
            
            # Generate certificate
            certificate = await self._generate_certificate(
                user_id, quiz.course_id, percentage, progress
            )
            certificate_id = certificate.id
            
            # Award points and check badges
            await self._award_completion_points(user_id, percentage)
            
        logger.info(
            f"User {user_id} submitted quiz {quiz_id}: "
            f"Score: {percentage:.1f}% ({'passed' if passed else 'failed'})"
        )
        
        return {
            "score": percentage,
            "passed": passed,
            "passing_score": quiz.passing_score,
            "correct_answers": score,
            "total_questions": len(quiz.questions),
            "points_earned": score,
            "total_points": total_points,
            "feedback": feedback,
            "certificate_id": certificate_id
        }
        
    async def _get_user_progress(self, user_id: int, course_id: int) -> Optional[UserCourseProgress]:
        """Get user's course progress."""
        result = await self.db.execute(
            select(UserCourseProgress).where(
                and_(
                    UserCourseProgress.user_id == user_id,
                    UserCourseProgress.course_id == course_id
                )
            )
        )
        return result.scalar_one_or_none()
        
    async def _generate_certificate(
        self,
        user_id: int,
        course_id: int,
        score: float,
        progress: UserCourseProgress
    ) -> Certificate:
        """Generate a certificate for course completion."""
        # Generate unique certificate number and verification code
        cert_number = self._generate_certificate_number()
        verification_code = self._generate_verification_code()
        
        # Calculate time spent
        time_spent_hours = 0
        if progress.started_at and progress.completed_at:
            time_diff = progress.completed_at - progress.started_at
            time_spent_hours = int(time_diff.total_seconds() / 3600)
        
        certificate = Certificate(
            user_id=user_id,
            course_id=course_id,
            company_id=progress.company_id,
            certificate_number=cert_number,
            verification_code=verification_code,
            completion_date=progress.completed_at or datetime.utcnow(),
            final_score=int(score),
            time_spent_hours=time_spent_hours
        )
        
        self.db.add(certificate)
        await self.db.commit()
        await self.db.refresh(certificate)
        
        # Update progress with certificate
        progress.certificate_issued = True
        progress.certificate_url = f"/api/v1/certificates/{certificate.id}"
        await self.db.commit()
        
        logger.info(f"Generated certificate {cert_number} for user {user_id}")
        return certificate
        
    def _generate_certificate_number(self) -> str:
        """Generate unique certificate number."""
        prefix = "CERT"
        timestamp = datetime.utcnow().strftime("%Y%m")
        random_part = ''.join(secrets.choice(string.digits) for _ in range(6))
        return f"{prefix}-{timestamp}-{random_part}"
        
    def _generate_verification_code(self) -> str:
        """Generate secure verification code."""
        return secrets.token_urlsafe(32)
        
    async def _award_completion_points(self, user_id: int, score: float) -> None:
        """Award points for course completion and check for badges."""
        # Get or create user points
        result = await self.db.execute(
            select(UserPoints).where(UserPoints.user_id == user_id)
        )
        user_points = result.scalar_one_or_none()
        
        if not user_points:
            user_points = UserPoints(user_id=user_id)
            self.db.add(user_points)
            
        # Calculate points based on score
        base_points = 50  # Base points for completion
        bonus_points = 0
        
        if score == 100:
            bonus_points = 50  # Perfect score bonus
            user_points.perfect_quizzes += 1
        elif score >= 90:
            bonus_points = 25  # High score bonus
            
        total_points = base_points + bonus_points
        new_level, leveled_up = user_points.add_points(total_points, "Course completion")
        
        # Update statistics
        user_points.courses_completed += 1
        user_points.update_streak(datetime.utcnow())
        
        await self.db.commit()
        
        # Check for badge eligibility
        await self._check_and_award_badges(user_id, user_points)
        
        logger.info(
            f"Awarded {total_points} points to user {user_id}. "
            f"New level: {new_level}, Leveled up: {leveled_up}"
        )
        
    async def _check_and_award_badges(self, user_id: int, user_points: UserPoints) -> None:
        """Check and award badges based on achievements."""
        # Get all active badges
        result = await self.db.execute(
            select(Badge).where(Badge.is_active == True)
        )
        badges = result.scalars().all()
        
        # Check each badge's requirements
        for badge in badges:
            # Skip if user already has this badge
            existing = await self.db.execute(
                select(UserBadge).where(
                    and_(
                        UserBadge.user_id == user_id,
                        UserBadge.badge_id == badge.id
                    )
                )
            )
            if existing.scalar_one_or_none():
                continue
                
            # Check requirements
            earned = False
            requirements = badge.requirements or {}
            
            if badge.badge_type == "completion":
                required_courses = requirements.get("courses_completed", 0)
                if user_points.courses_completed >= required_courses:
                    earned = True
                    
            elif badge.badge_type == "streak":
                required_streak = requirements.get("streak_days", 0)
                if user_points.current_streak_days >= required_streak:
                    earned = True
                    
            elif badge.badge_type == "score":
                required_perfect = requirements.get("perfect_quizzes", 0)
                if user_points.perfect_quizzes >= required_perfect:
                    earned = True
                    
            elif badge.badge_type == "special":
                # Special badges have custom requirements
                if requirements.get("total_points", 0) <= user_points.total_points:
                    earned = True
                    
            if earned:
                # Award badge
                user_badge = UserBadge(
                    user_id=user_id,
                    badge_id=badge.id,
                    points_awarded=badge.points_value,
                    earned_for={
                        "courses_completed": user_points.courses_completed,
                        "current_streak": user_points.current_streak_days,
                        "perfect_quizzes": user_points.perfect_quizzes,
                        "total_points": user_points.total_points
                    }
                )
                self.db.add(user_badge)
                
                # Add badge points
                user_points.add_points(badge.points_value, f"Badge: {badge.name}")
                
                logger.info(f"Awarded badge '{badge.name}' to user {user_id}")
                
        await self.db.commit()
        
    async def get_quiz_attempts(self, user_id: int, quiz_id: int) -> List[Dict[str, Any]]:
        """Get user's quiz attempt history."""
        # This would typically query a quiz_attempts table
        # For now, return empty list as the table doesn't exist yet
        return []
        
    async def update_quiz(
        self,
        quiz_id: int,
        updates: Dict[str, Any]
    ) -> Quiz:
        """Update quiz details."""
        quiz = await self.get_quiz(quiz_id)
        if not quiz:
            raise NotFoundError("Quiz not found")
            
        # Update fields
        for field, value in updates.items():
            if hasattr(quiz, field):
                setattr(quiz, field, value)
                
        quiz.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(quiz)
        
        return quiz
        
    async def delete_quiz(self, quiz_id: int) -> bool:
        """Delete a quiz and all its questions."""
        quiz = await self.get_quiz(quiz_id)
        if not quiz:
            raise NotFoundError("Quiz not found")
            
        await self.db.delete(quiz)
        await self.db.commit()
        
        logger.info(f"Deleted quiz: {quiz_id}")
        return True