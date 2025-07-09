"""
Email scheduling service using Celery for delayed and recurring email tasks.
"""

import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import logging
from celery import Celery
from celery.schedules import crontab
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.config import settings
from models import EmailCampaign, User, EmailTemplate

logger = logging.getLogger(__name__)

# Initialize Celery
celery_app = Celery(
    "email_scheduler",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_always_eager=settings.CELERY_TASK_ALWAYS_EAGER,
    task_eager_propagates=settings.CELERY_TASK_EAGER_PROPAGATES,
    task_soft_time_limit=300,  # 5 minutes
    task_time_limit=600,  # 10 minutes
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)


class EmailSchedulerService:
    """Service for scheduling email tasks with Celery."""

    def __init__(self, db: AsyncSession):
        """Initialize scheduler service."""
        self.db = db

    async def schedule_campaign(
        self,
        campaign_id: int,
        scheduled_at: datetime
    ) -> str:
        """Schedule a campaign to be sent at a specific time."""
        # Calculate delay
        delay = (scheduled_at - datetime.utcnow()).total_seconds()
        if delay < 0:
            raise ValueError("Scheduled time must be in the future")

        # Schedule task
        task = send_campaign_task.apply_async(
            args=[campaign_id],
            eta=scheduled_at,
            task_id=f"campaign_{campaign_id}",
        )

        logger.info(f"Scheduled campaign {campaign_id} for {scheduled_at}")
        return task.id

    async def schedule_recurring_campaign(
        self,
        campaign_id: int,
        schedule: Dict[str, Any]
    ) -> str:
        """
        Schedule a recurring campaign.

        Args:
            campaign_id: Campaign to send
            schedule: Schedule configuration
                - frequency: daily, weekly, monthly
                - time: HH:MM format
                - day_of_week: 0-6 for weekly
                - day_of_month: 1-31 for monthly
        """
        frequency = schedule.get("frequency", "daily")
        time_str = schedule.get("time", "09:00")
        hour, minute = map(int, time_str.split(":"))

        # Create crontab schedule
        if frequency == "daily":
            cron_schedule = crontab(hour=hour, minute=minute)
        elif frequency == "weekly":
            day_of_week = schedule.get("day_of_week", 1)  # Default Monday
            cron_schedule = crontab(
                hour=hour,
                minute=minute,
                day_of_week=day_of_week
            )
        elif frequency == "monthly":
            day_of_month = schedule.get("day_of_month", 1)
            cron_schedule = crontab(
                hour=hour,
                minute=minute,
                day_of_month=day_of_month
            )
        else:
            raise ValueError(f"Invalid frequency: {frequency}")

        # Add to periodic tasks
        task_name = f"recurring_campaign_{campaign_id}"
        celery_app.conf.beat_schedule[task_name] = {
            "task": "email_scheduler.send_campaign_task",
            "schedule": cron_schedule,
            "args": [campaign_id],
        }

        logger.info(f"Scheduled recurring campaign {campaign_id} with {frequency} frequency")
        return task_name

    async def cancel_campaign(self, campaign_id: int) -> bool:
        """Cancel a scheduled campaign."""
        try:
            # Revoke the task
            celery_app.control.revoke(
                f"campaign_{campaign_id}",
                terminate=True
            )

            # Remove from periodic tasks if exists
            task_name = f"recurring_campaign_{campaign_id}"
            if task_name in celery_app.conf.beat_schedule:
                del celery_app.conf.beat_schedule[task_name]

            logger.info(f"Cancelled scheduled campaign {campaign_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel campaign {campaign_id}: {str(e)}")
            return False

    async def schedule_user_email(
        self,
        user_id: int,
        template_id: int,
        scheduled_at: datetime,
        variables: Optional[Dict[str, Any]] = None
    ) -> str:
        """Schedule a single email to a user."""
        # Calculate delay
        delay = (scheduled_at - datetime.utcnow()).total_seconds()
        if delay < 0:
            raise ValueError("Scheduled time must be in the future")

        # Schedule task
        task = send_user_email_task.apply_async(
            args=[user_id, template_id, variables or {}],
            eta=scheduled_at,
        )

        logger.info(f"Scheduled email to user {user_id} for {scheduled_at}")
        return task.id

    async def schedule_batch_emails(
        self,
        user_emails: List[Dict[str, Any]],
        scheduled_at: datetime,
        batch_size: int = 100
    ) -> List[str]:
        """
        Schedule batch emails.

        Args:
            user_emails: List of dicts with user_id, template_id, variables
            scheduled_at: When to send
            batch_size: Number of emails per batch
        """
        task_ids = []

        # Split into batches
        for i in range(0, len(user_emails), batch_size):
            batch = user_emails[i:i + batch_size]
            
            # Schedule batch task
            task = send_batch_emails_task.apply_async(
                args=[batch],
                eta=scheduled_at,
            )
            task_ids.append(task.id)

        logger.info(f"Scheduled {len(task_ids)} batch email tasks")
        return task_ids

    async def get_scheduled_tasks(self) -> List[Dict[str, Any]]:
        """Get list of scheduled tasks."""
        # Get scheduled tasks from Celery
        inspect = celery_app.control.inspect()
        scheduled = inspect.scheduled()
        
        tasks = []
        if scheduled:
            for worker, task_list in scheduled.items():
                for task in task_list:
                    tasks.append({
                        "id": task["request"]["id"],
                        "name": task["request"]["name"],
                        "args": task["request"]["args"],
                        "eta": task["eta"],
                        "worker": worker,
                    })

        return tasks

    async def schedule_reminder_emails(
        self,
        campaign_id: int,
        reminder_intervals: List[int]  # Days before deadline
    ) -> List[str]:
        """Schedule reminder emails for a campaign."""
        campaign = await self.db.get(EmailCampaign, campaign_id)
        if not campaign:
            raise ValueError("Campaign not found")

        task_ids = []
        
        # Assume campaign has a deadline field
        deadline = getattr(campaign, 'deadline', None)
        if not deadline:
            raise ValueError("Campaign has no deadline set")

        for days_before in reminder_intervals:
            reminder_date = deadline - timedelta(days=days_before)
            if reminder_date > datetime.utcnow():
                task = send_campaign_reminder_task.apply_async(
                    args=[campaign_id, days_before],
                    eta=reminder_date,
                )
                task_ids.append(task.id)

        logger.info(f"Scheduled {len(task_ids)} reminder emails for campaign {campaign_id}")
        return task_ids


