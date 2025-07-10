"""Course management service for creating and managing training content."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.course import (
    Course, Module, Lesson, Quiz, Question, 
    UserCourseProgress, UserLessonProgress, UserQuizAttempt
)
from models.user import User
from models.analytics import AnalyticsEvent
from core.logging import logger
from core.exceptions import ValidationError, NotFoundError


class CourseService:
    """Service for managing courses, modules, lessons, and quizzes."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        
    # Course Management
    async def create_course(
        self,
        title: str,
        description: str,
        category: str,
        difficulty: str,
        duration_hours: int,
        created_by_id: int,
        is_published: bool = False,
        tags: Optional[List[str]] = None,
        prerequisites: Optional[List[int]] = None,
    ) -> Course:
        """Create a new course."""
        # Validate difficulty
        valid_difficulties = ["beginner", "intermediate", "advanced"]
        if difficulty not in valid_difficulties:
            raise ValidationError(f"Invalid difficulty. Must be one of: {valid_difficulties}")
            
        # Create course
        course = Course(
            title=title,
            description=description,
            category=category,
            difficulty=difficulty,
            duration_hours=duration_hours,
            created_by_id=created_by_id,
            is_published=is_published,
            tags=tags or [],
            prerequisites=prerequisites or [],
        )
        
        self.db.add(course)
        await self.db.commit()
        await self.db.refresh(course)
        
        logger.info(f"Created course: {course.id} - {course.title}")
        return course
        
    async def update_course(
        self,
        course_id: int,
        updates: Dict[str, Any]
    ) -> Course:
        """Update course details."""
        course = await self.db.get(Course, course_id)
        if not course:
            raise NotFoundError("Course not found")
            
        # Update fields
        for field, value in updates.items():
            if hasattr(course, field):
                setattr(course, field, value)
                
        course.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(course)
        
        return course
        
    async def get_course_with_content(self, course_id: int) -> Optional[Course]:
        """Get course with all modules, lessons, and quizzes."""
        result = await self.db.execute(
            select(Course)
            .options(
                selectinload(Course.modules).selectinload(Module.lessons),
                selectinload(Course.quizzes)
            )
            .where(Course.id == course_id)
        )
        return result.scalar_one_or_none()
        
    # Module Management
    async def create_module(
        self,
        course_id: int,
        title: str,
        description: str,
        order_index: int,
        duration_minutes: int = 30,
    ) -> Module:
        """Create a new module in a course."""
        # Verify course exists
        course = await self.db.get(Course, course_id)
        if not course:
            raise NotFoundError("Course not found")
            
        module = Module(
            course_id=course_id,
            title=title,
            description=description,
            order_index=order_index,
            duration_minutes=duration_minutes,
        )
        
        self.db.add(module)
        await self.db.commit()
        await self.db.refresh(module)
        
        return module
        
    # Lesson Management
    async def create_lesson(
        self,
        module_id: int,
        title: str,
        content_type: str,
        content: Dict[str, Any],
        order_index: int,
        duration_minutes: int = 10,
    ) -> Lesson:
        """Create a new lesson in a module."""
        # Validate content type
        valid_types = ["video", "text", "interactive", "pdf", "quiz"]
        if content_type not in valid_types:
            raise ValidationError(f"Invalid content type. Must be one of: {valid_types}")
            
        # Verify module exists
        module = await self.db.get(Module, module_id)
        if not module:
            raise NotFoundError("Module not found")
            
        lesson = Lesson(
            module_id=module_id,
            title=title,
            content_type=content_type,
            content=content,
            order_index=order_index,
            duration_minutes=duration_minutes,
        )
        
        self.db.add(lesson)
        await self.db.commit()
        await self.db.refresh(lesson)
        
        return lesson
        
    # Quiz Management
    async def create_quiz(
        self,
        course_id: int,
        title: str,
        description: str,
        passing_score: int = 70,
        time_limit_minutes: Optional[int] = None,
        max_attempts: int = 3,
    ) -> Quiz:
        """Create a new quiz for a course."""
        # Verify course exists
        course = await self.db.get(Course, course_id)
        if not course:
            raise NotFoundError("Course not found")
            
        quiz = Quiz(
            course_id=course_id,
            title=title,
            description=description,
            passing_score=passing_score,
            time_limit_minutes=time_limit_minutes,
            max_attempts=max_attempts,
        )
        
        self.db.add(quiz)
        await self.db.commit()
        await self.db.refresh(quiz)
        
        return quiz
        
    async def add_question_to_quiz(
        self,
        quiz_id: int,
        question_text: str,
        question_type: str,
        options: Optional[List[str]] = None,
        correct_answer: Optional[str] = None,
        correct_answers: Optional[List[str]] = None,
        explanation: Optional[str] = None,
        points: int = 1,
        order_index: int = 0,
    ) -> Question:
        """Add a question to a quiz."""
        # Validate question type
        valid_types = ["single_choice", "multiple_choice", "true_false", "short_answer"]
        if question_type not in valid_types:
            raise ValidationError(f"Invalid question type. Must be one of: {valid_types}")
            
        # Verify quiz exists
        quiz = await self.db.get(Quiz, quiz_id)
        if not quiz:
            raise NotFoundError("Quiz not found")
            
        question = Question(
            quiz_id=quiz_id,
            question_text=question_text,
            question_type=question_type,
            options=options,
            correct_answer=correct_answer,
            correct_answers=correct_answers,
            explanation=explanation,
            points=points,
            order_index=order_index,
        )
        
        self.db.add(question)
        await self.db.commit()
        await self.db.refresh(question)
        
        return question
        
    # User Progress Management
    async def enroll_user(
        self,
        user_id: int,
        course_id: int,
        enrolled_by_id: Optional[int] = None,
    ) -> UserCourseProgress:
        """Enroll a user in a course."""
        # Check if already enrolled
        existing_query = select(UserCourseProgress).where(
            and_(
                UserCourseProgress.user_id == user_id,
                UserCourseProgress.course_id == course_id,
            )
        )
        existing_result = await self.db.execute(existing_query)
        existing = existing_result.scalar_one_or_none()
        
        if existing:
            return existing
            
        # Create enrollment
        enrollment = UserCourseProgress(
            user_id=user_id,
            course_id=course_id,
            enrolled_by_id=enrolled_by_id or user_id,
            status="enrolled",
            progress_percentage=0,
        )
        
        self.db.add(enrollment)
        
        # Log enrollment event
        event = AnalyticsEvent.log_event(
            event_type=AnalyticsEvent.EventType.COURSE_STARTED,
            event_category=AnalyticsEvent.EventCategory.COURSE,
            user_id=user_id,
            event_data={"course_id": course_id}
        )
        self.db.add(event)
        
        await self.db.commit()
        await self.db.refresh(enrollment)
        
        return enrollment
        
    async def update_lesson_progress(
        self,
        user_id: int,
        lesson_id: int,
        completed: bool = False,
        time_spent_seconds: Optional[int] = None,
    ) -> UserLessonProgress:
        """Update user's progress on a lesson."""
        # Get or create lesson progress
        progress_query = select(UserLessonProgress).where(
            and_(
                UserLessonProgress.user_id == user_id,
                UserLessonProgress.lesson_id == lesson_id,
            )
        )
        progress_result = await self.db.execute(progress_query)
        progress = progress_result.scalar_one_or_none()
        
        if not progress:
            # Get lesson to find module and course
            lesson_query = select(Lesson).options(
                selectinload(Lesson.module)
            ).where(Lesson.id == lesson_id)
            lesson_result = await self.db.execute(lesson_query)
            lesson = lesson_result.scalar_one_or_none()
            
            if not lesson:
                raise NotFoundError("Lesson not found")
                
            progress = UserLessonProgress(
                user_id=user_id,
                lesson_id=lesson_id,
                module_id=lesson.module_id,
                completed=completed,
                time_spent_seconds=time_spent_seconds or 0,
            )
            self.db.add(progress)
        else:
            progress.completed = completed
            if time_spent_seconds:
                progress.time_spent_seconds += time_spent_seconds
                
        if completed and not progress.completed_at:
            progress.completed_at = datetime.utcnow()
            
        await self.db.commit()
        await self.db.refresh(progress)
        
        # Update course progress
        await self._update_course_progress(user_id, lesson.module.course_id)
        
        return progress
        
    async def submit_quiz_attempt(
        self,
        user_id: int,
        quiz_id: int,
        answers: Dict[int, Any],
    ) -> UserQuizAttempt:
        """Submit a quiz attempt and calculate score."""
        # Get quiz with questions
        quiz_query = select(Quiz).options(
            selectinload(Quiz.questions)
        ).where(Quiz.id == quiz_id)
        quiz_result = await self.db.execute(quiz_query)
        quiz = quiz_result.scalar_one_or_none()
        
        if not quiz:
            raise NotFoundError("Quiz not found")
            
        # Check attempt limit
        attempts_query = select(func.count(UserQuizAttempt.id)).where(
            and_(
                UserQuizAttempt.user_id == user_id,
                UserQuizAttempt.quiz_id == quiz_id,
            )
        )
        attempts_result = await self.db.execute(attempts_query)
        attempt_count = attempts_result.scalar() or 0
        
        if attempt_count >= quiz.max_attempts:
            raise ValidationError(f"Maximum attempts ({quiz.max_attempts}) exceeded")
            
        # Calculate score
        total_points = 0
        earned_points = 0
        question_results = {}
        
        for question in quiz.questions:
            total_points += question.points
            user_answer = answers.get(question.id)
            
            is_correct = self._check_answer(question, user_answer)
            if is_correct:
                earned_points += question.points
                
            question_results[question.id] = {
                "question": question.question_text,
                "user_answer": user_answer,
                "correct_answer": question.correct_answer or question.correct_answers,
                "is_correct": is_correct,
                "points": question.points if is_correct else 0,
            }
            
        score_percentage = (earned_points / total_points * 100) if total_points > 0 else 0
        passed = score_percentage >= quiz.passing_score
        
        # Create attempt record
        attempt = UserQuizAttempt(
            user_id=user_id,
            quiz_id=quiz_id,
            course_id=quiz.course_id,
            answers=answers,
            score=round(score_percentage, 2),
            passed=passed,
            time_taken_seconds=None,  # TODO: Track time
            completed_at=datetime.utcnow(),
        )
        
        self.db.add(attempt)
        
        # Log quiz completion
        event = AnalyticsEvent.log_event(
            event_type=AnalyticsEvent.EventType.QUIZ_COMPLETED,
            event_category=AnalyticsEvent.EventCategory.COURSE,
            user_id=user_id,
            event_data={
                "quiz_id": quiz_id,
                "score": score_percentage,
                "passed": passed,
            }
        )
        self.db.add(event)
        
        await self.db.commit()
        await self.db.refresh(attempt)
        
        # Update course progress if passed
        if passed:
            await self._update_course_progress(user_id, quiz.course_id)
            
        return attempt
        
    def _check_answer(self, question: Question, user_answer: Any) -> bool:
        """Check if user's answer is correct."""
        if question.question_type == "single_choice":
            return str(user_answer) == str(question.correct_answer)
        elif question.question_type == "multiple_choice":
            if not isinstance(user_answer, list):
                return False
            user_set = set(str(a) for a in user_answer)
            correct_set = set(str(a) for a in question.correct_answers or [])
            return user_set == correct_set
        elif question.question_type == "true_false":
            return str(user_answer).lower() == str(question.correct_answer).lower()
        elif question.question_type == "short_answer":
            # Simple text comparison (case-insensitive)
            return str(user_answer).strip().lower() == str(question.correct_answer).strip().lower()
        return False
        
    async def _update_course_progress(self, user_id: int, course_id: int):
        """Update overall course progress based on completed lessons and quizzes."""
        # Get course with all content
        course = await self.get_course_with_content(course_id)
        if not course:
            return
            
        # Count total lessons
        total_lessons = sum(len(module.lessons) for module in course.modules)
        
        # Count completed lessons
        completed_query = select(func.count(UserLessonProgress.id)).join(
            Lesson, UserLessonProgress.lesson_id == Lesson.id
        ).join(
            Module, Lesson.module_id == Module.id
        ).where(
            and_(
                Module.course_id == course_id,
                UserLessonProgress.user_id == user_id,
                UserLessonProgress.completed == True,
            )
        )
        completed_result = await self.db.execute(completed_query)
        completed_lessons = completed_result.scalar() or 0
        
        # Calculate progress percentage
        progress_percentage = (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0
        
        # Get course progress record
        progress_query = select(UserCourseProgress).where(
            and_(
                UserCourseProgress.user_id == user_id,
                UserCourseProgress.course_id == course_id,
            )
        )
        progress_result = await self.db.execute(progress_query)
        progress = progress_result.scalar_one_or_none()
        
        if progress:
            progress.progress_percentage = round(progress_percentage, 2)
            progress.last_accessed_at = datetime.utcnow()
            
            # Check if course is completed
            if progress_percentage >= 100:
                # Check if quiz is passed (if required)
                quiz_passed = True
                if course.quizzes:
                    quiz_query = select(UserQuizAttempt).where(
                        and_(
                            UserQuizAttempt.user_id == user_id,
                            UserQuizAttempt.course_id == course_id,
                            UserQuizAttempt.passed == True,
                        )
                    )
                    quiz_result = await self.db.execute(quiz_query)
                    quiz_attempt = quiz_result.scalar_one_or_none()
                    quiz_passed = quiz_attempt is not None
                    
                    if quiz_attempt:
                        progress.quiz_score = quiz_attempt.score
                        
                if quiz_passed:
                    progress.status = "completed"
                    progress.completed_at = datetime.utcnow()
                    
                    # Log completion event
                    event = AnalyticsEvent.log_event(
                        event_type=AnalyticsEvent.EventType.COURSE_COMPLETED,
                        event_category=AnalyticsEvent.EventCategory.COURSE,
                        user_id=user_id,
                        event_data={"course_id": course_id}
                    )
                    self.db.add(event)
            else:
                progress.status = "in_progress"
                
            await self.db.commit()
            
    # Search and Discovery
    async def search_courses(
        self,
        search_term: Optional[str] = None,
        category: Optional[str] = None,
        difficulty: Optional[str] = None,
        is_published: bool = True,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Course]:
        """Search for courses based on criteria."""
        query = select(Course)
        
        # Apply filters
        filters = []
        if is_published is not None:
            filters.append(Course.is_published == is_published)
            
        if search_term:
            search_pattern = f"%{search_term}%"
            filters.append(
                or_(
                    Course.title.ilike(search_pattern),
                    Course.description.ilike(search_pattern),
                )
            )
            
        if category:
            filters.append(Course.category == category)
            
        if difficulty:
            filters.append(Course.difficulty == difficulty)
            
        if filters:
            query = query.where(and_(*filters))
            
        # Apply pagination
        query = query.offset(offset).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
        
    async def get_user_courses(
        self,
        user_id: int,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get courses for a specific user with progress."""
        query = select(
            UserCourseProgress,
            Course
        ).join(
            Course, UserCourseProgress.course_id == Course.id
        ).where(UserCourseProgress.user_id == user_id)
        
        if status:
            query = query.where(UserCourseProgress.status == status)
            
        result = await self.db.execute(query)
        
        courses = []
        for progress, course in result:
            courses.append({
                "course": course,
                "enrollment": progress,
                "progress_percentage": progress.progress_percentage,
                "status": progress.status,
                "enrolled_at": progress.created_at,
                "completed_at": progress.completed_at,
                "last_accessed_at": progress.last_accessed_at,
                "quiz_score": progress.quiz_score,
                "certificate_issued": progress.certificate_issued,
            })
            
        return courses
        
    async def get_course_analytics(self, course_id: int) -> Dict[str, Any]:
        """Get analytics for a specific course."""
        # Get enrollment count
        enrollment_query = select(func.count(UserCourseProgress.id)).where(
            UserCourseProgress.course_id == course_id
        )
        enrollment_result = await self.db.execute(enrollment_query)
        total_enrollments = enrollment_result.scalar() or 0
        
        # Get completion count
        completion_query = select(func.count(UserCourseProgress.id)).where(
            and_(
                UserCourseProgress.course_id == course_id,
                UserCourseProgress.status == "completed",
            )
        )
        completion_result = await self.db.execute(completion_query)
        completions = completion_result.scalar() or 0
        
        # Get average progress
        avg_progress_query = select(func.avg(UserCourseProgress.progress_percentage)).where(
            UserCourseProgress.course_id == course_id
        )
        avg_progress_result = await self.db.execute(avg_progress_query)
        avg_progress = avg_progress_result.scalar() or 0
        
        # Get average quiz score
        avg_score_query = select(func.avg(UserCourseProgress.quiz_score)).where(
            and_(
                UserCourseProgress.course_id == course_id,
                UserCourseProgress.quiz_score.isnot(None),
            )
        )
        avg_score_result = await self.db.execute(avg_score_query)
        avg_quiz_score = avg_score_result.scalar() or 0
        
        # Calculate completion rate
        completion_rate = (completions / total_enrollments * 100) if total_enrollments > 0 else 0
        
        return {
            "course_id": course_id,
            "total_enrollments": total_enrollments,
            "completions": completions,
            "completion_rate": round(completion_rate, 2),
            "average_progress": round(float(avg_progress), 2),
            "average_quiz_score": round(float(avg_quiz_score), 2),
        }