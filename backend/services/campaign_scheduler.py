"""
Campaign scheduling service for managing automated campaign execution.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union
import logging
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger

from models import (
    EmailCampaign, PhishingCampaign, CampaignStatus,
    Company, User, EmailTemplate
)
from services.email_campaign import EmailCampaignService
from services.phishing_service import PhishingService
from core.cache import get_cache
from core.config import settings

logger = logging.getLogger(__name__)


class CampaignType(str, Enum):
    """Campaign types."""
    EMAIL = "email"
    PHISHING = "phishing"
    TRAINING_REMINDER = "training_reminder"
    SECURITY_DIGEST = "security_digest"


class CampaignScheduler:
    """Service for scheduling and managing automated campaigns."""

    def __init__(self, db: AsyncSession, cache=None):
        """Initialize campaign scheduler."""
        self.db = db
        self.cache = cache or get_cache()
        self.scheduler = AsyncIOScheduler()
        self.email_service = EmailCampaignService(db, cache)
        self.phishing_service = PhishingService(db, cache)
        
        # Start scheduler
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Campaign scheduler started")

    async def schedule_campaign(
        self,
        campaign_type: CampaignType,
        campaign_id: int,
        execute_at: datetime,
        recurring: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Schedule a campaign for execution.

        Args:
            campaign_type: Type of campaign
            campaign_id: Campaign ID
            execute_at: When to execute
            recurring: Optional recurring schedule config

        Returns:
            Job ID
        """
        job_id = f"{campaign_type}_{campaign_id}_{execute_at.timestamp()}"

        # Create trigger
        if recurring:
            trigger = self._create_recurring_trigger(recurring)
        else:
            trigger = DateTrigger(run_date=execute_at)

        # Add job
        if campaign_type == CampaignType.EMAIL:
            self.scheduler.add_job(
                self._execute_email_campaign,
                trigger,
                args=[campaign_id],
                id=job_id,
                replace_existing=True,
            )
        elif campaign_type == CampaignType.PHISHING:
            self.scheduler.add_job(
                self._execute_phishing_campaign,
                trigger,
                args=[campaign_id],
                id=job_id,
                replace_existing=True,
            )
        elif campaign_type == CampaignType.TRAINING_REMINDER:
            self.scheduler.add_job(
                self._send_training_reminders,
                trigger,
                args=[campaign_id],
                id=job_id,
                replace_existing=True,
            )
        elif campaign_type == CampaignType.SECURITY_DIGEST:
            self.scheduler.add_job(
                self._send_security_digest,
                trigger,
                args=[campaign_id],
                id=job_id,
                replace_existing=True,
            )

        # Store job info in cache
        job_info = {
            "job_id": job_id,
            "campaign_type": campaign_type,
            "campaign_id": campaign_id,
            "execute_at": execute_at.isoformat(),
            "recurring": recurring,
            "created_at": datetime.utcnow().isoformat(),
        }
        await self.cache.hset(
            "scheduled_campaigns",
            job_id,
            json.dumps(job_info)
        )

        logger.info(f"Scheduled {campaign_type} campaign {campaign_id} for {execute_at}")
        return job_id

    def _create_recurring_trigger(self, config: Dict[str, Any]) -> Union[CronTrigger, IntervalTrigger]:
        """Create a recurring trigger from configuration."""
        schedule_type = config.get("type", "interval")

        if schedule_type == "cron":
            # Cron-based schedule
            return CronTrigger(
                year=config.get("year"),
                month=config.get("month"),
                day=config.get("day"),
                week=config.get("week"),
                day_of_week=config.get("day_of_week"),
                hour=config.get("hour"),
                minute=config.get("minute"),
                second=config.get("second", 0),
                timezone=config.get("timezone", "UTC"),
            )
        elif schedule_type == "interval":
            # Interval-based schedule
            return IntervalTrigger(
                weeks=config.get("weeks", 0),
                days=config.get("days", 0),
                hours=config.get("hours", 0),
                minutes=config.get("minutes", 0),
                seconds=config.get("seconds", 0),
                start_date=config.get("start_date"),
                end_date=config.get("end_date"),
                timezone=config.get("timezone", "UTC"),
            )
        else:
            raise ValueError(f"Unknown schedule type: {schedule_type}")

    async def cancel_campaign(self, job_id: str) -> bool:
        """Cancel a scheduled campaign."""
        try:
            self.scheduler.remove_job(job_id)
            await self.cache.hdel("scheduled_campaigns", job_id)
            logger.info(f"Cancelled scheduled campaign {job_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel campaign {job_id}: {str(e)}")
            return False

    async def get_scheduled_campaigns(
        self,
        campaign_type: Optional[CampaignType] = None,
        company_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get list of scheduled campaigns."""
        import json
        
        # Get all scheduled campaigns from cache
        campaigns_data = await self.cache.hgetall("scheduled_campaigns")
        
        campaigns = []
        for job_id, data in campaigns_data.items():
            try:
                campaign_info = json.loads(data)
                
                # Filter by type if specified
                if campaign_type and campaign_info["campaign_type"] != campaign_type:
                    continue
                
                # Filter by company if specified
                if company_id:
                    # Need to check the actual campaign
                    if campaign_info["campaign_type"] == CampaignType.EMAIL:
                        campaign = await self.db.get(
                            EmailCampaign,
                            campaign_info["campaign_id"]
                        )
                        if not campaign or campaign.company_id != company_id:
                            continue
                    elif campaign_info["campaign_type"] == CampaignType.PHISHING:
                        campaign = await self.db.get(
                            PhishingCampaign,
                            campaign_info["campaign_id"]
                        )
                        if not campaign or campaign.company_id != company_id:
                            continue
                
                # Get job info from scheduler
                job = self.scheduler.get_job(job_id)
                if job:
                    campaign_info["next_run_time"] = job.next_run_time
                    campaign_info["is_active"] = True
                else:
                    campaign_info["is_active"] = False
                
                campaigns.append(campaign_info)
                
            except Exception as e:
                logger.error(f"Error processing scheduled campaign {job_id}: {str(e)}")
        
        return campaigns

    async def _execute_email_campaign(self, campaign_id: int):
        """Execute an email campaign."""
        logger.info(f"Executing email campaign {campaign_id}")
        try:
            # Get fresh DB session
            async with self.db() as session:
                service = EmailCampaignService(session, self.cache)
                await service._execute_campaign(campaign_id)
        except Exception as e:
            logger.error(f"Failed to execute email campaign {campaign_id}: {str(e)}")

    async def _execute_phishing_campaign(self, campaign_id: int):
        """Execute a phishing campaign."""
        logger.info(f"Executing phishing campaign {campaign_id}")
        try:
            async with self.db() as session:
                service = PhishingService(session, self.cache)
                await service._execute_campaign(campaign_id)
        except Exception as e:
            logger.error(f"Failed to execute phishing campaign {campaign_id}: {str(e)}")

    async def _send_training_reminders(self, company_id: int):
        """Send training reminder emails to users."""
        logger.info(f"Sending training reminders for company {company_id}")
        try:
            async with self.db() as session:
                # Get users with incomplete training
                stmt = select(User).where(
                    User.company_id == company_id,
                    User.is_active == True,
                    User.email_verified == True,
                )
                result = await session.execute(stmt)
                users = result.scalars().all()

                # Check each user's training status
                email_service = EmailCampaignService(session, self.cache)
                
                for user in users:
                    # Get incomplete courses
                    incomplete_courses = await self._get_incomplete_courses(session, user.id)
                    
                    if incomplete_courses:
                        # Send reminder email
                        await email_service.email_service.send_tracked_email(
                            user_id=user.id,
                            template_code="training_reminder",
                            variables={
                                "incomplete_courses": incomplete_courses,
                                "courses_count": len(incomplete_courses),
                            }
                        )

        except Exception as e:
            logger.error(f"Failed to send training reminders: {str(e)}")

    async def _get_incomplete_courses(
        self,
        session: AsyncSession,
        user_id: int
    ) -> List[Dict[str, Any]]:
        """Get list of incomplete courses for a user."""
        from models import UserCourseProgress, Course
        
        stmt = select(UserCourseProgress).where(
            UserCourseProgress.user_id == user_id,
            UserCourseProgress.completion_percentage < 100,
        ).options(selectinload(UserCourseProgress.course))
        
        result = await session.execute(stmt)
        progress_records = result.scalars().all()
        
        incomplete = []
        for progress in progress_records:
            if progress.course:
                incomplete.append({
                    "course_id": progress.course_id,
                    "course_title": progress.course.title,
                    "progress": progress.completion_percentage,
                    "last_accessed": progress.last_accessed_at,
                })
        
        return incomplete

    async def _send_security_digest(self, company_id: int):
        """Send security digest emails to company admins."""
        logger.info(f"Sending security digest for company {company_id}")
        try:
            async with self.db() as session:
                # Get company admins
                stmt = select(User).where(
                    User.company_id == company_id,
                    User.role == "admin",
                    User.is_active == True,
                )
                result = await session.execute(stmt)
                admins = result.scalars().all()

                # Get security metrics
                from services.analytics_collector import AnalyticsCollector
                analytics = AnalyticsCollector(session, self.cache)
                
                # Get weekly metrics
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=7)
                metrics = await analytics.get_company_metrics(
                    company_id,
                    start_date,
                    end_date
                )

                # Send digest to each admin
                email_service = EmailCampaignService(session, self.cache)
                
                for admin in admins:
                    await email_service.email_service.send_tracked_email(
                        user_id=admin.id,
                        template_code="security_digest",
                        variables={
                            "metrics": metrics,
                            "period": "weekly",
                            "start_date": start_date,
                            "end_date": end_date,
                        }
                    )

        except Exception as e:
            logger.error(f"Failed to send security digest: {str(e)}")

    async def setup_default_schedules(self, company_id: int):
        """Set up default recurring campaigns for a company."""
        try:
            # Weekly security digest (every Monday at 9 AM)
            await self.schedule_campaign(
                campaign_type=CampaignType.SECURITY_DIGEST,
                campaign_id=company_id,
                execute_at=datetime.utcnow().replace(hour=9, minute=0, second=0),
                recurring={
                    "type": "cron",
                    "day_of_week": 0,  # Monday
                    "hour": 9,
                    "minute": 0,
                }
            )

            # Monthly training reminders (1st of each month)
            await self.schedule_campaign(
                campaign_type=CampaignType.TRAINING_REMINDER,
                campaign_id=company_id,
                execute_at=datetime.utcnow().replace(day=1, hour=10, minute=0, second=0),
                recurring={
                    "type": "cron",
                    "day": 1,
                    "hour": 10,
                    "minute": 0,
                }
            )

            logger.info(f"Set up default schedules for company {company_id}")

        except Exception as e:
            logger.error(f"Failed to set up default schedules: {str(e)}")

    async def pause_all_campaigns(self, company_id: int):
        """Pause all campaigns for a company."""
        campaigns = await self.get_scheduled_campaigns(company_id=company_id)
        
        paused = 0
        for campaign in campaigns:
            if campaign.get("is_active"):
                self.scheduler.pause_job(campaign["job_id"])
                paused += 1
        
        logger.info(f"Paused {paused} campaigns for company {company_id}")
        return paused

    async def resume_all_campaigns(self, company_id: int):
        """Resume all campaigns for a company."""
        campaigns = await self.get_scheduled_campaigns(company_id=company_id)
        
        resumed = 0
        for campaign in campaigns:
            job = self.scheduler.get_job(campaign["job_id"])
            if job and not job.next_run_time:
                self.scheduler.resume_job(campaign["job_id"])
                resumed += 1
        
        logger.info(f"Resumed {resumed} campaigns for company {company_id}")
        return resumed

    async def get_campaign_history(
        self,
        campaign_type: CampaignType,
        campaign_id: int,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get execution history for a campaign."""
        # This would typically query a campaign execution log table
        # For now, return mock data
        return []

    def shutdown(self):
        """Shutdown the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Campaign scheduler shut down")