# Celery Tasks
@celery_app.task(name="email_scheduler.send_campaign_task")
def send_campaign_task(campaign_id: int):
    """Celery task to send a campaign."""
    # This would be called by Celery worker
    # Import here to avoid circular imports
    import asyncio
    from db.session import get_db
    from services.email_campaign import EmailCampaignService

    async def _send():
        async with get_db() as db:
            service = EmailCampaignService(db)
            await service._execute_campaign(campaign_id)

    # Run async function
    asyncio.run(_send())


@celery_app.task(name="email_scheduler.send_user_email_task")
def send_user_email_task(
    user_id: int,
    template_id: int,
    variables: Dict[str, Any]
):
    """Celery task to send email to a user."""
    import asyncio
    from db.session import get_db
    from services.email_service import ExtendedEmailService

    async def _send():
        async with get_db() as db:
            service = ExtendedEmailService(db)
            await service.send_tracked_email(
                user_id=user_id,
                template_id=template_id,
                variables=variables,
            )

    asyncio.run(_send())


@celery_app.task(name="email_scheduler.send_batch_emails_task")
def send_batch_emails_task(user_emails: List[Dict[str, Any]]):
    """Celery task to send batch emails."""
    import asyncio
    from db.session import get_db
    from services.email_service import ExtendedEmailService

    async def _send():
        async with get_db() as db:
            service = ExtendedEmailService(db)
            
            for email_data in user_emails:
                try:
                    await service.send_tracked_email(
                        user_id=email_data["user_id"],
                        template_id=email_data["template_id"],
                        variables=email_data.get("variables", {}),
                    )
                except Exception as e:
                    logger.error(f"Failed to send email: {str(e)}")

    asyncio.run(_send())


@celery_app.task(name="email_scheduler.send_campaign_reminder_task")
def send_campaign_reminder_task(campaign_id: int, days_before: int):
    """Celery task to send campaign reminder."""
    import asyncio
    from db.session import get_db
    from services.email_campaign import EmailCampaignService

    async def _send():
        async with get_db() as db:
            # Get campaign
            campaign = await db.get(EmailCampaign, campaign_id)
            if not campaign:
                return

            # Create reminder campaign
            service = EmailCampaignService(db)
            reminder_campaign = await service.create_campaign(
                name=f"{campaign.name} - {days_before} Day Reminder",
                template_id=campaign.template_id,  # Use reminder template
                company_id=campaign.company_id,
                target_users=campaign.target_users,
                variables={
                    **campaign.variables,
                    "days_remaining": days_before,
                    "original_campaign": campaign.name,
                },
                created_by=campaign.created_by,
            )

            # Execute immediately
            await service._execute_campaign(reminder_campaign.id)

    asyncio.run(_send())


# Periodic Tasks
@celery_app.task(name="email_scheduler.cleanup_old_emails")
def cleanup_old_emails():
    """Periodic task to clean up old email logs."""
    import asyncio
    from db.session import get_db
    from services.email_service import ExtendedEmailService

    async def _cleanup():
        async with get_db() as db:
            service = ExtendedEmailService(db)
            count = await service.cleanup_old_logs(days=90)
            logger.info(f"Cleaned up {count} old email logs")

    asyncio.run(_cleanup())


# Configure periodic tasks
celery_app.conf.beat_schedule.update({
    "cleanup-old-emails": {
        "task": "email_scheduler.cleanup_old_emails",
        "schedule": crontab(hour=2, minute=0),  # Run at 2 AM daily
    },
})