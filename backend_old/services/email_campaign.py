"""Email campaign service."""

import logging
from typing import List, Optional, Dict, Any, Set
from datetime import datetime, timedelta
import asyncio
import uuid
from collections import defaultdict

from sqlalchemy import and_, or_, select, update, func
from sqlalchemy.orm import Session, selectinload

from models.email_campaign import (
    EmailTemplate, EmailCampaign, EmailLog, EmailEvent,
    EmailPreference, EmailBounce,
    EmailStatus, CampaignStatus, EmailFrequency
)
from models.user import User, UserRole
from models.company import Company
from services.email import email_service
from services.email_template import template_engine, EmailPersonalization
from db.session import get_db
from core.config import settings

logger = logging.getLogger(__name__)


class EmailCampaignService:
    """Service for managing email campaigns."""
    
    def __init__(self):
        self.batch_size = 100  # Send emails in batches
        self.rate_limit = 10  # Emails per second
        
    async def create_campaign(
        self,
        db: Session,
        campaign_data: Dict[str, Any],
        company_id: str,
        created_by_id: str,
    ) -> EmailCampaign:
        """Create a new email campaign."""
        campaign = EmailCampaign(
            **campaign_data,
            company_id=company_id,
            created_by_id=created_by_id,
        )
        
        db.add(campaign)
        db.commit()
        db.refresh(campaign)
        
        logger.info(f"Created campaign {campaign.id} for company {company_id}")
        return campaign
    
    async def update_campaign(
        self,
        db: Session,
        campaign_id: str,
        updates: Dict[str, Any],
    ) -> EmailCampaign:
        """Update an email campaign."""
        campaign = db.query(EmailCampaign).filter(
            EmailCampaign.id == campaign_id
        ).first()
        
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")
        
        # Don't allow updates to sent campaigns
        if campaign.status in [CampaignStatus.SENDING, CampaignStatus.SENT, CampaignStatus.COMPLETED]:
            raise ValueError("Cannot update campaign that has been sent")
        
        for key, value in updates.items():
            setattr(campaign, key, value)
        
        campaign.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(campaign)
        
        return campaign
    
    async def get_campaign_recipients(
        self,
        db: Session,
        campaign: EmailCampaign,
    ) -> List[User]:
        """Get list of recipients for a campaign."""
        query = db.query(User).join(Company).filter(
            User.company_id == campaign.company_id,
            User.is_active == True,
            User.email_verified == True,
        )
        
        # Apply targeting filters
        if not campaign.target_all_users:
            conditions = []
            
            # Target specific roles
            if campaign.target_user_roles:
                conditions.append(User.role.in_(campaign.target_user_roles))
            
            # Target specific users
            if campaign.target_user_ids:
                conditions.append(User.id.in_(campaign.target_user_ids))
            
            if conditions:
                query = query.filter(or_(*conditions))
        
        # Exclude unsubscribed users
        if campaign.exclude_unsubscribed:
            query = query.outerjoin(EmailPreference).filter(
                or_(
                    EmailPreference.is_subscribed == True,
                    EmailPreference.id == None,  # No preference = subscribed
                )
            )
        
        # Exclude bounced emails
        bounced_emails = db.query(EmailBounce.email).filter(
            EmailBounce.is_suppressed == True
        ).subquery()
        query = query.filter(~User.email.in_(bounced_emails))
        
        recipients = query.all()
        
        # Apply custom segments if defined
        if campaign.target_segments:
            recipients = self._apply_segments(recipients, campaign.target_segments)
        
        return recipients
    
    def _apply_segments(self, users: List[User], segments: Dict[str, Any]) -> List[User]:
        """Apply custom segmentation rules."""
        filtered = users
        
        # Example segments - extend as needed
        if 'min_days_since_registration' in segments:
            min_date = datetime.utcnow() - timedelta(days=segments['min_days_since_registration'])
            filtered = [u for u in filtered if u.created_at <= min_date]
        
        if 'max_days_since_registration' in segments:
            max_date = datetime.utcnow() - timedelta(days=segments['max_days_since_registration'])
            filtered = [u for u in filtered if u.created_at >= max_date]
        
        if 'has_completed_courses' in segments and segments['has_completed_courses']:
            filtered = [u for u in filtered if len(u.completed_courses) > 0]
        
        return filtered
    
    async def send_campaign(
        self,
        db: Session,
        campaign_id: str,
        test_mode: bool = False,
        test_recipients: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Send an email campaign."""
        campaign = db.query(EmailCampaign).options(
            selectinload(EmailCampaign.template),
            selectinload(EmailCampaign.company),
        ).filter(
            EmailCampaign.id == campaign_id
        ).first()
        
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")
        
        if not campaign.template:
            raise ValueError("Campaign has no template")
        
        # Check campaign status
        if campaign.status not in [CampaignStatus.DRAFT, CampaignStatus.SCHEDULED]:
            raise ValueError(f"Cannot send campaign in status {campaign.status}")
        
        # Update campaign status
        campaign.status = CampaignStatus.SENDING
        campaign.sent_at = datetime.utcnow()
        db.commit()
        
        try:
            # Get recipients
            if test_mode and test_recipients:
                recipients = db.query(User).filter(
                    User.email.in_(test_recipients)
                ).all()
            else:
                recipients = await self.get_campaign_recipients(db, campaign)
            
            campaign.total_recipients = len(recipients)
            db.commit()
            
            # Send emails in batches
            sent_count = 0
            failed_count = 0
            
            for i in range(0, len(recipients), self.batch_size):
                batch = recipients[i:i + self.batch_size]
                results = await self._send_batch(db, campaign, batch)
                
                sent_count += results['sent']
                failed_count += results['failed']
                
                # Update progress
                campaign.total_sent = sent_count
                db.commit()
                
                # Rate limiting
                await asyncio.sleep(len(batch) / self.rate_limit)
            
            # Update campaign status
            campaign.status = CampaignStatus.COMPLETED
            campaign.completed_at = datetime.utcnow()
            campaign.total_sent = sent_count
            db.commit()
            
            logger.info(f"Campaign {campaign_id} completed: {sent_count} sent, {failed_count} failed")
            
            return {
                'campaign_id': str(campaign.id),
                'total_recipients': len(recipients),
                'sent': sent_count,
                'failed': failed_count,
            }
            
        except Exception as e:
            # Update campaign status on error
            campaign.status = CampaignStatus.PAUSED
            db.commit()
            
            logger.error(f"Campaign {campaign_id} failed: {str(e)}")
            raise
    
    async def _send_batch(
        self,
        db: Session,
        campaign: EmailCampaign,
        recipients: List[User],
    ) -> Dict[str, int]:
        """Send emails to a batch of recipients."""
        sent = 0
        failed = 0
        
        for recipient in recipients:
            try:
                # Create email log entry
                email_log = EmailLog(
                    campaign_id=campaign.id,
                    template_id=campaign.template.id,
                    user_id=recipient.id,
                    to_email=recipient.email,
                    from_email=campaign.template.from_email or settings.SMTP_FROM_EMAIL,
                    subject=campaign.custom_subject or campaign.template.subject,
                    status=EmailStatus.PENDING,
                )
                db.add(email_log)
                db.commit()
                
                # Get personalization variables
                user_vars = EmailPersonalization.get_default_variables(
                    recipient,
                    campaign.company
                )
                
                # Merge with campaign variables
                variables = EmailPersonalization.merge_variables(
                    user_vars,
                    campaign.template.variables,
                    campaign.custom_variables,
                )
                
                # Get user's unsubscribe token
                pref = db.query(EmailPreference).filter(
                    EmailPreference.user_id == recipient.id
                ).first()
                
                if pref:
                    variables['unsubscribe_token'] = pref.unsubscribe_token
                
                # Render template
                rendered = template_engine.render_template(
                    campaign.template.html_content,
                    variables,
                    campaign.template.text_content,
                    str(email_log.id),
                )
                
                # Send email
                success = await email_service.send_email(
                    to_email=recipient.email,
                    subject=email_log.subject,
                    html_content=rendered['html'],
                    text_content=rendered['text'],
                )
                
                if success:
                    email_log.status = EmailStatus.SENT
                    email_log.sent_at = datetime.utcnow()
                    email_log.provider = 'smtp'  # Update based on actual provider
                    sent += 1
                else:
                    email_log.status = EmailStatus.FAILED
                    email_log.error_message = "Failed to send email"
                    failed += 1
                
                db.commit()
                
            except Exception as e:
                logger.error(f"Failed to send email to {recipient.email}: {str(e)}")
                
                if 'email_log' in locals():
                    email_log.status = EmailStatus.FAILED
                    email_log.error_message = str(e)
                    db.commit()
                
                failed += 1
        
        return {'sent': sent, 'failed': failed}
    
    async def track_email_open(
        self,
        db: Session,
        email_log_id: str,
        request_data: Dict[str, Any],
    ) -> None:
        """Track email open event."""
        email_log = db.query(EmailLog).filter(
            EmailLog.id == email_log_id
        ).first()
        
        if not email_log:
            return
        
        # Update email log
        if not email_log.first_opened_at:
            email_log.first_opened_at = datetime.utcnow()
            email_log.status = EmailStatus.OPENED
        
        email_log.opened_at = datetime.utcnow()
        email_log.open_count += 1
        
        # Create event
        event = EmailEvent(
            email_log_id=email_log_id,
            event_type='open',
            ip_address=request_data.get('ip_address'),
            user_agent=request_data.get('user_agent'),
            device_type=request_data.get('device_type'),
            os=request_data.get('os'),
            browser=request_data.get('browser'),
            location=request_data.get('location'),
        )
        db.add(event)
        
        # Update campaign stats
        if email_log.campaign_id:
            await self._update_campaign_stats(db, email_log.campaign_id)
        
        db.commit()
    
    async def track_email_click(
        self,
        db: Session,
        email_log_id: str,
        clicked_url: str,
        position: Optional[int],
        request_data: Dict[str, Any],
    ) -> None:
        """Track email click event."""
        email_log = db.query(EmailLog).filter(
            EmailLog.id == email_log_id
        ).first()
        
        if not email_log:
            return
        
        # Update email log
        if not email_log.first_clicked_at:
            email_log.first_clicked_at = datetime.utcnow()
            email_log.status = EmailStatus.CLICKED
        
        email_log.clicked_at = datetime.utcnow()
        email_log.click_count += 1
        
        # Track clicked links
        if clicked_url not in email_log.clicked_links:
            email_log.clicked_links = email_log.clicked_links + [clicked_url]
        
        # Create event
        event = EmailEvent(
            email_log_id=email_log_id,
            event_type='click',
            clicked_url=clicked_url,
            click_position=position,
            ip_address=request_data.get('ip_address'),
            user_agent=request_data.get('user_agent'),
            device_type=request_data.get('device_type'),
            os=request_data.get('os'),
            browser=request_data.get('browser'),
            location=request_data.get('location'),
        )
        db.add(event)
        
        # Update campaign stats
        if email_log.campaign_id:
            await self._update_campaign_stats(db, email_log.campaign_id)
        
        db.commit()
    
    async def handle_bounce(
        self,
        db: Session,
        email: str,
        bounce_type: str,
        reason: Optional[str] = None,
        diagnostic_code: Optional[str] = None,
    ) -> None:
        """Handle email bounce."""
        # Update or create bounce record
        bounce = db.query(EmailBounce).filter(
            EmailBounce.email == email
        ).first()
        
        if bounce:
            bounce.bounce_count += 1
            bounce.last_bounce_at = datetime.utcnow()
            bounce.bounce_type = bounce_type
            bounce.reason = reason
            bounce.diagnostic_code = diagnostic_code
            
            # Suppress after 3 hard bounces
            if bounce_type == 'hard' and bounce.bounce_count >= 3:
                bounce.is_suppressed = True
                bounce.suppressed_at = datetime.utcnow()
        else:
            bounce = EmailBounce(
                email=email,
                bounce_type=bounce_type,
                reason=reason,
                diagnostic_code=diagnostic_code,
            )
            
            # Immediately suppress hard bounces
            if bounce_type == 'hard':
                bounce.is_suppressed = True
                bounce.suppressed_at = datetime.utcnow()
            
            db.add(bounce)
        
        # Update email log
        email_log = db.query(EmailLog).filter(
            EmailLog.to_email == email,
            EmailLog.status.in_([EmailStatus.SENT, EmailStatus.DELIVERED])
        ).order_by(EmailLog.sent_at.desc()).first()
        
        if email_log:
            email_log.status = EmailStatus.BOUNCED
            email_log.bounced_at = datetime.utcnow()
            email_log.bounce_type = bounce_type
            email_log.error_message = reason
            
            # Create event
            event = EmailEvent(
                email_log_id=email_log.id,
                event_type='bounce',
                bounce_reason=reason,
            )
            db.add(event)
            
            # Update campaign stats
            if email_log.campaign_id:
                await self._update_campaign_stats(db, email_log.campaign_id)
        
        db.commit()
    
    async def handle_unsubscribe(
        self,
        db: Session,
        user_id: str,
        token: str,
    ) -> bool:
        """Handle email unsubscribe."""
        pref = db.query(EmailPreference).filter(
            EmailPreference.user_id == user_id,
            EmailPreference.unsubscribe_token == token,
        ).first()
        
        if not pref:
            return False
        
        pref.is_subscribed = False
        pref.unsubscribed_at = datetime.utcnow()
        
        # Update latest email log
        email_log = db.query(EmailLog).filter(
            EmailLog.user_id == user_id,
            EmailLog.status != EmailStatus.UNSUBSCRIBED,
        ).order_by(EmailLog.sent_at.desc()).first()
        
        if email_log:
            email_log.status = EmailStatus.UNSUBSCRIBED
            email_log.unsubscribed_at = datetime.utcnow()
            
            # Create event
            event = EmailEvent(
                email_log_id=email_log.id,
                event_type='unsubscribe',
            )
            db.add(event)
            
            # Update campaign stats
            if email_log.campaign_id:
                await self._update_campaign_stats(db, email_log.campaign_id)
        
        db.commit()
        return True
    
    async def _update_campaign_stats(self, db: Session, campaign_id: str) -> None:
        """Update campaign statistics."""
        # Get aggregated stats
        stats = db.query(
            func.count(EmailLog.id).label('total_sent'),
            func.sum(func.cast(EmailLog.status == EmailStatus.DELIVERED, Integer)).label('delivered'),
            func.sum(func.cast(EmailLog.open_count > 0, Integer)).label('opened'),
            func.sum(func.cast(EmailLog.click_count > 0, Integer)).label('clicked'),
            func.sum(func.cast(EmailLog.status == EmailStatus.BOUNCED, Integer)).label('bounced'),
            func.sum(func.cast(EmailLog.status == EmailStatus.UNSUBSCRIBED, Integer)).label('unsubscribed'),
        ).filter(
            EmailLog.campaign_id == campaign_id,
            EmailLog.status != EmailStatus.PENDING,
        ).first()
        
        campaign = db.query(EmailCampaign).filter(
            EmailCampaign.id == campaign_id
        ).first()
        
        if campaign and stats:
            campaign.total_sent = stats.total_sent or 0
            campaign.total_delivered = stats.delivered or 0
            campaign.total_opened = stats.opened or 0
            campaign.total_clicked = stats.clicked or 0
            campaign.total_bounced = stats.bounced or 0
            campaign.total_unsubscribed = stats.unsubscribed or 0
            
            # Calculate rates
            if campaign.total_sent > 0:
                campaign.delivery_rate = (campaign.total_delivered / campaign.total_sent) * 100
                campaign.bounce_rate = (campaign.total_bounced / campaign.total_sent) * 100
                
            if campaign.total_delivered > 0:
                campaign.open_rate = (campaign.total_opened / campaign.total_delivered) * 100
                campaign.click_rate = (campaign.total_clicked / campaign.total_delivered) * 100
                campaign.unsubscribe_rate = (campaign.total_unsubscribed / campaign.total_delivered) * 100
    
    async def get_campaign_analytics(
        self,
        db: Session,
        campaign_id: str,
    ) -> Dict[str, Any]:
        """Get detailed campaign analytics."""
        campaign = db.query(EmailCampaign).filter(
            EmailCampaign.id == campaign_id
        ).first()
        
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")
        
        # Get time-based stats
        opens_by_hour = defaultdict(int)
        clicks_by_hour = defaultdict(int)
        
        open_events = db.query(EmailEvent).join(EmailLog).filter(
            EmailLog.campaign_id == campaign_id,
            EmailEvent.event_type == 'open',
        ).all()
        
        for event in open_events:
            hour = event.timestamp.hour
            opens_by_hour[hour] += 1
        
        click_events = db.query(EmailEvent).join(EmailLog).filter(
            EmailLog.campaign_id == campaign_id,
            EmailEvent.event_type == 'click',
        ).all()
        
        for event in click_events:
            hour = event.timestamp.hour
            clicks_by_hour[hour] += 1
        
        # Get device stats
        device_stats = db.query(
            EmailEvent.device_type,
            EmailEvent.event_type,
            func.count(EmailEvent.id).label('count'),
        ).join(EmailLog).filter(
            EmailLog.campaign_id == campaign_id,
            EmailEvent.event_type.in_(['open', 'click']),
        ).group_by(
            EmailEvent.device_type,
            EmailEvent.event_type,
        ).all()
        
        opens_by_device = defaultdict(int)
        clicks_by_device = defaultdict(int)
        
        for stat in device_stats:
            if stat.event_type == 'open':
                opens_by_device[stat.device_type or 'unknown'] = stat.count
            else:
                clicks_by_device[stat.device_type or 'unknown'] = stat.count
        
        # Get link performance
        link_clicks = db.query(
            EmailEvent.clicked_url,
            func.count(EmailEvent.id).label('clicks'),
            func.count(func.distinct(EmailEvent.email_log_id)).label('unique_clicks'),
        ).join(EmailLog).filter(
            EmailLog.campaign_id == campaign_id,
            EmailEvent.event_type == 'click',
        ).group_by(
            EmailEvent.clicked_url,
        ).order_by(
            func.count(EmailEvent.id).desc(),
        ).all()
        
        return {
            'campaign_id': str(campaign.id),
            'name': campaign.name,
            'status': campaign.status,
            'scheduled_at': campaign.scheduled_at,
            'sent_at': campaign.sent_at,
            'completed_at': campaign.completed_at,
            'total_recipients': campaign.total_recipients,
            'total_sent': campaign.total_sent,
            'total_delivered': campaign.total_delivered,
            'total_opened': campaign.total_opened,
            'total_clicked': campaign.total_clicked,
            'total_bounced': campaign.total_bounced,
            'total_unsubscribed': campaign.total_unsubscribed,
            'delivery_rate': campaign.delivery_rate,
            'open_rate': campaign.open_rate,
            'click_rate': campaign.click_rate,
            'bounce_rate': campaign.bounce_rate,
            'unsubscribe_rate': campaign.unsubscribe_rate,
            'opens_by_hour': dict(opens_by_hour),
            'clicks_by_hour': dict(clicks_by_hour),
            'opens_by_device': dict(opens_by_device),
            'clicks_by_device': dict(clicks_by_device),
            'link_clicks': [
                {
                    'url': click.clicked_url,
                    'clicks': click.clicks,
                    'unique_clicks': click.unique_clicks,
                }
                for click in link_clicks
            ],
        }


# Global campaign service instance
campaign_service = EmailCampaignService()