"""Campaign scheduler service for automated phishing campaign execution."""

import logging
from datetime import datetime, timedelta
from typing import List
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from sqlalchemy.orm import Session

from models import PhishingCampaign
from schemas.phishing import CampaignStatus
from services.phishing_service import PhishingService
from db.session import SessionLocal

logger = logging.getLogger(__name__)


class CampaignScheduler:
    """Service for scheduling and executing phishing campaigns."""
    
    def __init__(self):
        """Initialize campaign scheduler."""
        self.scheduler = AsyncIOScheduler()
        self.scheduler.start()
        logger.info("Campaign scheduler initialized")
    
    def get_db(self) -> Session:
        """Get database session."""
        db = SessionLocal()
        try:
            return db
        finally:
            db.close()
    
    async def check_scheduled_campaigns(self):
        """Check for campaigns that need to be started."""
        db = self.get_db()
        try:
            # Find campaigns that should be started
            now = datetime.utcnow()
            campaigns = db.query(PhishingCampaign).filter(
                PhishingCampaign.status == CampaignStatus.SCHEDULED,
                PhishingCampaign.scheduled_at <= now
            ).all()
            
            for campaign in campaigns:
                logger.info(f"Starting scheduled campaign: {campaign.name} (ID: {campaign.id})")
                await self.start_campaign(campaign.id, campaign.company_id)
                
        except Exception as e:
            logger.error(f"Error checking scheduled campaigns: {str(e)}")
        finally:
            db.close()
    
    async def start_campaign(self, campaign_id: int, company_id: int):
        """Start a scheduled campaign."""
        db = self.get_db()
        try:
            service = PhishingService(db)
            service.start_campaign(campaign_id, company_id)
            logger.info(f"Campaign {campaign_id} started successfully")
        except Exception as e:
            logger.error(f"Failed to start campaign {campaign_id}: {str(e)}")
        finally:
            db.close()
    
    def schedule_campaign(self, campaign_id: int, company_id: int, scheduled_at: datetime):
        """Schedule a campaign for future execution."""
        job_id = f"campaign_{campaign_id}"
        
        # Remove existing job if any
        existing_job = self.scheduler.get_job(job_id)
        if existing_job:
            self.scheduler.remove_job(job_id)
        
        # Schedule new job
        self.scheduler.add_job(
            func=self.start_campaign,
            trigger=DateTrigger(run_date=scheduled_at),
            args=[campaign_id, company_id],
            id=job_id,
            name=f"Start campaign {campaign_id}",
            misfire_grace_time=300  # 5 minutes grace period
        )
        
        logger.info(f"Campaign {campaign_id} scheduled for {scheduled_at}")
    
    def cancel_scheduled_campaign(self, campaign_id: int):
        """Cancel a scheduled campaign."""
        job_id = f"campaign_{campaign_id}"
        
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Cancelled scheduled campaign {campaign_id}")
        except Exception as e:
            logger.warning(f"Could not cancel job for campaign {campaign_id}: {str(e)}")
    
    def reschedule_campaign(self, campaign_id: int, company_id: int, new_scheduled_at: datetime):
        """Reschedule a campaign."""
        self.cancel_scheduled_campaign(campaign_id)
        self.schedule_campaign(campaign_id, company_id, new_scheduled_at)
    
    async def check_campaign_completion(self):
        """Check for campaigns that should be marked as completed."""
        db = self.get_db()
        try:
            # Find running campaigns
            campaigns = db.query(PhishingCampaign).filter(
                PhishingCampaign.status == CampaignStatus.RUNNING
            ).all()
            
            for campaign in campaigns:
                # Check if all emails have been sent
                pending_emails = any(
                    result.email_sent_at is None 
                    for result in campaign.results
                )
                
                if not pending_emails:
                    # Check if campaign has been running for at least 7 days
                    if campaign.started_at and (datetime.utcnow() - campaign.started_at).days >= 7:
                        campaign.status = CampaignStatus.COMPLETED
                        campaign.completed_at = datetime.utcnow()
                        db.commit()
                        logger.info(f"Campaign {campaign.id} marked as completed")
                        
        except Exception as e:
            logger.error(f"Error checking campaign completion: {str(e)}")
        finally:
            db.close()
    
    def start_background_tasks(self):
        """Start background tasks for campaign management."""
        # Check scheduled campaigns every minute
        self.scheduler.add_job(
            func=self.check_scheduled_campaigns,
            trigger="interval",
            minutes=1,
            id="check_scheduled_campaigns",
            name="Check scheduled campaigns"
        )
        
        # Check campaign completion every hour
        self.scheduler.add_job(
            func=self.check_campaign_completion,
            trigger="interval",
            hours=1,
            id="check_campaign_completion",
            name="Check campaign completion"
        )
        
        logger.info("Background tasks started")
    
    def shutdown(self):
        """Shutdown the scheduler."""
        self.scheduler.shutdown()
        logger.info("Campaign scheduler shut down")


# Global scheduler instance
campaign_scheduler = CampaignScheduler()