"""Analytics service for generating reports and insights."""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy import select, func, and_, or_, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.analytics import AnalyticsEvent
from models.user import User, UserRole
from models.company import Company
from models.course import Course, UserCourseProgress
from models.phishing import PhishingCampaign, PhishingResult
from models.email_campaign import EmailCampaign, EmailLog
from core.logging import logger


class AnalyticsService:
    """Service for generating analytics and reports."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def get_dashboard_metrics(
        self,
        company_id: int,
        date_range: Optional[Tuple[datetime, datetime]] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive dashboard metrics for a company.
        
        Args:
            company_id: Company ID
            date_range: Optional date range (start, end)
            
        Returns:
            Dictionary containing various metrics
        """
        if not date_range:
            # Default to last 30 days
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)
            date_range = (start_date, end_date)
            
        metrics = {
            "overview": await self._get_overview_metrics(company_id, date_range),
            "user_activity": await self._get_user_activity_metrics(company_id, date_range),
            "course_performance": await self._get_course_performance_metrics(company_id, date_range),
            "phishing_stats": await self._get_phishing_stats(company_id, date_range),
            "security_score": await self._calculate_security_score(company_id),
            "trends": await self._get_trend_data(company_id, date_range),
            "top_performers": await self._get_top_performers(company_id, date_range),
            "risk_assessment": await self._get_risk_assessment(company_id),
        }
        
        return metrics
        
    async def _get_overview_metrics(
        self,
        company_id: int,
        date_range: Tuple[datetime, datetime]
    ) -> Dict[str, Any]:
        """Get overview metrics."""
        start_date, end_date = date_range
        
        # Total users
        total_users_query = select(func.count(User.id)).where(
            User.company_id == company_id,
            User.is_active == True
        )
        total_users_result = await self.db.execute(total_users_query)
        total_users = total_users_result.scalar() or 0
        
        # Active users (logged in within date range)
        active_users_query = select(func.count(func.distinct(AnalyticsEvent.user_id))).where(
            AnalyticsEvent.company_id == company_id,
            AnalyticsEvent.event_type == AnalyticsEvent.EventType.LOGIN,
            AnalyticsEvent.created_at.between(start_date, end_date)
        )
        active_users_result = await self.db.execute(active_users_query)
        active_users = active_users_result.scalar() or 0
        
        # Courses completed
        courses_completed_query = select(func.count(UserCourseProgress.id)).where(
            UserCourseProgress.status == "completed",
            UserCourseProgress.completed_at.between(start_date, end_date)
        ).join(User).where(User.company_id == company_id)
        courses_completed_result = await self.db.execute(courses_completed_query)
        courses_completed = courses_completed_result.scalar() or 0
        
        # Phishing campaigns
        phishing_campaigns_query = select(func.count(PhishingCampaign.id)).where(
            PhishingCampaign.company_id == company_id,
            PhishingCampaign.created_at.between(start_date, end_date)
        )
        phishing_campaigns_result = await self.db.execute(phishing_campaigns_query)
        phishing_campaigns = phishing_campaigns_result.scalar() or 0
        
        # Calculate engagement rate
        engagement_rate = (active_users / total_users * 100) if total_users > 0 else 0
        
        # Average quiz score
        avg_quiz_score_query = select(func.avg(UserCourseProgress.quiz_score)).where(
            UserCourseProgress.quiz_score.isnot(None),
            UserCourseProgress.completed_at.between(start_date, end_date)
        ).join(User).where(User.company_id == company_id)
        avg_quiz_score_result = await self.db.execute(avg_quiz_score_query)
        avg_quiz_score = avg_quiz_score_result.scalar() or 0
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "engagement_rate": round(engagement_rate, 2),
            "courses_completed": courses_completed,
            "phishing_campaigns": phishing_campaigns,
            "avg_quiz_score": round(float(avg_quiz_score), 2),
        }
        
    async def _get_user_activity_metrics(
        self,
        company_id: int,
        date_range: Tuple[datetime, datetime]
    ) -> Dict[str, Any]:
        """Get user activity metrics."""
        start_date, end_date = date_range
        
        # Login frequency
        login_query = select(
            func.date(AnalyticsEvent.created_at).label('date'),
            func.count(AnalyticsEvent.id).label('count')
        ).where(
            AnalyticsEvent.company_id == company_id,
            AnalyticsEvent.event_type == AnalyticsEvent.EventType.LOGIN,
            AnalyticsEvent.created_at.between(start_date, end_date)
        ).group_by(func.date(AnalyticsEvent.created_at)).order_by('date')
        
        login_result = await self.db.execute(login_query)
        login_data = [{"date": row.date.isoformat(), "count": row.count} for row in login_result]
        
        # Activity by hour
        activity_by_hour_query = select(
            func.extract('hour', AnalyticsEvent.created_at).label('hour'),
            func.count(AnalyticsEvent.id).label('count')
        ).where(
            AnalyticsEvent.company_id == company_id,
            AnalyticsEvent.created_at.between(start_date, end_date)
        ).group_by('hour').order_by('hour')
        
        activity_by_hour_result = await self.db.execute(activity_by_hour_query)
        activity_by_hour = [
            {"hour": int(row.hour), "count": row.count} 
            for row in activity_by_hour_result
        ]
        
        # Most active users
        most_active_query = select(
            User.id,
            User.first_name,
            User.last_name,
            func.count(AnalyticsEvent.id).label('activity_count')
        ).join(
            AnalyticsEvent, User.id == AnalyticsEvent.user_id
        ).where(
            User.company_id == company_id,
            AnalyticsEvent.created_at.between(start_date, end_date)
        ).group_by(User.id).order_by(func.count(AnalyticsEvent.id).desc()).limit(10)
        
        most_active_result = await self.db.execute(most_active_query)
        most_active_users = [
            {
                "user_id": row.id,
                "name": f"{row.first_name} {row.last_name}",
                "activity_count": row.activity_count
            }
            for row in most_active_result
        ]
        
        return {
            "login_trend": login_data,
            "activity_by_hour": activity_by_hour,
            "most_active_users": most_active_users,
        }
        
    async def _get_course_performance_metrics(
        self,
        company_id: int,
        date_range: Tuple[datetime, datetime]
    ) -> Dict[str, Any]:
        """Get course performance metrics."""
        start_date, end_date = date_range
        
        # Course completion rates
        course_stats_query = select(
            Course.id,
            Course.title,
            func.count(UserCourseProgress.id).label('enrollments'),
            func.sum(case((UserCourseProgress.status == 'completed', 1), else_=0)).label('completions'),
            func.avg(UserCourseProgress.progress_percentage).label('avg_progress'),
            func.avg(UserCourseProgress.quiz_score).label('avg_score')
        ).join(
            UserCourseProgress, Course.id == UserCourseProgress.course_id
        ).join(
            User, UserCourseProgress.user_id == User.id
        ).where(
            User.company_id == company_id,
            UserCourseProgress.created_at.between(start_date, end_date)
        ).group_by(Course.id).order_by(func.count(UserCourseProgress.id).desc())
        
        course_stats_result = await self.db.execute(course_stats_query)
        course_performance = []
        
        for row in course_stats_result:
            completion_rate = (row.completions / row.enrollments * 100) if row.enrollments > 0 else 0
            course_performance.append({
                "course_id": row.id,
                "course_title": row.title,
                "enrollments": row.enrollments,
                "completions": row.completions,
                "completion_rate": round(completion_rate, 2),
                "avg_progress": round(float(row.avg_progress or 0), 2),
                "avg_score": round(float(row.avg_score or 0), 2),
            })
            
        # Time to completion
        completion_time_query = select(
            func.avg(
                func.extract(
                    'epoch',
                    UserCourseProgress.completed_at - UserCourseProgress.created_at
                ) / 86400  # Convert to days
            ).label('avg_days')
        ).join(
            User, UserCourseProgress.user_id == User.id
        ).where(
            User.company_id == company_id,
            UserCourseProgress.status == 'completed',
            UserCourseProgress.completed_at.between(start_date, end_date)
        )
        
        completion_time_result = await self.db.execute(completion_time_query)
        avg_completion_days = completion_time_result.scalar() or 0
        
        return {
            "course_performance": course_performance,
            "avg_completion_days": round(float(avg_completion_days), 2),
        }
        
    async def _get_phishing_stats(
        self,
        company_id: int,
        date_range: Tuple[datetime, datetime]
    ) -> Dict[str, Any]:
        """Get phishing simulation statistics."""
        start_date, end_date = date_range
        
        # Overall phishing metrics
        phishing_metrics_query = select(
            func.count(PhishingResult.id).label('total_sent'),
            func.sum(case((PhishingResult.email_opened_at.isnot(None), 1), else_=0)).label('opened'),
            func.sum(case((PhishingResult.link_clicked_at.isnot(None), 1), else_=0)).label('clicked'),
            func.sum(case((PhishingResult.reported_at.isnot(None), 1), else_=0)).label('reported')
        ).join(
            PhishingCampaign, PhishingResult.campaign_id == PhishingCampaign.id
        ).where(
            PhishingCampaign.company_id == company_id,
            PhishingResult.email_sent_at.between(start_date, end_date)
        )
        
        phishing_result = await self.db.execute(phishing_metrics_query)
        phishing_data = phishing_result.one()
        
        total_sent = phishing_data.total_sent or 0
        opened = phishing_data.opened or 0
        clicked = phishing_data.clicked or 0
        reported = phishing_data.reported or 0
        
        # Calculate rates
        open_rate = (opened / total_sent * 100) if total_sent > 0 else 0
        click_rate = (clicked / total_sent * 100) if total_sent > 0 else 0
        report_rate = (reported / total_sent * 100) if total_sent > 0 else 0
        
        # Phishing trends over time
        phishing_trend_query = select(
            func.date(PhishingResult.email_sent_at).label('date'),
            func.count(PhishingResult.id).label('sent'),
            func.sum(case((PhishingResult.link_clicked_at.isnot(None), 1), else_=0)).label('clicked')
        ).join(
            PhishingCampaign, PhishingResult.campaign_id == PhishingCampaign.id
        ).where(
            PhishingCampaign.company_id == company_id,
            PhishingResult.email_sent_at.between(start_date, end_date)
        ).group_by(func.date(PhishingResult.email_sent_at)).order_by('date')
        
        phishing_trend_result = await self.db.execute(phishing_trend_query)
        phishing_trend = [
            {
                "date": row.date.isoformat(),
                "sent": row.sent,
                "clicked": row.clicked,
                "click_rate": round((row.clicked / row.sent * 100) if row.sent > 0 else 0, 2)
            }
            for row in phishing_trend_result
        ]
        
        # Most vulnerable users
        vulnerable_users_query = select(
            User.id,
            User.first_name,
            User.last_name,
            func.count(PhishingResult.id).label('total_phishing'),
            func.sum(case((PhishingResult.link_clicked_at.isnot(None), 1), else_=0)).label('clicked')
        ).join(
            PhishingResult, User.id == PhishingResult.user_id
        ).join(
            PhishingCampaign, PhishingResult.campaign_id == PhishingCampaign.id
        ).where(
            PhishingCampaign.company_id == company_id,
            PhishingResult.email_sent_at.between(start_date, end_date)
        ).group_by(User.id).having(
            func.sum(case((PhishingResult.link_clicked_at.isnot(None), 1), else_=0)) > 0
        ).order_by(func.sum(case((PhishingResult.link_clicked_at.isnot(None), 1), else_=0)).desc()).limit(10)
        
        vulnerable_users_result = await self.db.execute(vulnerable_users_query)
        vulnerable_users = [
            {
                "user_id": row.id,
                "name": f"{row.first_name} {row.last_name}",
                "total_phishing": row.total_phishing,
                "times_clicked": row.clicked,
                "click_rate": round((row.clicked / row.total_phishing * 100), 2)
            }
            for row in vulnerable_users_result
        ]
        
        return {
            "summary": {
                "total_sent": total_sent,
                "opened": opened,
                "clicked": clicked,
                "reported": reported,
                "open_rate": round(open_rate, 2),
                "click_rate": round(click_rate, 2),
                "report_rate": round(report_rate, 2),
            },
            "trend": phishing_trend,
            "vulnerable_users": vulnerable_users,
        }
        
    async def _calculate_security_score(self, company_id: int) -> Dict[str, Any]:
        """Calculate overall security score for the company."""
        # Get all active users
        users_query = select(User).where(
            User.company_id == company_id,
            User.is_active == True
        )
        users_result = await self.db.execute(users_query)
        users = users_result.scalars().all()
        
        if not users:
            return {"score": 0, "breakdown": {}}
            
        # Calculate various score components
        scores = {
            "training_completion": 0,
            "phishing_awareness": 0,
            "password_security": 0,
            "two_factor_adoption": 0,
            "activity_engagement": 0,
        }
        
        # Training completion score
        course_completion_query = select(
            func.avg(UserCourseProgress.progress_percentage)
        ).join(
            User, UserCourseProgress.user_id == User.id
        ).where(User.company_id == company_id)
        
        course_completion_result = await self.db.execute(course_completion_query)
        avg_completion = course_completion_result.scalar() or 0
        scores["training_completion"] = float(avg_completion)
        
        # Phishing awareness score (inverse of click rate)
        last_30_days = datetime.utcnow() - timedelta(days=30)
        phishing_query = select(
            func.count(PhishingResult.id).label('total'),
            func.sum(case((PhishingResult.link_clicked_at.isnot(None), 1), else_=0)).label('clicked')
        ).join(
            PhishingCampaign, PhishingResult.campaign_id == PhishingCampaign.id
        ).where(
            PhishingCampaign.company_id == company_id,
            PhishingResult.email_sent_at >= last_30_days
        )
        
        phishing_result = await self.db.execute(phishing_query)
        phishing_data = phishing_result.one()
        
        if phishing_data.total > 0:
            click_rate = (phishing_data.clicked / phishing_data.total)
            scores["phishing_awareness"] = (1 - click_rate) * 100
        else:
            scores["phishing_awareness"] = 75  # Default score if no data
            
        # Password security (based on password age and strength)
        # For now, use a default score
        scores["password_security"] = 80
        
        # Two-factor adoption
        two_fa_users = sum(1 for user in users if user.two_factor_enabled)
        scores["two_factor_adoption"] = (two_fa_users / len(users)) * 100
        
        # Activity engagement (based on login frequency)
        active_users_query = select(
            func.count(func.distinct(AnalyticsEvent.user_id))
        ).where(
            AnalyticsEvent.company_id == company_id,
            AnalyticsEvent.event_type == AnalyticsEvent.EventType.LOGIN,
            AnalyticsEvent.created_at >= last_30_days
        )
        
        active_users_result = await self.db.execute(active_users_query)
        active_users = active_users_result.scalar() or 0
        scores["activity_engagement"] = (active_users / len(users)) * 100
        
        # Calculate weighted overall score
        weights = {
            "training_completion": 0.25,
            "phishing_awareness": 0.30,
            "password_security": 0.15,
            "two_factor_adoption": 0.20,
            "activity_engagement": 0.10,
        }
        
        overall_score = sum(scores[key] * weights[key] for key in scores)
        
        return {
            "score": round(overall_score, 2),
            "breakdown": {key: round(value, 2) for key, value in scores.items()},
            "recommendations": self._get_security_recommendations(scores),
        }
        
    def _get_security_recommendations(self, scores: Dict[str, float]) -> List[str]:
        """Get security recommendations based on scores."""
        recommendations = []
        
        if scores["training_completion"] < 70:
            recommendations.append("Increase training completion rates through reminders and incentives")
            
        if scores["phishing_awareness"] < 80:
            recommendations.append("Conduct more frequent phishing simulations to improve awareness")
            
        if scores["two_factor_adoption"] < 90:
            recommendations.append("Mandate two-factor authentication for all users")
            
        if scores["activity_engagement"] < 60:
            recommendations.append("Improve user engagement through gamification and regular communications")
            
        return recommendations
        
    async def _get_trend_data(
        self,
        company_id: int,
        date_range: Tuple[datetime, datetime]
    ) -> Dict[str, Any]:
        """Get trend data for various metrics."""
        start_date, end_date = date_range
        
        # Calculate previous period for comparison
        period_length = (end_date - start_date).days
        prev_end_date = start_date
        prev_start_date = prev_end_date - timedelta(days=period_length)
        
        # Current period metrics
        current_metrics = await self._get_overview_metrics(company_id, date_range)
        
        # Previous period metrics
        previous_metrics = await self._get_overview_metrics(company_id, (prev_start_date, prev_end_date))
        
        # Calculate trends
        trends = {}
        for key in current_metrics:
            current_value = current_metrics[key]
            previous_value = previous_metrics[key]
            
            if previous_value > 0:
                change_percentage = ((current_value - previous_value) / previous_value) * 100
            else:
                change_percentage = 100 if current_value > 0 else 0
                
            trends[key] = {
                "current": current_value,
                "previous": previous_value,
                "change": round(current_value - previous_value, 2),
                "change_percentage": round(change_percentage, 2),
                "trend": "up" if change_percentage > 0 else "down" if change_percentage < 0 else "stable"
            }
            
        return trends
        
    async def _get_top_performers(
        self,
        company_id: int,
        date_range: Tuple[datetime, datetime]
    ) -> List[Dict[str, Any]]:
        """Get top performing users based on various criteria."""
        start_date, end_date = date_range
        
        # Top learners (by courses completed and scores)
        top_learners_query = select(
            User.id,
            User.first_name,
            User.last_name,
            func.count(UserCourseProgress.id).label('courses_completed'),
            func.avg(UserCourseProgress.quiz_score).label('avg_score')
        ).join(
            UserCourseProgress, User.id == UserCourseProgress.user_id
        ).where(
            User.company_id == company_id,
            UserCourseProgress.status == 'completed',
            UserCourseProgress.completed_at.between(start_date, end_date)
        ).group_by(User.id).order_by(
            func.count(UserCourseProgress.id).desc(),
            func.avg(UserCourseProgress.quiz_score).desc()
        ).limit(10)
        
        top_learners_result = await self.db.execute(top_learners_query)
        top_performers = []
        
        for row in top_learners_result:
            # Get phishing performance
            phishing_query = select(
                func.count(PhishingResult.id).label('total'),
                func.sum(case((PhishingResult.link_clicked_at.isnot(None), 1), else_=0)).label('clicked')
            ).where(
                PhishingResult.user_id == row.id,
                PhishingResult.email_sent_at.between(start_date, end_date)
            )
            
            phishing_result = await self.db.execute(phishing_query)
            phishing_data = phishing_result.one()
            
            phishing_score = 100
            if phishing_data.total > 0:
                phishing_score = ((phishing_data.total - phishing_data.clicked) / phishing_data.total) * 100
                
            top_performers.append({
                "user_id": row.id,
                "name": f"{row.first_name} {row.last_name}",
                "courses_completed": row.courses_completed,
                "avg_quiz_score": round(float(row.avg_score or 0), 2),
                "phishing_score": round(phishing_score, 2),
                "overall_score": round((float(row.avg_score or 0) + phishing_score) / 2, 2)
            })
            
        return sorted(top_performers, key=lambda x: x["overall_score"], reverse=True)
        
    async def _get_risk_assessment(self, company_id: int) -> Dict[str, Any]:
        """Get risk assessment for the company."""
        # Users who haven't completed training
        untrained_users_query = select(func.count(User.id)).where(
            User.company_id == company_id,
            User.is_active == True,
            ~User.id.in_(
                select(UserCourseProgress.user_id).where(
                    UserCourseProgress.status == 'completed'
                )
            )
        )
        
        untrained_users_result = await self.db.execute(untrained_users_query)
        untrained_users = untrained_users_result.scalar() or 0
        
        # Users who clicked phishing links recently
        last_30_days = datetime.utcnow() - timedelta(days=30)
        phishing_clickers_query = select(
            func.count(func.distinct(PhishingResult.user_id))
        ).join(
            PhishingCampaign, PhishingResult.campaign_id == PhishingCampaign.id
        ).where(
            PhishingCampaign.company_id == company_id,
            PhishingResult.link_clicked_at.isnot(None),
            PhishingResult.email_sent_at >= last_30_days
        )
        
        phishing_clickers_result = await self.db.execute(phishing_clickers_query)
        phishing_clickers = phishing_clickers_result.scalar() or 0
        
        # Users without 2FA
        no_2fa_query = select(func.count(User.id)).where(
            User.company_id == company_id,
            User.is_active == True,
            User.two_factor_enabled == False
        )
        
        no_2fa_result = await self.db.execute(no_2fa_query)
        no_2fa_users = no_2fa_result.scalar() or 0
        
        # Calculate risk levels
        total_users_query = select(func.count(User.id)).where(
            User.company_id == company_id,
            User.is_active == True
        )
        total_users_result = await self.db.execute(total_users_query)
        total_users = total_users_result.scalar() or 1  # Avoid division by zero
        
        risk_assessment = {
            "high_risk_users": {
                "untrained": untrained_users,
                "phishing_vulnerable": phishing_clickers,
                "no_2fa": no_2fa_users,
                "total": untrained_users + phishing_clickers + no_2fa_users,
            },
            "risk_percentages": {
                "untrained": round((untrained_users / total_users) * 100, 2),
                "phishing_vulnerable": round((phishing_clickers / total_users) * 100, 2),
                "no_2fa": round((no_2fa_users / total_users) * 100, 2),
            },
            "overall_risk_level": self._calculate_risk_level(
                untrained_users, phishing_clickers, no_2fa_users, total_users
            ),
            "recommendations": self._get_risk_recommendations(
                untrained_users, phishing_clickers, no_2fa_users, total_users
            ),
        }
        
        return risk_assessment
        
    def _calculate_risk_level(
        self,
        untrained: int,
        phishing_vulnerable: int,
        no_2fa: int,
        total_users: int
    ) -> str:
        """Calculate overall risk level."""
        if total_users == 0:
            return "Unknown"
            
        risk_score = (
            (untrained / total_users) * 0.3 +
            (phishing_vulnerable / total_users) * 0.4 +
            (no_2fa / total_users) * 0.3
        ) * 100
        
        if risk_score >= 70:
            return "Critical"
        elif risk_score >= 50:
            return "High"
        elif risk_score >= 30:
            return "Medium"
        elif risk_score >= 10:
            return "Low"
        else:
            return "Very Low"
            
    def _get_risk_recommendations(
        self,
        untrained: int,
        phishing_vulnerable: int,
        no_2fa: int,
        total_users: int
    ) -> List[str]:
        """Get risk mitigation recommendations."""
        recommendations = []
        
        if untrained > total_users * 0.2:
            recommendations.append("Mandate security awareness training for all new and existing employees")
            
        if phishing_vulnerable > total_users * 0.1:
            recommendations.append("Increase phishing simulation frequency and provide immediate feedback")
            
        if no_2fa > total_users * 0.1:
            recommendations.append("Implement mandatory two-factor authentication policy")
            
        if len(recommendations) == 0:
            recommendations.append("Continue monitoring and maintaining current security practices")
            
        return recommendations
        
    async def generate_compliance_report(
        self,
        company_id: int,
        report_type: str = "monthly"
    ) -> Dict[str, Any]:
        """Generate compliance report for auditing purposes."""
        # Determine date range based on report type
        end_date = datetime.utcnow()
        if report_type == "monthly":
            start_date = end_date - timedelta(days=30)
        elif report_type == "quarterly":
            start_date = end_date - timedelta(days=90)
        elif report_type == "annual":
            start_date = end_date - timedelta(days=365)
        else:
            start_date = end_date - timedelta(days=30)
            
        date_range = (start_date, end_date)
        
        # Get comprehensive metrics
        metrics = await self.get_dashboard_metrics(company_id, date_range)
        
        # Add compliance-specific data
        compliance_data = {
            "report_metadata": {
                "company_id": company_id,
                "report_type": report_type,
                "generated_at": datetime.utcnow().isoformat(),
                "period_start": start_date.isoformat(),
                "period_end": end_date.isoformat(),
            },
            "executive_summary": {
                "total_users": metrics["overview"]["total_users"],
                "security_score": metrics["security_score"]["score"],
                "training_completion_rate": metrics["overview"]["courses_completed"],
                "phishing_resilience": 100 - metrics["phishing_stats"]["summary"]["click_rate"],
                "overall_risk_level": metrics["risk_assessment"]["overall_risk_level"],
            },
            "detailed_metrics": metrics,
            "compliance_checklist": await self._generate_compliance_checklist(company_id, date_range),
        }
        
        return compliance_data
        
    async def _generate_compliance_checklist(
        self,
        company_id: int,
        date_range: Tuple[datetime, datetime]
    ) -> Dict[str, bool]:
        """Generate compliance checklist."""
        start_date, end_date = date_range
        
        # Check various compliance requirements
        checklist = {}
        
        # All users completed basic training
        all_trained_query = select(
            func.count(User.id).label('total'),
            func.count(UserCourseProgress.user_id).label('trained')
        ).select_from(User).outerjoin(
            UserCourseProgress,
            and_(
                User.id == UserCourseProgress.user_id,
                UserCourseProgress.status == 'completed'
            )
        ).where(
            User.company_id == company_id,
            User.is_active == True
        )
        
        all_trained_result = await self.db.execute(all_trained_query)
        training_data = all_trained_result.one()
        
        checklist["all_users_trained"] = training_data.trained >= training_data.total * 0.95
        checklist["phishing_tests_conducted"] = await self._check_phishing_tests(company_id, date_range)
        checklist["incident_response_ready"] = True  # Placeholder
        checklist["access_controls_enforced"] = await self._check_access_controls(company_id)
        checklist["audit_logs_maintained"] = True  # We have analytics events
        
        return checklist
        
    async def _check_phishing_tests(
        self,
        company_id: int,
        date_range: Tuple[datetime, datetime]
    ) -> bool:
        """Check if regular phishing tests are conducted."""
        start_date, end_date = date_range
        
        # Check if at least one phishing campaign per month
        months_in_range = max(1, (end_date - start_date).days // 30)
        
        phishing_count_query = select(func.count(PhishingCampaign.id)).where(
            PhishingCampaign.company_id == company_id,
            PhishingCampaign.created_at.between(start_date, end_date)
        )
        
        phishing_count_result = await self.db.execute(phishing_count_query)
        phishing_count = phishing_count_result.scalar() or 0
        
        return phishing_count >= months_in_range
        
    async def _check_access_controls(self, company_id: int) -> bool:
        """Check if proper access controls are in place."""
        # Check 2FA adoption rate
        two_fa_query = select(
            func.count(User.id).label('total'),
            func.sum(case((User.two_factor_enabled == True, 1), else_=0)).label('with_2fa')
        ).where(
            User.company_id == company_id,
            User.is_active == True
        )
        
        two_fa_result = await self.db.execute(two_fa_query)
        two_fa_data = two_fa_result.one()
        
        if two_fa_data.total == 0:
            return False
            
        # At least 80% should have 2FA enabled
        return (two_fa_data.with_2fa / two_fa_data.total) >= 0.8