"""Email scheduling service using Celery."""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from celery import Celery
from celery.schedules import crontab

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from models.email_campaign import (
    EmailCampaign, EmailPreference, EmailLog,
    CampaignStatus, EmailFrequency, EmailStatus
)
from models.user import User
from services.email_campaign import campaign_service
from core.config import settings
from db.session import AsyncSessionLocal as SessionLocal

logger = logging.getLogger(__name__)

# Initialize Celery
celery_app = Celery(
    'email_scheduler',
    broker=settings.REDIS_URL or 'redis://localhost:6379/0',
    backend=settings.REDIS_URL or 'redis://localhost:6379/0',
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_routes={
        'email_scheduler.send_scheduled_campaigns': {'queue': 'campaigns'},
        'email_scheduler.send_campaign_task': {'queue': 'campaigns'},
        'email_scheduler.send_digest_emails': {'queue': 'digests'},
        'email_scheduler.cleanup_old_logs': {'queue': 'maintenance'},
    },
)

# Configure periodic tasks
celery_app.conf.beat_schedule = {
    'check-scheduled-campaigns': {
        'task': 'email_scheduler.send_scheduled_campaigns',
        'schedule': timedelta(minutes=5),  # Check every 5 minutes
    },
    'send-daily-digests': {
        'task': 'email_scheduler.send_digest_emails',
        'schedule': crontab(hour=9, minute=0),  # Daily at 9 AM
        'kwargs': {'frequency': 'daily'},
    },
    'send-weekly-digests': {
        'task': 'email_scheduler.send_digest_emails',
        'schedule': crontab(hour=9, minute=0, day_of_week=1),  # Monday at 9 AM
        'kwargs': {'frequency': 'weekly'},
    },
    'cleanup-old-logs': {
        'task': 'email_scheduler.cleanup_old_logs',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
}


@celery_app.task(name='email_scheduler.send_scheduled_campaigns')
def send_scheduled_campaigns():
    """Check and send scheduled campaigns."""
    with SessionLocal() as db:
        # Find campaigns ready to send
        now = datetime.utcnow()
        campaigns = db.query(EmailCampaign).filter(
            EmailCampaign.status == CampaignStatus.SCHEDULED,
            EmailCampaign.scheduled_at <= now,
        ).all()
        
        for campaign in campaigns:
            # Queue campaign for sending
            send_campaign_task.apply_async(
                args=[str(campaign.id)],
                queue='campaigns',
            )
            
            logger.info(f"Queued campaign {campaign.id} for sending")
        
        return f"Queued {len(campaigns)} campaigns for sending"


@celery_app.task(name='email_scheduler.send_campaign_task', bind=True, max_retries=3)
def send_campaign_task(self, campaign_id: str):
    """Send a campaign asynchronously."""
    try:
        with SessionLocal() as db:
            result = asyncio.run(
                campaign_service.send_campaign(db, campaign_id)
            )
            return result
            
    except Exception as e:
        logger.error(f"Failed to send campaign {campaign_id}: {str(e)}")
        
        # Retry with exponential backoff
        retry_in = 60 * (2 ** self.request.retries)  # 1min, 2min, 4min
        raise self.retry(exc=e, countdown=retry_in)


@celery_app.task(name='email_scheduler.send_digest_emails')
def send_digest_emails(frequency: str = 'daily'):
    """Send digest emails to users based on their preferences."""
    with SessionLocal() as db:
        # Map frequency to enum
        freq_map = {
            'daily': EmailFrequency.DAILY,
            'weekly': EmailFrequency.WEEKLY,
            'monthly': EmailFrequency.MONTHLY,
        }
        
        email_frequency = freq_map.get(frequency)
        if not email_frequency:
            return f"Invalid frequency: {frequency}"
        
        # Get users with this digest preference
        users = db.query(User).join(EmailPreference).filter(
            EmailPreference.email_frequency == email_frequency,
            EmailPreference.is_subscribed == True,
            User.is_active == True,
            User.email_verified == True,
        ).all()
        
        sent_count = 0
        
        for user in users:
            # Check if it's the right day for weekly digests
            if frequency == 'weekly' and user.email_preference.digest_day != datetime.utcnow().weekday():
                continue
            
            # Collect digest content
            digest_content = collect_digest_content(db, user, frequency)
            
            if digest_content:
                # Send digest email
                send_digest_email.apply_async(
                    args=[str(user.id), digest_content],
                    queue='digests',
                )
                sent_count += 1
        
        return f"Queued {sent_count} {frequency} digest emails"


@celery_app.task(name='email_scheduler.send_digest_email')
def send_digest_email(user_id: str, content: Dict[str, Any]):
    """Send a digest email to a user."""
    try:
        with SessionLocal() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return
            
            # Get digest template
            template = db.query(EmailTemplate).filter(
                EmailTemplate.slug == 'digest-email',
                EmailTemplate.is_active == True,
            ).first()
            
            if not template:
                logger.warning("Digest email template not found")
                return
            
            # Create email log
            email_log = EmailLog(
                template_id=template.id,
                user_id=user.id,
                to_email=user.email,
                from_email=template.from_email or settings.SMTP_FROM_EMAIL,
                subject=template.subject,
                status=EmailStatus.PENDING,
            )
            db.add(email_log)
            db.commit()
            
            # Prepare variables
            variables = EmailPersonalization.get_default_variables(user)
            variables.update(content)
            
            # Render and send
            rendered = template_engine.render_template(
                template.html_content,
                variables,
                template.text_content,
                str(email_log.id),
            )
            
            success = asyncio.run(
                email_service.send_email(
                    to_email=user.email,
                    subject=template.subject,
                    html_content=rendered['html'],
                    text_content=rendered['text'],
                )
            )
            
            if success:
                email_log.status = EmailStatus.SENT
                email_log.sent_at = datetime.utcnow()
            else:
                email_log.status = EmailStatus.FAILED
            
            db.commit()
            
    except Exception as e:
        logger.error(f"Failed to send digest email to user {user_id}: {str(e)}")


def collect_digest_content(db: Session, user: User, frequency: str) -> Optional[Dict[str, Any]]:
    """Collect content for digest email."""
    content = {}
    
    # Determine time range
    if frequency == 'daily':
        since = datetime.utcnow() - timedelta(days=1)
    elif frequency == 'weekly':
        since = datetime.utcnow() - timedelta(days=7)
    else:  # monthly
        since = datetime.utcnow() - timedelta(days=30)
    
    # Get new courses
    from models.course import Course, CourseStatus
    new_courses = db.query(Course).filter(
        Course.created_at >= since,
        Course.status == CourseStatus.PUBLISHED,
        Course.company_id == user.company_id,
    ).all()
    
    if new_courses:
        content['new_courses'] = [
            {
                'id': str(course.id),
                'title': course.title,
                'description': course.description,
                'difficulty': course.difficulty_level.value,
            }
            for course in new_courses
        ]
    
    # Get security alerts
    from models.phishing import PhishingResult
    phishing_attempts = db.query(PhishingResult).filter(
        PhishingResult.user_id == user.id,
        PhishingResult.created_at >= since,
    ).count()
    
    if phishing_attempts > 0:
        content['security_alerts'] = {
            'phishing_attempts': phishing_attempts,
        }
    
    # Get course progress
    from models.course import CourseEnrollment
    enrollments = db.query(CourseEnrollment).filter(
        CourseEnrollment.user_id == user.id,
        CourseEnrollment.updated_at >= since,
    ).all()
    
    if enrollments:
        content['course_progress'] = [
            {
                'course_title': enrollment.course.title,
                'progress': enrollment.progress_percentage,
                'completed': enrollment.completed_at is not None,
            }
            for enrollment in enrollments
        ]
    
    # Only return content if there's something to report
    return content if content else None


@celery_app.task(name='email_scheduler.cleanup_old_logs')
def cleanup_old_logs():
    """Clean up old email logs and events."""
    with SessionLocal() as db:
        # Delete logs older than 90 days
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        
        # Delete events first (due to foreign key)
        deleted_events = db.query(EmailEvent).filter(
            EmailEvent.timestamp < cutoff_date
        ).delete()
        
        # Delete logs
        deleted_logs = db.query(EmailLog).filter(
            EmailLog.created_at < cutoff_date
        ).delete()
        
        db.commit()
        
        logger.info(f"Cleaned up {deleted_events} events and {deleted_logs} logs")
        return f"Deleted {deleted_events} events and {deleted_logs} logs"


@celery_app.task(name='email_scheduler.schedule_campaign')
def schedule_campaign(campaign_id: str, scheduled_at: datetime):
    """Schedule a campaign for future sending."""
    with SessionLocal() as db:
        campaign = db.query(EmailCampaign).filter(
            EmailCampaign.id == campaign_id
        ).first()
        
        if not campaign:
            return f"Campaign {campaign_id} not found"
        
        campaign.status = CampaignStatus.SCHEDULED
        campaign.scheduled_at = scheduled_at
        db.commit()
        
        logger.info(f"Campaign {campaign_id} scheduled for {scheduled_at}")
        return f"Campaign scheduled for {scheduled_at}"


# Import asyncio for async tasks
import asyncio
from services.email_template import template_engine, EmailPersonalization
from models.email_campaign import EmailTemplate, EmailEvent