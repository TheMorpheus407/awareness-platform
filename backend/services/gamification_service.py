"""Gamification service for managing badges, points, and achievements."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import select, and_, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.course import Badge, UserBadge, UserPoints
from models.user import User
from core.logging import logger
from core.exceptions import NotFoundError, ValidationError


class GamificationService:
    """Service for managing gamification features."""
    
    # Point values for different actions
    POINTS_CONFIG = {
        "course_completion": 50,
        "perfect_quiz": 50,
        "high_score_quiz": 25,  # 90%+
        "daily_activity": 10,
        "weekly_streak": 50,
        "monthly_streak": 200,
        "first_course": 100,
        "level_up": 25,
        "badge_earned": 0,  # Badge points are defined per badge
    }
    
    # Level thresholds
    LEVEL_CONFIG = {
        1: 0,
        2: 100,
        3: 250,
        4: 500,
        5: 1000,
        6: 1750,
        7: 2750,
        8: 4000,
        9: 5500,
        10: 7500,
    }
    
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def get_user_points(self, user_id: int) -> UserPoints:
        """Get or create user points record."""
        result = await self.db.execute(
            select(UserPoints).where(UserPoints.user_id == user_id)
        )
        user_points = result.scalar_one_or_none()
        
        if not user_points:
            user_points = UserPoints(user_id=user_id)
            self.db.add(user_points)
            await self.db.commit()
            await self.db.refresh(user_points)
            
        return user_points
        
    async def award_points(
        self,
        user_id: int,
        points: int,
        reason: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Award points to a user.
        
        Returns:
            Dict with new total, level info, and any badges earned
        """
        user_points = await self.get_user_points(user_id)
        old_level = user_points.current_level
        
        # Add points
        new_level, leveled_up = user_points.add_points(points, reason)
        
        # Award level up bonus
        if leveled_up:
            bonus_points = self.POINTS_CONFIG["level_up"] * (new_level - old_level)
            user_points.add_points(bonus_points, f"Level up bonus (Level {new_level})")
            
        await self.db.commit()
        
        # Check for new badges
        new_badges = await self._check_and_award_badges(user_id, user_points, context)
        
        logger.info(
            f"Awarded {points} points to user {user_id} for '{reason}'. "
            f"Total: {user_points.total_points}, Level: {new_level}"
        )
        
        return {
            "points_awarded": points,
            "total_points": user_points.total_points,
            "current_level": new_level,
            "leveled_up": leveled_up,
            "points_to_next_level": user_points.points_to_next_level,
            "new_badges": new_badges
        }
        
    async def get_user_badges(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all badges earned by a user."""
        result = await self.db.execute(
            select(UserBadge)
            .where(UserBadge.user_id == user_id)
            .options(selectinload(UserBadge.badge))
            .order_by(UserBadge.earned_at.desc())
        )
        user_badges = result.scalars().all()
        
        return [
            {
                "badge_id": ub.badge_id,
                "name": ub.badge.name,
                "description": ub.badge.description,
                "icon_url": ub.badge.icon_url,
                "badge_type": ub.badge.badge_type,
                "points_awarded": ub.points_awarded,
                "earned_at": ub.earned_at.isoformat(),
                "earned_for": ub.earned_for
            }
            for ub in user_badges
        ]
        
    async def get_available_badges(self) -> List[Dict[str, Any]]:
        """Get all available badges."""
        result = await self.db.execute(
            select(Badge)
            .where(Badge.is_active == True)
            .order_by(Badge.badge_type, Badge.points_value)
        )
        badges = result.scalars().all()
        
        return [
            {
                "id": badge.id,
                "name": badge.name,
                "description": badge.description,
                "icon_url": badge.icon_url,
                "badge_type": badge.badge_type,
                "points_value": badge.points_value,
                "requirements": badge.requirements
            }
            for badge in badges
        ]
        
    async def create_badge(
        self,
        name: str,
        description: str,
        badge_type: str,
        requirements: Dict[str, Any],
        points_value: int = 10,
        icon_url: Optional[str] = None
    ) -> Badge:
        """Create a new badge."""
        valid_types = ["completion", "streak", "score", "special"]
        if badge_type not in valid_types:
            raise ValidationError(f"Invalid badge type. Must be one of: {valid_types}")
            
        badge = Badge(
            name=name,
            description=description,
            icon_url=icon_url,
            badge_type=badge_type,
            requirements=requirements,
            points_value=points_value,
            is_active=True
        )
        
        self.db.add(badge)
        await self.db.commit()
        await self.db.refresh(badge)
        
        logger.info(f"Created badge: {badge.name} ({badge.badge_type})")
        return badge
        
    async def _check_and_award_badges(
        self,
        user_id: int,
        user_points: UserPoints,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Check and award badges based on current achievements."""
        new_badges = []
        
        # Get all active badges
        result = await self.db.execute(
            select(Badge).where(Badge.is_active == True)
        )
        badges = result.scalars().all()
        
        # Get user's existing badges
        existing_result = await self.db.execute(
            select(UserBadge.badge_id).where(UserBadge.user_id == user_id)
        )
        existing_badge_ids = set(existing_result.scalars())
        
        for badge in badges:
            # Skip if already earned
            if badge.id in existing_badge_ids:
                continue
                
            # Check if badge requirements are met
            if self._check_badge_requirements(badge, user_points, context):
                # Award badge
                user_badge = UserBadge(
                    user_id=user_id,
                    badge_id=badge.id,
                    points_awarded=badge.points_value,
                    earned_for={
                        "total_points": user_points.total_points,
                        "current_level": user_points.current_level,
                        "courses_completed": user_points.courses_completed,
                        "perfect_quizzes": user_points.perfect_quizzes,
                        "current_streak": user_points.current_streak_days,
                        "context": context
                    }
                )
                self.db.add(user_badge)
                
                # Add badge points
                user_points.add_points(badge.points_value, f"Badge earned: {badge.name}")
                
                new_badges.append({
                    "badge_id": badge.id,
                    "name": badge.name,
                    "description": badge.description,
                    "icon_url": badge.icon_url,
                    "points_awarded": badge.points_value
                })
                
                logger.info(f"Awarded badge '{badge.name}' to user {user_id}")
                
        if new_badges:
            await self.db.commit()
            
        return new_badges
        
    def _check_badge_requirements(
        self,
        badge: Badge,
        user_points: UserPoints,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Check if badge requirements are met."""
        requirements = badge.requirements or {}
        
        if badge.badge_type == "completion":
            # Course completion badges
            required_courses = requirements.get("courses_completed", 0)
            if user_points.courses_completed >= required_courses:
                return True
                
        elif badge.badge_type == "streak":
            # Streak badges
            required_streak = requirements.get("streak_days", 0)
            if user_points.current_streak_days >= required_streak:
                return True
                
        elif badge.badge_type == "score":
            # Quiz score badges
            if "perfect_quizzes" in requirements:
                if user_points.perfect_quizzes >= requirements["perfect_quizzes"]:
                    return True
                    
        elif badge.badge_type == "special":
            # Special badges with custom requirements
            if "total_points" in requirements:
                if user_points.total_points >= requirements["total_points"]:
                    return True
                    
            if "level" in requirements:
                if user_points.current_level >= requirements["level"]:
                    return True
                    
            # Context-based special badges
            if context and "achievement" in requirements:
                achievement = requirements["achievement"]
                if context.get("achievement") == achievement:
                    return True
                    
        return False
        
    async def get_leaderboard(
        self,
        company_id: Optional[int] = None,
        timeframe: str = "all_time",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get points leaderboard.
        
        Args:
            company_id: Filter by company (optional)
            timeframe: 'all_time', 'monthly', 'weekly'
            limit: Number of top users to return
        """
        query = (
            select(UserPoints, User)
            .join(User, UserPoints.user_id == User.id)
            .order_by(UserPoints.total_points.desc())
            .limit(limit)
        )
        
        if company_id:
            query = query.where(User.company_id == company_id)
            
        result = await self.db.execute(query)
        leaderboard = []
        
        for idx, (points, user) in enumerate(result):
            leaderboard.append({
                "rank": idx + 1,
                "user_id": user.id,
                "user_name": user.full_name,
                "total_points": points.total_points,
                "current_level": points.current_level,
                "courses_completed": points.courses_completed,
                "perfect_quizzes": points.perfect_quizzes,
                "current_streak": points.current_streak_days
            })
            
        return leaderboard
        
    async def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive gamification stats for a user."""
        user_points = await self.get_user_points(user_id)
        badges = await self.get_user_badges(user_id)
        
        # Calculate progress to next level
        current_threshold = self.LEVEL_CONFIG.get(user_points.current_level, 0)
        next_threshold = user_points.points_to_next_level
        progress_to_next = (
            (user_points.total_points - current_threshold) / 
            (next_threshold - current_threshold) * 100
        ) if next_threshold > current_threshold else 100
        
        # Get user rank
        rank_result = await self.db.execute(
            select(func.count(UserPoints.id))
            .where(UserPoints.total_points > user_points.total_points)
        )
        rank = (rank_result.scalar() or 0) + 1
        
        return {
            "user_id": user_id,
            "total_points": user_points.total_points,
            "current_level": user_points.current_level,
            "points_to_next_level": user_points.points_to_next_level,
            "progress_to_next_level": round(progress_to_next, 2),
            "global_rank": rank,
            "badges_earned": len(badges),
            "total_badges_available": await self._count_available_badges(),
            "courses_completed": user_points.courses_completed,
            "perfect_quizzes": user_points.perfect_quizzes,
            "current_streak_days": user_points.current_streak_days,
            "longest_streak_days": user_points.longest_streak_days,
            "last_activity": user_points.last_activity_date.isoformat() if user_points.last_activity_date else None
        }
        
    async def _count_available_badges(self) -> int:
        """Count total available badges."""
        result = await self.db.execute(
            select(func.count(Badge.id)).where(Badge.is_active == True)
        )
        return result.scalar() or 0
        
    async def update_daily_streak(self, user_id: int) -> Dict[str, Any]:
        """Update user's daily streak and award streak points if applicable."""
        user_points = await self.get_user_points(user_id)
        old_streak = user_points.current_streak_days
        
        # Update streak
        user_points.update_streak(datetime.utcnow())
        
        # Award streak milestone points
        streak_rewards = {
            7: ("weekly_streak", "7-day streak"),
            30: ("monthly_streak", "30-day streak"),
            60: ("monthly_streak", "60-day streak"),
            90: ("monthly_streak", "90-day streak"),
            365: ("monthly_streak", "365-day streak")
        }
        
        points_awarded = 0
        milestone_reached = None
        
        for days, (config_key, description) in streak_rewards.items():
            if old_streak < days <= user_points.current_streak_days:
                points = self.POINTS_CONFIG.get(config_key, 50)
                user_points.add_points(points, f"Milestone: {description}")
                points_awarded += points
                milestone_reached = description
                
        await self.db.commit()
        
        return {
            "current_streak": user_points.current_streak_days,
            "longest_streak": user_points.longest_streak_days,
            "points_awarded": points_awarded,
            "milestone_reached": milestone_reached
        }