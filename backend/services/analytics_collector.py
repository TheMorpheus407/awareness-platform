"""
Analytics data collection service for tracking user behavior and system metrics.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
import logging
from collections import defaultdict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, case
from sqlalchemy.orm import selectinload

from models import (
    AnalyticsEvent, User, Company, Course, UserCourseProgress,
    PhishingCampaign, PhishingResult, EmailLog, EmailStatus
)
from core.cache import get_cache
from core.config import settings

logger = logging.getLogger(__name__)


class AnalyticsCollector:
    """Service for collecting and aggregating analytics data."""

    def __init__(self, db: AsyncSession, cache=None):
        """Initialize analytics collector."""
        self.db = db
        self.cache = cache or get_cache()
        self.batch_size = 100
        self.flush_interval = 60  # seconds

    async def track_event(
        self,
        event_type: str,
        user_id: Optional[int] = None,
        company_id: Optional[int] = None,
        properties: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """
        Track an analytics event.

        Args:
            event_type: Type of event (e.g., 'page_view', 'course_started')
            user_id: Optional user ID associated with event
            company_id: Optional company ID
            properties: Additional event properties
            timestamp: Event timestamp (defaults to now)
        """
        # Create event
        event = AnalyticsEvent(
            event_type=event_type,
            user_id=user_id,
            company_id=company_id,
            properties=properties or {},
            timestamp=timestamp or datetime.utcnow(),
        )

        # Add to batch in cache
        batch_key = "analytics:batch:current"
        await self.cache.rpush(batch_key, event.json())

        # Check if batch should be flushed
        batch_size = await self.cache.llen(batch_key)
        if batch_size >= self.batch_size:
            asyncio.create_task(self._flush_batch())

    async def _flush_batch(self) -> None:
        """Flush the current batch of events to database."""
        batch_key = "analytics:batch:current"
        processing_key = "analytics:batch:processing"

        try:
            # Move batch to processing
            await self.cache.rename(batch_key, processing_key)

            # Get all events from batch
            events_json = await self.cache.lrange(processing_key, 0, -1)
            if not events_json:
                return

            # Parse and save events
            events = []
            for event_json in events_json:
                try:
                    import json
                    event_data = json.loads(event_json)
                    event = AnalyticsEvent(**event_data)
                    events.append(event)
                except Exception as e:
                    logger.error(f"Failed to parse event: {str(e)}")

            if events:
                self.db.add_all(events)
                await self.db.commit()
                logger.info(f"Flushed {len(events)} analytics events")

            # Clean up
            await self.cache.delete(processing_key)

        except Exception as e:
            logger.error(f"Failed to flush analytics batch: {str(e)}")
            # Move back to current batch
            try:
                await self.cache.rename(processing_key, batch_key)
            except:
                pass

    async def get_company_metrics(
        self,
        company_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get comprehensive metrics for a company."""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        metrics = {
            "overview": await self._get_company_overview(company_id),
            "user_activity": await self._get_user_activity_metrics(
                company_id, start_date, end_date
            ),
            "training_progress": await self._get_training_metrics(
                company_id, start_date, end_date
            ),
            "phishing_performance": await self._get_phishing_metrics(
                company_id, start_date, end_date
            ),
            "security_trends": await self._get_security_trends(
                company_id, start_date, end_date
            ),
        }

        return metrics

    async def _get_company_overview(self, company_id: int) -> Dict[str, Any]:
        """Get company overview metrics."""
        # Total users
        stmt = select(func.count(User.id)).where(
            User.company_id == company_id,
            User.is_active == True
        )
        total_users = await self.db.scalar(stmt)

        # Active users (last 30 days)
        active_cutoff = datetime.utcnow() - timedelta(days=30)
        stmt = select(func.count(User.id)).where(
            User.company_id == company_id,
            User.is_active == True,
            User.last_login >= active_cutoff
        )
        active_users = await self.db.scalar(stmt)

        # Average security score
        stmt = select(func.avg(User.security_score)).where(
            User.company_id == company_id,
            User.is_active == True,
            User.security_score.isnot(None)
        )
        avg_security_score = await self.db.scalar(stmt) or 0

        # Courses completed (all time)
        stmt = select(func.count(UserCourseProgress.id)).where(
            UserCourseProgress.completion_percentage == 100
        ).join(User).where(User.company_id == company_id)
        courses_completed = await self.db.scalar(stmt)

        return {
            "total_users": total_users,
            "active_users": active_users,
            "active_rate": (active_users / total_users * 100) if total_users > 0 else 0,
            "average_security_score": round(avg_security_score, 1),
            "total_courses_completed": courses_completed,
        }

    async def _get_user_activity_metrics(
        self,
        company_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get user activity metrics."""
        # Daily active users
        stmt = select(
            func.date_trunc('day', AnalyticsEvent.timestamp).label('day'),
            func.count(func.distinct(AnalyticsEvent.user_id)).label('active_users')
        ).where(
            AnalyticsEvent.company_id == company_id,
            AnalyticsEvent.timestamp.between(start_date, end_date),
            AnalyticsEvent.event_type.in_(['login', 'page_view', 'course_view'])
        ).group_by('day').order_by('day')

        result = await self.db.execute(stmt)
        daily_active = [
            {
                "date": row.day,
                "active_users": row.active_users
            }
            for row in result
        ]

        # Top events
        stmt = select(
            AnalyticsEvent.event_type,
            func.count(AnalyticsEvent.id).label('count')
        ).where(
            AnalyticsEvent.company_id == company_id,
            AnalyticsEvent.timestamp.between(start_date, end_date)
        ).group_by(AnalyticsEvent.event_type).order_by(func.count(AnalyticsEvent.id).desc()).limit(10)

        result = await self.db.execute(stmt)
        top_events = [
            {
                "event": row.event_type,
                "count": row.count
            }
            for row in result
        ]

        return {
            "daily_active_users": daily_active,
            "top_events": top_events,
        }

    async def _get_training_metrics(
        self,
        company_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get training metrics."""
        # Course completion rate
        stmt = select(
            Course.id,
            Course.title,
            func.count(UserCourseProgress.id).label('enrollments'),
            func.count(
                case(
                    (UserCourseProgress.completion_percentage == 100, 1),
                    else_=None
                )
            ).label('completions')
        ).select_from(Course).join(
            UserCourseProgress,
            Course.id == UserCourseProgress.course_id
        ).join(User).where(
            User.company_id == company_id,
            UserCourseProgress.enrolled_at.between(start_date, end_date)
        ).group_by(Course.id, Course.title)

        result = await self.db.execute(stmt)
        course_stats = []
        for row in result:
            completion_rate = (row.completions / row.enrollments * 100) if row.enrollments > 0 else 0
            course_stats.append({
                "course_id": row.id,
                "course_title": row.title,
                "enrollments": row.enrollments,
                "completions": row.completions,
                "completion_rate": round(completion_rate, 1),
            })

        # Average time to complete
        stmt = select(
            func.avg(
                func.extract(
                    'epoch',
                    UserCourseProgress.completed_at - UserCourseProgress.enrolled_at
                ) / 86400  # Convert to days
            ).label('avg_days')
        ).join(User).where(
            User.company_id == company_id,
            UserCourseProgress.completed_at.isnot(None),
            UserCourseProgress.completed_at.between(start_date, end_date)
        )

        avg_completion_days = await self.db.scalar(stmt) or 0

        # Department performance
        stmt = select(
            User.department,
            func.count(func.distinct(User.id)).label('users'),
            func.avg(
                case(
                    (UserCourseProgress.completion_percentage.isnot(None), UserCourseProgress.completion_percentage),
                    else_=0
                )
            ).label('avg_progress')
        ).select_from(User).outerjoin(
            UserCourseProgress,
            User.id == UserCourseProgress.user_id
        ).where(
            User.company_id == company_id,
            User.is_active == True
        ).group_by(User.department)

        result = await self.db.execute(stmt)
        department_performance = [
            {
                "department": row.department or "Unknown",
                "users": row.users,
                "average_progress": round(row.avg_progress or 0, 1),
            }
            for row in result
        ]

        return {
            "course_statistics": course_stats,
            "average_completion_days": round(avg_completion_days, 1),
            "department_performance": department_performance,
        }

    async def _get_phishing_metrics(
        self,
        company_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get phishing simulation metrics."""
        # Overall click rate
        stmt = select(
            func.count(PhishingResult.id).label('total_sent'),
            func.count(
                case(
                    (PhishingResult.clicked_at.isnot(None), 1),
                    else_=None
                )
            ).label('total_clicked'),
            func.count(
                case(
                    (PhishingResult.data_submitted_at.isnot(None), 1),
                    else_=None
                )
            ).label('total_submitted')
        ).join(
            PhishingCampaign,
            PhishingResult.campaign_id == PhishingCampaign.id
        ).where(
            PhishingCampaign.company_id == company_id,
            PhishingResult.sent_at.between(start_date, end_date)
        )

        result = await self.db.execute(stmt)
        row = result.one()

        click_rate = (row.total_clicked / row.total_sent * 100) if row.total_sent > 0 else 0
        submission_rate = (row.total_submitted / row.total_sent * 100) if row.total_sent > 0 else 0

        # Campaign performance
        stmt = select(
            PhishingCampaign.id,
            PhishingCampaign.name,
            func.count(PhishingResult.id).label('emails_sent'),
            func.count(
                case(
                    (PhishingResult.clicked_at.isnot(None), 1),
                    else_=None
                )
            ).label('clicks')
        ).select_from(PhishingCampaign).join(
            PhishingResult,
            PhishingCampaign.id == PhishingResult.campaign_id
        ).where(
            PhishingCampaign.company_id == company_id,
            PhishingCampaign.created_at.between(start_date, end_date)
        ).group_by(PhishingCampaign.id, PhishingCampaign.name)

        result = await self.db.execute(stmt)
        campaign_performance = []
        for row in result:
            click_rate_campaign = (row.clicks / row.emails_sent * 100) if row.emails_sent > 0 else 0
            campaign_performance.append({
                "campaign_id": row.id,
                "campaign_name": row.name,
                "emails_sent": row.emails_sent,
                "click_rate": round(click_rate_campaign, 1),
            })

        # Click rate trend
        stmt = select(
            func.date_trunc('week', PhishingResult.sent_at).label('week'),
            func.count(PhishingResult.id).label('sent'),
            func.count(
                case(
                    (PhishingResult.clicked_at.isnot(None), 1),
                    else_=None
                )
            ).label('clicked')
        ).join(
            PhishingCampaign,
            PhishingResult.campaign_id == PhishingCampaign.id
        ).where(
            PhishingCampaign.company_id == company_id,
            PhishingResult.sent_at.between(start_date, end_date)
        ).group_by('week').order_by('week')

        result = await self.db.execute(stmt)
        click_rate_trend = []
        for row in result:
            weekly_rate = (row.clicked / row.sent * 100) if row.sent > 0 else 0
            click_rate_trend.append({
                "week": row.week,
                "click_rate": round(weekly_rate, 1),
            })

        return {
            "overall_click_rate": round(click_rate, 1),
            "overall_submission_rate": round(submission_rate, 1),
            "campaign_performance": campaign_performance,
            "click_rate_trend": click_rate_trend,
        }

    async def _get_security_trends(
        self,
        company_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get security score trends."""
        # Weekly average security score
        stmt = select(
            func.date_trunc('week', AnalyticsEvent.timestamp).label('week'),
            func.avg(
                func.cast(
                    AnalyticsEvent.properties['security_score'],
                    func.numeric
                )
            ).label('avg_score')
        ).where(
            AnalyticsEvent.company_id == company_id,
            AnalyticsEvent.event_type == 'security_score_update',
            AnalyticsEvent.timestamp.between(start_date, end_date)
        ).group_by('week').order_by('week')

        result = await self.db.execute(stmt)
        security_score_trend = [
            {
                "week": row.week,
                "average_score": round(float(row.avg_score or 0), 1),
            }
            for row in result
        ]

        # Risk distribution
        stmt = select(
            case(
                (User.security_score >= 90, 'Low Risk'),
                (User.security_score >= 70, 'Medium Risk'),
                (User.security_score >= 50, 'High Risk'),
                else_='Critical Risk'
            ).label('risk_level'),
            func.count(User.id).label('count')
        ).where(
            User.company_id == company_id,
            User.is_active == True
        ).group_by('risk_level')

        result = await self.db.execute(stmt)
        risk_distribution = {
            row.risk_level: row.count
            for row in result
        }

        return {
            "security_score_trend": security_score_trend,
            "risk_distribution": risk_distribution,
        }

    async def get_user_analytics(
        self,
        user_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get analytics for a specific user."""
        start_date = datetime.utcnow() - timedelta(days=days)

        # Activity summary
        stmt = select(
            AnalyticsEvent.event_type,
            func.count(AnalyticsEvent.id).label('count')
        ).where(
            AnalyticsEvent.user_id == user_id,
            AnalyticsEvent.timestamp >= start_date
        ).group_by(AnalyticsEvent.event_type)

        result = await self.db.execute(stmt)
        activity_summary = {
            row.event_type: row.count
            for row in result
        }

        # Course progress
        stmt = select(UserCourseProgress).where(
            UserCourseProgress.user_id == user_id
        ).options(selectinload(UserCourseProgress.course))

        result = await self.db.execute(stmt)
        courses = result.scalars().all()

        course_progress = [
            {
                "course_id": progress.course_id,
                "course_title": progress.course.title if progress.course else "Unknown",
                "progress": progress.completion_percentage,
                "enrolled_at": progress.enrolled_at,
                "completed_at": progress.completed_at,
            }
            for progress in courses
        ]

        # Phishing performance
        stmt = select(
            func.count(PhishingResult.id).label('total'),
            func.count(
                case(
                    (PhishingResult.clicked_at.isnot(None), 1),
                    else_=None
                )
            ).label('clicked')
        ).where(
            PhishingResult.user_id == user_id,
            PhishingResult.sent_at >= start_date
        )

        result = await self.db.execute(stmt)
        row = result.one()

        phishing_resistance = 100 - (row.clicked / row.total * 100) if row.total > 0 else 100

        return {
            "activity_summary": activity_summary,
            "course_progress": course_progress,
            "phishing_resistance_rate": round(phishing_resistance, 1),
            "total_phishing_tests": row.total,
        }

    async def generate_executive_report(
        self,
        company_id: int,
        period: str = "monthly"
    ) -> Dict[str, Any]:
        """Generate executive-level analytics report."""
        # Determine date range
        end_date = datetime.utcnow()
        if period == "weekly":
            start_date = end_date - timedelta(days=7)
        elif period == "monthly":
            start_date = end_date - timedelta(days=30)
        elif period == "quarterly":
            start_date = end_date - timedelta(days=90)
        else:
            start_date = end_date - timedelta(days=30)

        # Get all metrics
        metrics = await self.get_company_metrics(company_id, start_date, end_date)

        # Calculate key performance indicators
        kpis = {
            "security_posture": self._calculate_security_posture(metrics),
            "training_effectiveness": self._calculate_training_effectiveness(metrics),
            "phishing_readiness": self._calculate_phishing_readiness(metrics),
            "overall_risk_score": self._calculate_risk_score(metrics),
        }

        # Generate recommendations
        recommendations = self._generate_recommendations(metrics, kpis)

        return {
            "period": period,
            "start_date": start_date,
            "end_date": end_date,
            "metrics": metrics,
            "key_performance_indicators": kpis,
            "recommendations": recommendations,
            "executive_summary": self._generate_executive_summary(metrics, kpis),
        }

    def _calculate_security_posture(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall security posture score."""
        overview = metrics.get("overview", {})
        avg_score = overview.get("average_security_score", 0)
        active_rate = overview.get("active_rate", 0)

        # Weighted calculation
        posture_score = (avg_score * 0.7) + (active_rate * 0.3)

        return {
            "score": round(posture_score, 1),
            "rating": self._get_rating(posture_score),
            "components": {
                "security_score": avg_score,
                "engagement": active_rate,
            }
        }

    def _calculate_training_effectiveness(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate training effectiveness score."""
        training = metrics.get("training_progress", {})
        course_stats = training.get("course_statistics", [])

        if not course_stats:
            return {"score": 0, "rating": "No Data"}

        # Average completion rate
        avg_completion = sum(c["completion_rate"] for c in course_stats) / len(course_stats)

        return {
            "score": round(avg_completion, 1),
            "rating": self._get_rating(avg_completion),
            "average_completion_rate": avg_completion,
            "courses_analyzed": len(course_stats),
        }

    def _calculate_phishing_readiness(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate phishing readiness score."""
        phishing = metrics.get("phishing_performance", {})
        click_rate = phishing.get("overall_click_rate", 100)

        # Inverse of click rate (lower is better)
        readiness_score = 100 - click_rate

        return {
            "score": round(readiness_score, 1),
            "rating": self._get_rating(readiness_score),
            "click_rate": click_rate,
            "submission_rate": phishing.get("overall_submission_rate", 0),
        }

    def _calculate_risk_score(self, metrics: Dict[str, Any]) -> int:
        """Calculate overall risk score (0-100, lower is better)."""
        # Combine various factors
        security_posture = self._calculate_security_posture(metrics)["score"]
        phishing_readiness = self._calculate_phishing_readiness(metrics)["score"]
        training_effectiveness = self._calculate_training_effectiveness(metrics)["score"]

        # Weighted risk calculation (inverse of positive metrics)
        risk_score = 100 - (
            (security_posture * 0.4) +
            (phishing_readiness * 0.4) +
            (training_effectiveness * 0.2)
        )

        return max(0, min(100, round(risk_score)))

    def _get_rating(self, score: float) -> str:
        """Get rating based on score."""
        if score >= 90:
            return "Excellent"
        elif score >= 80:
            return "Good"
        elif score >= 70:
            return "Fair"
        elif score >= 60:
            return "Needs Improvement"
        else:
            return "Critical"

    def _generate_recommendations(
        self,
        metrics: Dict[str, Any],
        kpis: Dict[str, Any]
    ) -> List[str]:
        """Generate actionable recommendations based on metrics."""
        recommendations = []

        # Check security posture
        if kpis["security_posture"]["score"] < 70:
            recommendations.append(
                "Increase security awareness training frequency to improve overall security scores"
            )

        # Check training effectiveness
        training_kpi = kpis.get("training_effectiveness", {})
        if training_kpi.get("score", 0) < 80:
            recommendations.append(
                "Consider implementing mandatory training completion policies"
            )

        # Check phishing readiness
        if kpis["phishing_readiness"]["click_rate"] > 20:
            recommendations.append(
                "Increase phishing simulation frequency and provide immediate feedback"
            )

        # Check engagement
        overview = metrics.get("overview", {})
        if overview.get("active_rate", 0) < 60:
            recommendations.append(
                "Implement engagement campaigns to increase platform usage"
            )

        # Risk-based recommendations
        risk_score = kpis["overall_risk_score"]
        if risk_score > 70:
            recommendations.append(
                "Critical: Implement immediate security remediation program"
            )
        elif risk_score > 50:
            recommendations.append(
                "Schedule quarterly security reviews with department heads"
            )

        return recommendations

    def _generate_executive_summary(
        self,
        metrics: Dict[str, Any],
        kpis: Dict[str, Any]
    ) -> str:
        """Generate executive summary text."""
        risk_score = kpis["overall_risk_score"]
        risk_rating = self._get_rating(100 - risk_score)

        overview = metrics.get("overview", {})
        active_users = overview.get("active_users", 0)
        total_users = overview.get("total_users", 1)

        summary = f"""
        The organization's current security risk level is rated as {risk_rating} 
        with an overall risk score of {risk_score}/100. 

        Key findings:
        - {active_users} out of {total_users} users are actively engaged
        - Average security awareness score: {overview.get('average_security_score', 0)}/100
        - Phishing click rate: {kpis['phishing_readiness']['click_rate']}%
        - Training completion rate: {kpis['training_effectiveness'].get('average_completion_rate', 0)}%

        Immediate action is {'required' if risk_score > 70 else 'recommended'} to 
        {'address critical vulnerabilities' if risk_score > 70 else 'maintain and improve security posture'}.
        """

        return summary.strip()

    async def cleanup_old_events(self, days: int = 90) -> int:
        """Clean up old analytics events."""
        cutoff = datetime.utcnow() - timedelta(days=days)

        stmt = select(AnalyticsEvent).where(
            AnalyticsEvent.timestamp < cutoff
        )
        result = await self.db.execute(stmt)
        events = result.scalars().all()

        count = len(events)
        for event in events:
            await self.db.delete(event)

        await self.db.commit()
        logger.info(f"Cleaned up {count} old analytics events")
        return count