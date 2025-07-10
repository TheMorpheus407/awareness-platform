"""
Email campaign management service for creating and managing email campaigns.
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from models import (
    EmailCampaign, CampaignStatus, EmailTemplate, EmailLog,
    User, Company, EmailPreferences, EmailFrequency
)
from services.email_service import ExtendedEmailService
from services.email_scheduler import EmailSchedulerService
from core.exceptions import ValidationError
from core.cache import cache

logger = logging.getLogger(__name__)


class EmailCampaignService:
    """Service for managing email campaigns."""

    def __init__(self, db: AsyncSession, cache=None):
        """Initialize campaign service."""
        self.db = db
        self.cache = cache
        self.email_service = ExtendedEmailService(db, cache)
        self.scheduler_service = EmailSchedulerService(db)

    async def create_campaign(
        self,
        name: str,
        template_id: int,
        company_id: int,
        target_users: Optional[List[int]] = None,
        target_filters: Optional[Dict[str, Any]] = None,
        scheduled_at: Optional[datetime] = None,
        variables: Optional[Dict[str, Any]] = None,
        created_by: int = None,
    ) -> EmailCampaign:
        """
        Create a new email campaign.

        Args:
            name: Campaign name
            template_id: Email template to use
            company_id: Company ID
            target_users: Specific user IDs to target
            target_filters: Filters to select users dynamically
            scheduled_at: When to send the campaign
            variables: Default variables for the campaign
            created_by: User ID who created the campaign

        Returns:
            Created EmailCampaign
        """
        # Validate template exists
        template = await self.db.get(EmailTemplate, template_id)
        if not template:
            raise ValidationError("Template not found")

        # Get target users
        if target_users:
            recipients = target_users
        else:
            recipients = await self._get_filtered_users(company_id, target_filters)

        if not recipients:
            raise ValidationError("No recipients found for campaign")

        # Create campaign
        campaign = EmailCampaign(
            name=name,
            company_id=company_id,
            template_id=template_id,
            status=CampaignStatus.DRAFT,
            target_users=recipients,
            target_filters=target_filters,
            scheduled_at=scheduled_at,
            variables=variables or {},
            created_by=created_by,
            total_recipients=len(recipients),
        )

        self.db.add(campaign)
        await self.db.commit()
        await self.db.refresh(campaign)

        logger.info(f"Created campaign {campaign.id} with {len(recipients)} recipients")
        return campaign

    async def _get_filtered_users(
        self,
        company_id: int,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[int]:
        """Get users based on filters."""
        query = select(User.id).where(
            User.company_id == company_id,
            User.is_active == True,
            User.email_verified == True,
        )

        if filters:
            # Apply role filter
            if "roles" in filters:
                query = query.where(User.role.in_(filters["roles"]))

            # Apply department filter
            if "departments" in filters:
                query = query.where(User.department.in_(filters["departments"]))

            # Apply last active filter
            if "last_active_days" in filters:
                cutoff = datetime.utcnow() - timedelta(days=filters["last_active_days"])
                query = query.where(User.last_login >= cutoff)

            # Apply security score filter
            if "min_security_score" in filters:
                query = query.where(User.security_score >= filters["min_security_score"])

        # Check email preferences
        query = query.join(EmailPreferences, isouter=True).where(
            or_(
                EmailPreferences.id.is_(None),  # No preferences set
                EmailPreferences.marketing_emails == True,
            )
        )

        result = await self.db.execute(query)
        return [user_id for (user_id,) in result]

    async def update_campaign(
        self,
        campaign_id: int,
        **kwargs
    ) -> EmailCampaign:
        """Update campaign details."""
        campaign = await self.db.get(EmailCampaign, campaign_id)
        if not campaign:
            raise ValidationError("Campaign not found")

        # Only allow updates if campaign is in draft or scheduled status
        if campaign.status not in [CampaignStatus.DRAFT, CampaignStatus.SCHEDULED]:
            raise ValidationError(
                f"Cannot update campaign in {campaign.status} status"
            )

        # Update fields
        for key, value in kwargs.items():
            if hasattr(campaign, key):
                setattr(campaign, key, value)

        # Recalculate recipients if filters changed
        if "target_filters" in kwargs:
            recipients = await self._get_filtered_users(
                campaign.company_id,
                kwargs["target_filters"]
            )
            campaign.target_users = recipients
            campaign.total_recipients = len(recipients)

        await self.db.commit()
        await self.db.refresh(campaign)
        return campaign

    async def schedule_campaign(
        self,
        campaign_id: int,
        scheduled_at: datetime,
        send_immediately: bool = False
    ) -> EmailCampaign:
        """Schedule a campaign for sending."""
        campaign = await self.db.get(EmailCampaign, campaign_id)
        if not campaign:
            raise ValidationError("Campaign not found")

        if campaign.status != CampaignStatus.DRAFT:
            raise ValidationError(
                f"Can only schedule campaigns in DRAFT status, current: {campaign.status}"
            )

        # Validate scheduled time
        if not send_immediately and scheduled_at <= datetime.utcnow():
            raise ValidationError("Scheduled time must be in the future")

        # Update campaign
        campaign.scheduled_at = scheduled_at if not send_immediately else datetime.utcnow()
        campaign.status = CampaignStatus.SCHEDULED

        # Schedule the task
        if send_immediately:
            # Send immediately
            asyncio.create_task(self._execute_campaign(campaign_id))
        else:
            # Schedule for later
            await self.scheduler_service.schedule_campaign(
                campaign_id,
                scheduled_at
            )

        await self.db.commit()
        logger.info(f"Scheduled campaign {campaign_id} for {campaign.scheduled_at}")
        return campaign

    async def _execute_campaign(self, campaign_id: int) -> None:
        """Execute a campaign (send emails)."""
        try:
            campaign = await self.db.get(EmailCampaign, campaign_id)
            if not campaign:
                logger.error(f"Campaign {campaign_id} not found")
                return

            # Update status
            campaign.status = CampaignStatus.SENDING
            campaign.started_at = datetime.utcnow()
            await self.db.commit()

            # Get template
            template = await self.db.get(EmailTemplate, campaign.template_id)
            if not template:
                raise ValueError("Template not found")

            # Send emails to all recipients
            success_count = 0
            failed_count = 0

            for user_id in campaign.target_users:
                try:
                    # Check if user still meets criteria
                    user = await self.db.get(User, user_id)
                    if not user or not user.is_active or not user.email_verified:
                        continue

                    # Merge campaign variables with user-specific variables
                    variables = {
                        **campaign.variables,
                        "campaign": campaign,
                        "unsubscribe_link": f"{settings.FRONTEND_URL}/unsubscribe?token={user.unsubscribe_token}",
                    }

                    # Send email
                    await self.email_service.send_tracked_email(
                        user_id=user_id,
                        template_id=template.id,
                        variables=variables,
                        campaign_id=campaign.id,
                        track_opens=True,
                        track_clicks=True,
                    )
                    success_count += 1

                except Exception as e:
                    logger.error(f"Failed to send email to user {user_id}: {str(e)}")
                    failed_count += 1

                # Rate limiting - avoid overwhelming the email server
                if success_count % 50 == 0:
                    await asyncio.sleep(1)

            # Update campaign stats
            campaign.emails_sent = success_count
            campaign.emails_failed = failed_count
            campaign.status = CampaignStatus.COMPLETED
            campaign.completed_at = datetime.utcnow()

            await self.db.commit()
            logger.info(
                f"Campaign {campaign_id} completed: "
                f"{success_count} sent, {failed_count} failed"
            )

        except Exception as e:
            logger.error(f"Failed to execute campaign {campaign_id}: {str(e)}")
            # Update campaign status
            campaign = await self.db.get(EmailCampaign, campaign_id)
            if campaign:
                campaign.status = CampaignStatus.FAILED
                campaign.error_message = str(e)
                await self.db.commit()

    async def pause_campaign(self, campaign_id: int) -> EmailCampaign:
        """Pause a running campaign."""
        campaign = await self.db.get(EmailCampaign, campaign_id)
        if not campaign:
            raise ValidationError("Campaign not found")

        if campaign.status not in [CampaignStatus.SCHEDULED, CampaignStatus.SENDING]:
            raise ValidationError(
                f"Cannot pause campaign in {campaign.status} status"
            )

        campaign.status = CampaignStatus.PAUSED
        await self.db.commit()

        # Cancel scheduled task if exists
        await self.scheduler_service.cancel_campaign(campaign_id)

        return campaign

    async def resume_campaign(self, campaign_id: int) -> EmailCampaign:
        """Resume a paused campaign."""
        campaign = await self.db.get(EmailCampaign, campaign_id)
        if not campaign:
            raise ValidationError("Campaign not found")

        if campaign.status != CampaignStatus.PAUSED:
            raise ValidationError("Can only resume paused campaigns")

        # Reschedule or continue sending
        if campaign.started_at:
            # Was already sending, continue
            campaign.status = CampaignStatus.SENDING
            asyncio.create_task(self._execute_campaign(campaign_id))
        else:
            # Was scheduled, reschedule
            campaign.status = CampaignStatus.SCHEDULED
            if campaign.scheduled_at and campaign.scheduled_at > datetime.utcnow():
                await self.scheduler_service.schedule_campaign(
                    campaign_id,
                    campaign.scheduled_at
                )

        await self.db.commit()
        return campaign

    async def cancel_campaign(self, campaign_id: int) -> EmailCampaign:
        """Cancel a campaign."""
        campaign = await self.db.get(EmailCampaign, campaign_id)
        if not campaign:
            raise ValidationError("Campaign not found")

        if campaign.status in [CampaignStatus.COMPLETED, CampaignStatus.CANCELLED]:
            raise ValidationError(f"Campaign already {campaign.status}")

        campaign.status = CampaignStatus.CANCELLED
        campaign.completed_at = datetime.utcnow()
        await self.db.commit()

        # Cancel scheduled task if exists
        await self.scheduler_service.cancel_campaign(campaign_id)

        return campaign

    async def get_campaign_stats(self, campaign_id: int) -> Dict[str, Any]:
        """Get detailed campaign statistics."""
        campaign = await self.db.get(EmailCampaign, campaign_id)
        if not campaign:
            raise ValidationError("Campaign not found")

        # Get email stats
        stats = await self.email_service.get_email_stats(
            campaign_id=campaign_id
        )

        # Add campaign-specific stats
        stats.update({
            "campaign_id": campaign.id,
            "campaign_name": campaign.name,
            "status": campaign.status,
            "scheduled_at": campaign.scheduled_at,
            "started_at": campaign.started_at,
            "completed_at": campaign.completed_at,
            "total_recipients": campaign.total_recipients,
            "progress": (
                (campaign.emails_sent / campaign.total_recipients * 100)
                if campaign.total_recipients > 0 else 0
            ),
        })

        # Get engagement timeline
        query = select(
            func.date_trunc('hour', EmailLog.created_at).label('hour'),
            func.count(EmailLog.id).label('sent'),
            func.count(EmailLog.opened_at).label('opened'),
            func.count(EmailLog.clicked_at).label('clicked'),
        ).where(
            EmailLog.campaign_id == campaign_id
        ).group_by('hour').order_by('hour')

        result = await self.db.execute(query)
        timeline = []
        for row in result:
            timeline.append({
                "hour": row.hour,
                "sent": row.sent,
                "opened": row.opened,
                "clicked": row.clicked,
            })

        stats["timeline"] = timeline

        return stats

    async def duplicate_campaign(
        self,
        campaign_id: int,
        new_name: str,
        created_by: int
    ) -> EmailCampaign:
        """Create a copy of an existing campaign."""
        original = await self.db.get(EmailCampaign, campaign_id)
        if not original:
            raise ValidationError("Campaign not found")

        # Create new campaign
        new_campaign = EmailCampaign(
            name=new_name,
            company_id=original.company_id,
            template_id=original.template_id,
            status=CampaignStatus.DRAFT,
            target_users=original.target_users.copy(),
            target_filters=original.target_filters.copy() if original.target_filters else None,
            variables=original.variables.copy() if original.variables else {},
            created_by=created_by,
            total_recipients=original.total_recipients,
        )

        self.db.add(new_campaign)
        await self.db.commit()
        await self.db.refresh(new_campaign)

        return new_campaign

    async def test_campaign(
        self,
        campaign_id: int,
        test_emails: List[str]
    ) -> Dict[str, Any]:
        """Send test emails for a campaign."""
        campaign = await self.db.get(EmailCampaign, campaign_id)
        if not campaign:
            raise ValidationError("Campaign not found")

        # Get template
        template = await self.db.get(EmailTemplate, campaign.template_id)
        if not template:
            raise ValidationError("Template not found")

        # Send test emails
        results = {"success": [], "failed": []}
        
        for email in test_emails:
            try:
                # Create test variables
                variables = {
                    **campaign.variables,
                    "campaign": campaign,
                    "user": {
                        "first_name": "Test",
                        "last_name": "User",
                        "email": email,
                    },
                    "is_test": True,
                }

                # Render template
                content = await self.email_service.template_service.render_template(
                    template_id=template.id,
                    variables=variables
                )

                # Send email (without tracking for tests)
                success = await self.email_service.send_email(
                    to_email=email,
                    subject=f"[TEST] {content['subject']}",
                    body=content['body_text'],
                    html_body=content['body_html'],
                )

                if success:
                    results["success"].append(email)
                else:
                    results["failed"].append(email)

            except Exception as e:
                logger.error(f"Failed to send test email to {email}: {str(e)}")
                results["failed"].append(email)

        return results