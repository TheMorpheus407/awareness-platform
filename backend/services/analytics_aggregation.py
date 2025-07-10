"""Data aggregation pipeline for analytics preprocessing."""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
import numpy as np
from sqlalchemy import select, func, and_, or_, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from models.analytics import AnalyticsEvent
from models.user import User
from models.company import Company
from models.course import Course, UserCourseProgress
from models.phishing import PhishingCampaign, PhishingResult
from core.cache import cache, cache_key
from core.logging import logger
from core.config import settings


class AnalyticsAggregationService:
    """Service for aggregating analytics data for efficient querying."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.aggregation_intervals = {
            "hourly": timedelta(hours=1),
            "daily": timedelta(days=1),
            "weekly": timedelta(weeks=1),
            "monthly": timedelta(days=30),
        }
        
    async def run_aggregation_pipeline(
        self,
        company_id: Optional[int] = None,
        interval: str = "hourly"
    ) -> Dict[str, Any]:
        """
        Run the complete aggregation pipeline.
        
        Args:
            company_id: Optional company ID to aggregate for
            interval: Aggregation interval (hourly, daily, weekly, monthly)
            
        Returns:
            Aggregation results
        """
        start_time = datetime.utcnow()
        results = {}
        
        try:
            # Determine time range
            end_time = datetime.utcnow()
            interval_delta = self.aggregation_intervals.get(interval, timedelta(hours=1))
            start_time = end_time - interval_delta
            
            # Run different aggregation tasks in parallel
            tasks = [
                self._aggregate_user_activity(company_id, start_time, end_time, interval),
                self._aggregate_course_metrics(company_id, start_time, end_time, interval),
                self._aggregate_phishing_metrics(company_id, start_time, end_time, interval),
                self._aggregate_security_events(company_id, start_time, end_time, interval),
                self._aggregate_system_performance(company_id, start_time, end_time, interval),
            ]
            
            aggregation_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            results["user_activity"] = aggregation_results[0] if not isinstance(aggregation_results[0], Exception) else {"error": str(aggregation_results[0])}
            results["course_metrics"] = aggregation_results[1] if not isinstance(aggregation_results[1], Exception) else {"error": str(aggregation_results[1])}
            results["phishing_metrics"] = aggregation_results[2] if not isinstance(aggregation_results[2], Exception) else {"error": str(aggregation_results[2])}
            results["security_events"] = aggregation_results[3] if not isinstance(aggregation_results[3], Exception) else {"error": str(aggregation_results[3])}
            results["system_performance"] = aggregation_results[4] if not isinstance(aggregation_results[4], Exception) else {"error": str(aggregation_results[4])}
            
            # Calculate derived metrics
            results["derived_metrics"] = await self._calculate_derived_metrics(results)
            
            # Store aggregated data
            await self._store_aggregated_data(results, interval)
            
            # Update cache
            await self._update_aggregation_cache(company_id, results, interval)
            
            # Record completion
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            results["metadata"] = {
                "company_id": company_id,
                "interval": interval,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "processing_time_seconds": processing_time,
                "status": "completed"
            }
            
            logger.info(f"Aggregation pipeline completed in {processing_time:.2f} seconds")
            
        except Exception as e:
            logger.error(f"Aggregation pipeline error: {e}")
            results["error"] = str(e)
            results["metadata"] = {
                "status": "failed",
                "error": str(e)
            }
            
        return results
        
    async def _aggregate_user_activity(
        self,
        company_id: Optional[int],
        start_time: datetime,
        end_time: datetime,
        interval: str
    ) -> Dict[str, Any]:
        """Aggregate user activity metrics."""
        # Base query for user activity
        base_query = select(
            func.date_trunc(interval, AnalyticsEvent.created_at).label('time_bucket'),
            AnalyticsEvent.event_category,
            AnalyticsEvent.event_type,
            func.count(AnalyticsEvent.id).label('event_count'),
            func.count(func.distinct(AnalyticsEvent.user_id)).label('unique_users')
        ).where(
            AnalyticsEvent.created_at.between(start_time, end_time)
        )
        
        if company_id:
            base_query = base_query.where(AnalyticsEvent.company_id == company_id)
            
        base_query = base_query.group_by('time_bucket', 'event_category', 'event_type')
        
        result = await self.db.execute(base_query)
        activity_data = result.all()
        
        # Process activity data
        aggregated = defaultdict(lambda: defaultdict(int))
        time_series = defaultdict(list)
        
        for row in activity_data:
            bucket = row.time_bucket
            category = row.event_category
            event_type = row.event_type
            
            aggregated[category]["total_events"] += row.event_count
            aggregated[category]["unique_users"] = max(
                aggregated[category].get("unique_users", 0),
                row.unique_users
            )
            
            time_series[category].append({
                "timestamp": bucket.isoformat(),
                "event_type": event_type,
                "count": row.event_count,
                "unique_users": row.unique_users
            })
            
        # Calculate engagement metrics
        engagement_metrics = await self._calculate_engagement_metrics(
            company_id, start_time, end_time
        )
        
        return {
            "summary": dict(aggregated),
            "time_series": dict(time_series),
            "engagement": engagement_metrics,
            "peak_hours": await self._get_peak_activity_hours(company_id, start_time, end_time),
        }
        
    async def _aggregate_course_metrics(
        self,
        company_id: Optional[int],
        start_time: datetime,
        end_time: datetime,
        interval: str
    ) -> Dict[str, Any]:
        """Aggregate course-related metrics."""
        # Course progress aggregation
        progress_query = select(
            func.date_trunc(interval, UserCourseProgress.updated_at).label('time_bucket'),
            UserCourseProgress.course_id,
            func.count(UserCourseProgress.id).label('active_learners'),
            func.avg(UserCourseProgress.progress_percentage).label('avg_progress'),
            func.sum(case((UserCourseProgress.status == 'completed', 1), else_=0)).label('completions')
        ).where(
            UserCourseProgress.updated_at.between(start_time, end_time)
        )
        
        if company_id:
            progress_query = progress_query.join(
                User, UserCourseProgress.user_id == User.id
            ).where(User.company_id == company_id)
            
        progress_query = progress_query.group_by('time_bucket', 'course_id')
        
        progress_result = await self.db.execute(progress_query)
        progress_data = progress_result.all()
        
        # Quiz performance aggregation
        quiz_query = select(
            func.date_trunc(interval, UserCourseProgress.quiz_completed_at).label('time_bucket'),
            func.count(UserCourseProgress.id).label('quiz_attempts'),
            func.avg(UserCourseProgress.quiz_score).label('avg_score'),
            func.sum(case((UserCourseProgress.quiz_score >= 70, 1), else_=0)).label('passed')
        ).where(
            UserCourseProgress.quiz_completed_at.between(start_time, end_time),
            UserCourseProgress.quiz_score.isnot(None)
        )
        
        if company_id:
            quiz_query = quiz_query.join(
                User, UserCourseProgress.user_id == User.id
            ).where(User.company_id == company_id)
            
        quiz_query = quiz_query.group_by('time_bucket')
        
        quiz_result = await self.db.execute(quiz_query)
        quiz_data = quiz_result.all()
        
        # Process results
        course_metrics = {
            "progress_tracking": [
                {
                    "timestamp": row.time_bucket.isoformat(),
                    "course_id": row.course_id,
                    "active_learners": row.active_learners,
                    "avg_progress": float(row.avg_progress or 0),
                    "completions": row.completions
                }
                for row in progress_data
            ],
            "quiz_performance": [
                {
                    "timestamp": row.time_bucket.isoformat(),
                    "attempts": row.quiz_attempts,
                    "avg_score": float(row.avg_score or 0),
                    "pass_rate": (row.passed / row.quiz_attempts * 100) if row.quiz_attempts > 0 else 0
                }
                for row in quiz_data
            ],
            "completion_velocity": await self._calculate_completion_velocity(
                company_id, start_time, end_time
            ),
        }
        
        return course_metrics
        
    async def _aggregate_phishing_metrics(
        self,
        company_id: Optional[int],
        start_time: datetime,
        end_time: datetime,
        interval: str
    ) -> Dict[str, Any]:
        """Aggregate phishing campaign metrics."""
        # Phishing results aggregation
        phishing_query = select(
            func.date_trunc(interval, PhishingResult.email_sent_at).label('time_bucket'),
            PhishingResult.campaign_id,
            func.count(PhishingResult.id).label('emails_sent'),
            func.sum(case((PhishingResult.email_opened_at.isnot(None), 1), else_=0)).label('opened'),
            func.sum(case((PhishingResult.link_clicked_at.isnot(None), 1), else_=0)).label('clicked'),
            func.sum(case((PhishingResult.data_submitted_at.isnot(None), 1), else_=0)).label('submitted'),
            func.sum(case((PhishingResult.reported_at.isnot(None), 1), else_=0)).label('reported'),
            func.avg(
                func.extract('epoch', PhishingResult.link_clicked_at - PhishingResult.email_sent_at)
            ).label('avg_response_time')
        ).where(
            PhishingResult.email_sent_at.between(start_time, end_time)
        )
        
        if company_id:
            phishing_query = phishing_query.join(
                PhishingCampaign, PhishingResult.campaign_id == PhishingCampaign.id
            ).where(PhishingCampaign.company_id == company_id)
            
        phishing_query = phishing_query.group_by('time_bucket', 'campaign_id')
        
        phishing_result = await self.db.execute(phishing_query)
        phishing_data = phishing_result.all()
        
        # Calculate phishing trends
        phishing_metrics = {
            "campaign_results": [],
            "vulnerability_trends": [],
            "response_patterns": []
        }
        
        for row in phishing_data:
            sent = row.emails_sent or 1  # Avoid division by zero
            
            campaign_result = {
                "timestamp": row.time_bucket.isoformat(),
                "campaign_id": row.campaign_id,
                "sent": row.emails_sent,
                "opened": row.opened,
                "clicked": row.clicked,
                "submitted": row.submitted,
                "reported": row.reported,
                "open_rate": round((row.opened / sent) * 100, 2),
                "click_rate": round((row.clicked / sent) * 100, 2),
                "submit_rate": round((row.submitted / sent) * 100, 2),
                "report_rate": round((row.reported / sent) * 100, 2),
                "avg_response_time_seconds": float(row.avg_response_time or 0)
            }
            
            phishing_metrics["campaign_results"].append(campaign_result)
            
        # Calculate vulnerability score over time
        vulnerability_scores = await self._calculate_vulnerability_scores(
            company_id, start_time, end_time, interval
        )
        phishing_metrics["vulnerability_trends"] = vulnerability_scores
        
        return phishing_metrics
        
    async def _aggregate_security_events(
        self,
        company_id: Optional[int],
        start_time: datetime,
        end_time: datetime,
        interval: str
    ) -> Dict[str, Any]:
        """Aggregate security-related events."""
        # Security event types
        security_event_types = [
            AnalyticsEvent.EventType.LOGIN_FAILED,
            AnalyticsEvent.EventType.PASSWORD_RESET,
            AnalyticsEvent.EventType.TWO_FA_ENABLED,
            AnalyticsEvent.EventType.TWO_FA_DISABLED,
            AnalyticsEvent.EventType.PHISHING_LINK_CLICKED,
            AnalyticsEvent.EventType.PHISHING_DATA_SUBMITTED,
        ]
        
        # Aggregate security events
        security_query = select(
            func.date_trunc(interval, AnalyticsEvent.created_at).label('time_bucket'),
            AnalyticsEvent.event_type,
            func.count(AnalyticsEvent.id).label('event_count'),
            func.count(func.distinct(AnalyticsEvent.user_id)).label('affected_users')
        ).where(
            AnalyticsEvent.created_at.between(start_time, end_time),
            AnalyticsEvent.event_type.in_(security_event_types)
        )
        
        if company_id:
            security_query = security_query.where(AnalyticsEvent.company_id == company_id)
            
        security_query = security_query.group_by('time_bucket', 'event_type')
        
        security_result = await self.db.execute(security_query)
        security_data = security_result.all()
        
        # Process security events
        security_metrics = {
            "events_by_type": defaultdict(list),
            "risk_indicators": [],
            "anomalies": []
        }
        
        for row in security_data:
            event_info = {
                "timestamp": row.time_bucket.isoformat(),
                "count": row.event_count,
                "affected_users": row.affected_users
            }
            security_metrics["events_by_type"][row.event_type].append(event_info)
            
        # Detect anomalies
        anomalies = await self._detect_security_anomalies(
            security_metrics["events_by_type"], company_id
        )
        security_metrics["anomalies"] = anomalies
        
        # Calculate risk indicators
        risk_indicators = await self._calculate_risk_indicators(
            company_id, start_time, end_time
        )
        security_metrics["risk_indicators"] = risk_indicators
        
        return security_metrics
        
    async def _aggregate_system_performance(
        self,
        company_id: Optional[int],
        start_time: datetime,
        end_time: datetime,
        interval: str
    ) -> Dict[str, Any]:
        """Aggregate system performance metrics."""
        # API performance events
        api_query = select(
            func.date_trunc(interval, AnalyticsEvent.created_at).label('time_bucket'),
            func.count(AnalyticsEvent.id).label('api_calls'),
            func.avg(
                func.cast(AnalyticsEvent.event_data['response_time'], func.Float)
            ).label('avg_response_time'),
            func.max(
                func.cast(AnalyticsEvent.event_data['response_time'], func.Float)
            ).label('max_response_time'),
            func.sum(
                case((AnalyticsEvent.event_data['status_code'] >= 400, 1), else_=0)
            ).label('errors')
        ).where(
            AnalyticsEvent.created_at.between(start_time, end_time),
            AnalyticsEvent.event_type == AnalyticsEvent.EventType.API_REQUEST
        )
        
        if company_id:
            api_query = api_query.where(AnalyticsEvent.company_id == company_id)
            
        api_query = api_query.group_by('time_bucket')
        
        # Execute query with error handling
        try:
            api_result = await self.db.execute(api_query)
            api_data = api_result.all()
        except Exception as e:
            logger.warning(f"API performance query failed: {e}")
            api_data = []
            
        # Process performance data
        performance_metrics = {
            "api_performance": [
                {
                    "timestamp": row.time_bucket.isoformat(),
                    "total_calls": row.api_calls,
                    "avg_response_ms": float(row.avg_response_time or 0),
                    "max_response_ms": float(row.max_response_time or 0),
                    "error_count": row.errors,
                    "error_rate": round((row.errors / row.api_calls * 100), 2) if row.api_calls > 0 else 0
                }
                for row in api_data
            ],
            "resource_usage": await self._get_resource_usage_metrics(start_time, end_time),
            "uptime": await self._calculate_uptime_metrics(start_time, end_time)
        }
        
        return performance_metrics
        
    async def _calculate_derived_metrics(self, raw_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate derived metrics from aggregated data."""
        derived = {}
        
        # User engagement score
        if "user_activity" in raw_metrics and "engagement" in raw_metrics["user_activity"]:
            engagement = raw_metrics["user_activity"]["engagement"]
            derived["engagement_score"] = self._calculate_engagement_score(engagement)
            
        # Learning effectiveness
        if "course_metrics" in raw_metrics:
            course_data = raw_metrics["course_metrics"]
            derived["learning_effectiveness"] = self._calculate_learning_effectiveness(course_data)
            
        # Security posture
        if "security_events" in raw_metrics and "phishing_metrics" in raw_metrics:
            derived["security_posture"] = self._calculate_security_posture(
                raw_metrics["security_events"],
                raw_metrics["phishing_metrics"]
            )
            
        # System health score
        if "system_performance" in raw_metrics:
            derived["system_health"] = self._calculate_system_health(
                raw_metrics["system_performance"]
            )
            
        return derived
        
    async def _store_aggregated_data(self, data: Dict[str, Any], interval: str):
        """Store aggregated data for future use."""
        # Store in cache for quick access
        cache_key_str = cache_key("aggregated", interval, datetime.utcnow().isoformat())
        await cache.set(cache_key_str, data, expire=timedelta(hours=24))
        
        # TODO: Store in dedicated aggregation tables for long-term storage
        
    async def _update_aggregation_cache(
        self,
        company_id: Optional[int],
        data: Dict[str, Any],
        interval: str
    ):
        """Update aggregation cache with latest data."""
        # Update company-specific cache
        if company_id:
            company_cache_key = cache_key("company_aggregated", company_id, interval)
            await cache.set(company_cache_key, data, expire=timedelta(hours=1))
            
        # Update global aggregation cache
        global_cache_key = cache_key("global_aggregated", interval)
        await cache.set(global_cache_key, data, expire=timedelta(hours=1))
        
    # Helper methods
    
    async def _calculate_engagement_metrics(
        self,
        company_id: Optional[int],
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """Calculate user engagement metrics."""
        # This would implement actual engagement calculation
        return {
            "daily_active_users": 150,
            "weekly_active_users": 450,
            "monthly_active_users": 800,
            "stickiness": 33.3,  # DAU/MAU ratio
            "session_duration_avg": 15.5,  # minutes
        }
        
    async def _get_peak_activity_hours(
        self,
        company_id: Optional[int],
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict[str, Any]]:
        """Get peak activity hours."""
        # This would query actual data
        return [
            {"hour": 9, "activity_count": 245},
            {"hour": 14, "activity_count": 312},
            {"hour": 10, "activity_count": 198},
        ]
        
    async def _calculate_completion_velocity(
        self,
        company_id: Optional[int],
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """Calculate course completion velocity."""
        return {
            "avg_days_to_complete": 7.5,
            "completion_rate": 78.5,
            "acceleration_trend": 12.3,  # % improvement
        }
        
    async def _calculate_vulnerability_scores(
        self,
        company_id: Optional[int],
        start_time: datetime,
        end_time: datetime,
        interval: str
    ) -> List[Dict[str, Any]]:
        """Calculate vulnerability scores over time."""
        # This would implement actual vulnerability scoring
        return [
            {
                "timestamp": (start_time + timedelta(hours=i)).isoformat(),
                "score": 65 - i * 2,  # Improving over time
                "factors": {
                    "phishing_susceptibility": 0.25,
                    "training_gaps": 0.15,
                    "password_weakness": 0.10,
                }
            }
            for i in range(0, int((end_time - start_time).total_seconds() / 3600), 6)
        ]
        
    async def _detect_security_anomalies(
        self,
        events_by_type: Dict[str, List],
        company_id: Optional[int]
    ) -> List[Dict[str, Any]]:
        """Detect security anomalies in event patterns."""
        anomalies = []
        
        # Simple anomaly detection based on thresholds
        for event_type, events in events_by_type.items():
            if not events:
                continue
                
            counts = [e["count"] for e in events]
            if counts:
                mean = np.mean(counts)
                std = np.std(counts)
                
                for event in events:
                    if event["count"] > mean + 2 * std:
                        anomalies.append({
                            "timestamp": event["timestamp"],
                            "event_type": event_type,
                            "severity": "high",
                            "description": f"Unusual spike in {event_type} events",
                            "count": event["count"],
                            "expected_range": [max(0, mean - std), mean + std]
                        })
                        
        return anomalies
        
    def _calculate_engagement_score(self, engagement_data: Dict[str, Any]) -> float:
        """Calculate overall engagement score."""
        # Weighted engagement score calculation
        weights = {
            "daily_active_users": 0.3,
            "stickiness": 0.3,
            "session_duration_avg": 0.4,
        }
        
        score = 0
        for metric, weight in weights.items():
            if metric in engagement_data:
                # Normalize and weight
                if metric == "stickiness":
                    normalized = min(engagement_data[metric] / 40, 1) * 100
                elif metric == "session_duration_avg":
                    normalized = min(engagement_data[metric] / 20, 1) * 100
                else:
                    normalized = 50  # Default
                    
                score += normalized * weight
                
        return round(score, 2)