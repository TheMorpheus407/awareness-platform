"""Progress tracking service for monitoring user learning progress."""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy import select, and_, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.course import (
    Course, Module, Lesson, UserCourseProgress, 
    UserLessonProgress, UserPoints
)
from models.user import User
from models.company import Company
from core.logging import logger
from core.exceptions import NotFoundError, ValidationError


class ProgressService:
    """Service for tracking and managing user progress."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def enroll_user(
        self,
        user_id: int,
        course_id: int,
        company_id: int,
        enrolled_by_id: Optional[int] = None
    ) -> UserCourseProgress:
        """Enroll a user in a course."""
        # Check if already enrolled
        existing = await self.db.execute(
            select(UserCourseProgress).where(
                and_(
                    UserCourseProgress.user_id == user_id,
                    UserCourseProgress.course_id == course_id
                )
            )
        )
        if existing.scalar_one_or_none():
            raise ValidationError("User already enrolled in this course")
            
        # Create enrollment
        progress = UserCourseProgress(
            user_id=user_id,
            course_id=course_id,
            company_id=company_id,
            status='not_started',
            progress_percentage=0
        )
        
        self.db.add(progress)
        await self.db.commit()
        await self.db.refresh(progress)
        
        logger.info(f"Enrolled user {user_id} in course {course_id}")
        return progress
        
    async def get_user_course_progress(
        self,
        user_id: int,
        course_id: int
    ) -> Optional[UserCourseProgress]:
        """Get user's progress for a specific course."""
        result = await self.db.execute(
            select(UserCourseProgress)
            .where(
                and_(
                    UserCourseProgress.user_id == user_id,
                    UserCourseProgress.course_id == course_id
                )
            )
            .options(selectinload(UserCourseProgress.course))
        )
        return result.scalar_one_or_none()
        
    async def get_user_enrolled_courses(
        self,
        user_id: int,
        status: Optional[str] = None
    ) -> List[UserCourseProgress]:
        """Get all courses a user is enrolled in."""
        query = select(UserCourseProgress).where(
            UserCourseProgress.user_id == user_id
        ).options(selectinload(UserCourseProgress.course))
        
        if status:
            query = query.where(UserCourseProgress.status == status)
            
        result = await self.db.execute(query)
        return list(result.scalars())
        
    async def update_lesson_progress(
        self,
        user_id: int,
        lesson_id: int,
        progress_data: Dict[str, Any]
    ) -> UserLessonProgress:
        """Update progress for a specific lesson."""
        # Get lesson details
        lesson_result = await self.db.execute(
            select(Lesson)
            .where(Lesson.id == lesson_id)
            .options(
                selectinload(Lesson.module).selectinload(Module.course)
            )
        )
        lesson = lesson_result.scalar_one_or_none()
        if not lesson:
            raise NotFoundError("Lesson not found")
            
        # Get or create lesson progress
        progress_result = await self.db.execute(
            select(UserLessonProgress).where(
                and_(
                    UserLessonProgress.user_id == user_id,
                    UserLessonProgress.lesson_id == lesson_id
                )
            )
        )
        lesson_progress = progress_result.scalar_one_or_none()
        
        if not lesson_progress:
            lesson_progress = UserLessonProgress(
                user_id=user_id,
                lesson_id=lesson_id,
                module_id=lesson.module_id,
                course_id=lesson.module.course_id,
                status='not_started',
                progress_percentage=0
            )
            self.db.add(lesson_progress)
            
        # Update progress based on content type
        if lesson.content_type == 'video' and 'video_progress_seconds' in progress_data:
            lesson_progress.update_video_progress(
                progress_data['video_progress_seconds'],
                progress_data.get('video_total_seconds', 0)
            )
        elif lesson.content_type == 'text' and progress_data.get('completed'):
            lesson_progress.mark_complete()
        elif lesson.content_type == 'interactive' and 'interactions_completed' in progress_data:
            lesson_progress.interactions_completed = progress_data['interactions_completed']
            # Check if all interactions are completed
            if self._check_interactions_complete(
                progress_data['interactions_completed'],
                lesson.interactive_elements
            ):
                lesson_progress.mark_complete()
                
        # Update time spent
        if 'time_spent_seconds' in progress_data:
            lesson_progress.time_spent_seconds += progress_data['time_spent_seconds']
            
        # Update status
        if lesson_progress.status == 'not_started' and lesson_progress.progress_percentage > 0:
            lesson_progress.status = 'in_progress'
            lesson_progress.started_at = datetime.utcnow()
            
        lesson_progress.last_accessed_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(lesson_progress)
        
        # Update course progress
        await self._update_course_progress(user_id, lesson.module.course_id)
        
        return lesson_progress
        
    async def _update_course_progress(self, user_id: int, course_id: int) -> None:
        """Update overall course progress based on lesson completion."""
        # Get course with modules and lessons
        course_result = await self.db.execute(
            select(Course)
            .where(Course.id == course_id)
            .options(
                selectinload(Course.modules).selectinload(Module.lessons)
            )
        )
        course = course_result.scalar_one_or_none()
        if not course:
            return
            
        # Count total and completed lessons
        total_lessons = sum(len(module.lessons) for module in course.modules)
        if total_lessons == 0:
            return
            
        # Get completed lessons count
        completed_result = await self.db.execute(
            select(func.count(UserLessonProgress.id))
            .where(
                and_(
                    UserLessonProgress.user_id == user_id,
                    UserLessonProgress.course_id == course_id,
                    UserLessonProgress.status == 'completed'
                )
            )
        )
        completed_lessons = completed_result.scalar() or 0
        
        # Update course progress
        progress_result = await self.db.execute(
            select(UserCourseProgress).where(
                and_(
                    UserCourseProgress.user_id == user_id,
                    UserCourseProgress.course_id == course_id
                )
            )
        )
        course_progress = progress_result.scalar_one_or_none()
        
        if course_progress:
            percentage = int((completed_lessons / total_lessons) * 100)
            course_progress.update_progress(percentage)
            
            # Update points for daily activity
            await self._update_daily_points(user_id)
            
            await self.db.commit()
            
    def _check_interactions_complete(
        self,
        completed: Dict[str, Any],
        required: Dict[str, Any]
    ) -> bool:
        """Check if all required interactions are completed."""
        if not required:
            return True
            
        required_ids = set(required.get('interaction_ids', []))
        completed_ids = set(completed.keys())
        
        return required_ids.issubset(completed_ids)
        
    async def _update_daily_points(self, user_id: int) -> None:
        """Update user points for daily activity."""
        # Get or create user points
        result = await self.db.execute(
            select(UserPoints).where(UserPoints.user_id == user_id)
        )
        user_points = result.scalar_one_or_none()
        
        if not user_points:
            user_points = UserPoints(user_id=user_id)
            self.db.add(user_points)
            
        # Update streak
        user_points.update_streak(datetime.utcnow())
        
        # Award daily activity points (once per day)
        today = datetime.utcnow().date()
        if user_points.last_activity_date and user_points.last_activity_date.date() < today:
            user_points.add_points(10, "Daily activity")
            
        await self.db.commit()
        
    async def get_course_analytics(self, course_id: int) -> Dict[str, Any]:
        """Get analytics for a specific course."""
        # Total enrollments
        enrollment_result = await self.db.execute(
            select(func.count(UserCourseProgress.id))
            .where(UserCourseProgress.course_id == course_id)
        )
        total_enrollments = enrollment_result.scalar() or 0
        
        # Active learners (accessed in last 7 days)
        active_date = datetime.utcnow() - timedelta(days=7)
        active_result = await self.db.execute(
            select(func.count(UserCourseProgress.id))
            .where(
                and_(
                    UserCourseProgress.course_id == course_id,
                    UserCourseProgress.status == 'in_progress',
                    UserCourseProgress.updated_at >= active_date
                )
            )
        )
        active_learners = active_result.scalar() or 0
        
        # Completion rate
        completed_result = await self.db.execute(
            select(func.count(UserCourseProgress.id))
            .where(
                and_(
                    UserCourseProgress.course_id == course_id,
                    UserCourseProgress.status == 'completed'
                )
            )
        )
        completed_count = completed_result.scalar() or 0
        completion_rate = (completed_count / total_enrollments * 100) if total_enrollments > 0 else 0
        
        # Average progress
        avg_progress_result = await self.db.execute(
            select(func.avg(UserCourseProgress.progress_percentage))
            .where(UserCourseProgress.course_id == course_id)
        )
        avg_progress = avg_progress_result.scalar() or 0
        
        return {
            "course_id": course_id,
            "total_enrollments": total_enrollments,
            "active_learners": active_learners,
            "completion_rate": round(completion_rate, 2),
            "average_progress": round(avg_progress, 2),
            "completed_count": completed_count
        }
        
    async def get_user_analytics(self, user_id: int) -> Dict[str, Any]:
        """Get learning analytics for a specific user."""
        # Get user points
        points_result = await self.db.execute(
            select(UserPoints).where(UserPoints.user_id == user_id)
        )
        user_points = points_result.scalar_one_or_none()
        
        # Count courses
        enrolled_result = await self.db.execute(
            select(func.count(UserCourseProgress.id))
            .where(UserCourseProgress.user_id == user_id)
        )
        total_enrolled = enrolled_result.scalar() or 0
        
        # Count completed courses
        completed_result = await self.db.execute(
            select(func.count(UserCourseProgress.id))
            .where(
                and_(
                    UserCourseProgress.user_id == user_id,
                    UserCourseProgress.status == 'completed'
                )
            )
        )
        completed_courses = completed_result.scalar() or 0
        
        # Count in progress courses
        in_progress_result = await self.db.execute(
            select(func.count(UserCourseProgress.id))
            .where(
                and_(
                    UserCourseProgress.user_id == user_id,
                    UserCourseProgress.status == 'in_progress'
                )
            )
        )
        in_progress_courses = in_progress_result.scalar() or 0
        
        # Calculate total time spent
        time_result = await self.db.execute(
            select(func.sum(UserLessonProgress.time_spent_seconds))
            .where(UserLessonProgress.user_id == user_id)
        )
        total_time_seconds = time_result.scalar() or 0
        total_time_hours = round(total_time_seconds / 3600, 1)
        
        return {
            "user_id": user_id,
            "total_enrolled": total_enrolled,
            "completed_courses": completed_courses,
            "in_progress_courses": in_progress_courses,
            "total_points": user_points.total_points if user_points else 0,
            "current_level": user_points.current_level if user_points else 1,
            "current_streak_days": user_points.current_streak_days if user_points else 0,
            "longest_streak_days": user_points.longest_streak_days if user_points else 0,
            "perfect_quizzes": user_points.perfect_quizzes if user_points else 0,
            "total_time_hours": total_time_hours,
            "completion_rate": round((completed_courses / total_enrolled * 100) if total_enrolled > 0 else 0, 2)
        }
        
    async def get_company_analytics(self, company_id: int) -> Dict[str, Any]:
        """Get learning analytics for a company."""
        # Total users
        users_result = await self.db.execute(
            select(func.count(User.id))
            .where(User.company_id == company_id)
        )
        total_users = users_result.scalar() or 0
        
        # Active learners
        active_date = datetime.utcnow() - timedelta(days=30)
        active_result = await self.db.execute(
            select(func.count(func.distinct(UserCourseProgress.user_id)))
            .where(
                and_(
                    UserCourseProgress.company_id == company_id,
                    UserCourseProgress.updated_at >= active_date
                )
            )
        )
        active_learners = active_result.scalar() or 0
        
        # Total enrollments
        enrollment_result = await self.db.execute(
            select(func.count(UserCourseProgress.id))
            .where(UserCourseProgress.company_id == company_id)
        )
        total_enrollments = enrollment_result.scalar() or 0
        
        # Completed courses
        completed_result = await self.db.execute(
            select(func.count(UserCourseProgress.id))
            .where(
                and_(
                    UserCourseProgress.company_id == company_id,
                    UserCourseProgress.status == 'completed'
                )
            )
        )
        completed_courses = completed_result.scalar() or 0
        
        # Average completion rate
        completion_rate = (completed_courses / total_enrollments * 100) if total_enrollments > 0 else 0
        
        return {
            "company_id": company_id,
            "total_users": total_users,
            "active_learners": active_learners,
            "total_enrollments": total_enrollments,
            "completed_courses": completed_courses,
            "average_completion_rate": round(completion_rate, 2),
            "engagement_rate": round((active_learners / total_users * 100) if total_users > 0 else 0, 2)
        }