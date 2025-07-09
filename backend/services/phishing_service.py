"""
Phishing campaign service for managing phishing simulations and training.
"""

import asyncio
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
import logging
from urllib.parse import urlencode
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from models import (
    PhishingCampaign, PhishingTemplate, PhishingResult,
    User, Company, EmailLog, CampaignStatus, EmailStatus
)
from services.email_service import ExtendedEmailService
from core.config import settings
from core.exceptions import ValidationError, PermissionDenied
from core.cache import get_cache

logger = logging.getLogger(__name__)


class PhishingService:
    """Service for managing phishing campaigns and simulations."""

    def __init__(self, db: AsyncSession, cache=None):
        """Initialize phishing service."""
        self.db = db
        self.cache = cache or get_cache()
        self.email_service = ExtendedEmailService(db, cache)

    async def create_campaign(
        self,
        name: str,
        company_id: int,
        template_id: int,
        target_users: List[int],
        landing_page_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        created_by: int = None,
    ) -> PhishingCampaign:
        """
        Create a new phishing campaign.

        Args:
            name: Campaign name
            company_id: Company ID
            template_id: Phishing template to use
            target_users: List of user IDs to target
            landing_page_id: Optional custom landing page
            start_date: When to start the campaign
            end_date: When to end the campaign
            created_by: User who created the campaign

        Returns:
            Created PhishingCampaign
        """
        # Validate template
        template = await self.db.get(PhishingTemplate, template_id)
        if not template:
            raise ValidationError("Template not found")

        # Validate users belong to company
        stmt = select(User.id).where(
            User.id.in_(target_users),
            User.company_id == company_id,
            User.is_active == True,
        )
        result = await self.db.execute(stmt)
        valid_users = [user_id for (user_id,) in result]

        if len(valid_users) != len(target_users):
            raise ValidationError("Some users are invalid or don't belong to the company")

        # Create campaign
        campaign = PhishingCampaign(
            name=name,
            company_id=company_id,
            template_id=template_id,
            target_users=valid_users,
            landing_page_id=landing_page_id,
            start_date=start_date or datetime.utcnow(),
            end_date=end_date or (datetime.utcnow() + timedelta(days=30)),
            status=CampaignStatus.DRAFT,
            created_by=created_by,
        )

        self.db.add(campaign)
        await self.db.commit()
        await self.db.refresh(campaign)

        logger.info(f"Created phishing campaign {campaign.id}")
        return campaign

    async def launch_campaign(self, campaign_id: int) -> PhishingCampaign:
        """Launch a phishing campaign."""
        campaign = await self.db.get(
            PhishingCampaign,
            campaign_id,
            options=[selectinload(PhishingCampaign.template)]
        )
        if not campaign:
            raise ValidationError("Campaign not found")

        if campaign.status != CampaignStatus.DRAFT:
            raise ValidationError(f"Campaign is already {campaign.status}")

        # Update status
        campaign.status = CampaignStatus.SCHEDULED
        await self.db.commit()

        # Start sending phishing emails
        asyncio.create_task(self._execute_campaign(campaign_id))

        return campaign

    async def _execute_campaign(self, campaign_id: int) -> None:
        """Execute the phishing campaign."""
        try:
            campaign = await self.db.get(
                PhishingCampaign,
                campaign_id,
                options=[selectinload(PhishingCampaign.template)]
            )
            if not campaign:
                return

            # Update status
            campaign.status = CampaignStatus.SENDING
            await self.db.commit()

            template = campaign.template
            success_count = 0
            failed_count = 0

            # Send phishing emails to all targets
            for user_id in campaign.target_users:
                try:
                    # Generate unique tracking token
                    tracking_token = self._generate_tracking_token(
                        campaign_id,
                        user_id
                    )

                    # Create phishing result entry
                    result = PhishingResult(
                        campaign_id=campaign_id,
                        user_id=user_id,
                        tracking_token=tracking_token,
                        sent_at=datetime.utcnow(),
                    )
                    self.db.add(result)
                    await self.db.flush()

                    # Get user details
                    user = await self.db.get(User, user_id)
                    if not user or not user.is_active:
                        continue

                    # Prepare phishing email content
                    phishing_link = self._create_phishing_link(
                        campaign_id,
                        tracking_token,
                        template.target_url
                    )

                    # Replace placeholders in template
                    variables = {
                        "user": user,
                        "company": await self.db.get(Company, campaign.company_id),
                        "phishing_link": phishing_link,
                        "current_date": datetime.utcnow(),
                    }

                    # Send phishing email
                    subject = self._replace_placeholders(template.subject, variables)
                    body = self._replace_placeholders(template.body, variables)

                    # Track email but don't use standard tracking
                    # (we have our own tracking for phishing)
                    email_log = await self.email_service.send_tracked_email(
                        user_id=user_id,
                        subject=subject,
                        variables={
                            "body_text": body,
                            "body_html": self._create_html_body(template, body, phishing_link),
                        },
                        campaign_id=campaign_id,
                        track_opens=False,  # Use our own tracking
                        track_clicks=False,  # Use our own tracking
                    )

                    if email_log.status == EmailStatus.SENT:
                        success_count += 1
                    else:
                        failed_count += 1
                        result.error_message = "Failed to send email"

                except Exception as e:
                    logger.error(f"Failed to send phishing email to user {user_id}: {str(e)}")
                    failed_count += 1

                # Rate limiting
                if success_count % 25 == 0:
                    await asyncio.sleep(1)

            # Update campaign stats
            campaign.emails_sent = success_count
            campaign.emails_failed = failed_count
            campaign.status = CampaignStatus.ACTIVE
            campaign.launched_at = datetime.utcnow()

            await self.db.commit()
            logger.info(
                f"Phishing campaign {campaign_id} launched: "
                f"{success_count} sent, {failed_count} failed"
            )

        except Exception as e:
            logger.error(f"Failed to execute phishing campaign {campaign_id}: {str(e)}")
            campaign = await self.db.get(PhishingCampaign, campaign_id)
            if campaign:
                campaign.status = CampaignStatus.FAILED
                campaign.error_message = str(e)
                await self.db.commit()

    def _generate_tracking_token(self, campaign_id: int, user_id: int) -> str:
        """Generate a unique tracking token."""
        # Create unique token
        data = f"{campaign_id}:{user_id}:{datetime.utcnow().isoformat()}:{secrets.token_urlsafe(16)}"
        return hashlib.sha256(data.encode()).hexdigest()[:32]

    def _create_phishing_link(
        self,
        campaign_id: int,
        tracking_token: str,
        target_url: Optional[str] = None
    ) -> str:
        """Create the phishing link with tracking."""
        base_url = f"{settings.FRONTEND_URL}/api/v1/phishing/click"
        params = {
            "token": tracking_token,
            "campaign": campaign_id,
        }
        if target_url:
            params["redirect"] = target_url

        return f"{base_url}?{urlencode(params)}"

    def _replace_placeholders(self, text: str, variables: Dict[str, Any]) -> str:
        """Replace placeholders in template text."""
        if not text:
            return ""

        # Simple placeholder replacement
        for key, value in variables.items():
            if isinstance(value, dict):
                # Handle nested objects like user.first_name
                for subkey, subvalue in value.items():
                    text = text.replace(f"{{{{{key}.{subkey}}}}}", str(subvalue))
            else:
                text = text.replace(f"{{{{{key}}}}}", str(value))

        return text

    def _create_html_body(
        self,
        template: PhishingTemplate,
        body_text: str,
        phishing_link: str
    ) -> str:
        """Create HTML body for phishing email."""
        # If template has HTML, use it
        if hasattr(template, 'body_html') and template.body_html:
            return self._replace_placeholders(
                template.body_html,
                {"phishing_link": phishing_link}
            )

        # Otherwise, create simple HTML from text
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6;">
            {body_text.replace('\n', '<br>')}
        </body>
        </html>
        """
        return html_body

    async def track_click(
        self,
        tracking_token: str,
        ip_address: str,
        user_agent: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Track when a user clicks the phishing link.

        Returns:
            Tuple of (success, redirect_url)
        """
        # Find the phishing result
        stmt = select(PhishingResult).where(
            PhishingResult.tracking_token == tracking_token
        )
        result = await self.db.execute(stmt)
        phishing_result = result.scalar_one_or_none()

        if not phishing_result:
            logger.warning(f"Invalid tracking token: {tracking_token}")
            return False, None

        # Check if already clicked
        if phishing_result.clicked_at:
            logger.info(f"Duplicate click for token: {tracking_token}")
            return True, phishing_result.redirect_url

        # Update result
        phishing_result.clicked_at = datetime.utcnow()
        phishing_result.click_ip = ip_address
        phishing_result.click_user_agent = user_agent

        # Get campaign to check landing page
        campaign = await self.db.get(
            PhishingCampaign,
            phishing_result.campaign_id,
            options=[selectinload(PhishingCampaign.template)]
        )

        # Determine redirect URL
        redirect_url = None
        if campaign:
            if campaign.landing_page_id:
                # Custom landing page
                redirect_url = f"{settings.FRONTEND_URL}/phishing/landing/{campaign.landing_page_id}"
            elif campaign.template.target_url:
                # Template's target URL
                redirect_url = campaign.template.target_url
            else:
                # Default phishing education page
                redirect_url = f"{settings.FRONTEND_URL}/phishing/education?campaign={campaign.id}"

        phishing_result.redirect_url = redirect_url

        # Update user's phishing score (negative impact)
        user = await self.db.get(User, phishing_result.user_id)
        if user:
            user.phishing_clicks = (user.phishing_clicks or 0) + 1
            user.security_score = max(0, (user.security_score or 100) - 10)

        await self.db.commit()

        # Cache the click to prevent duplicate tracking
        await self.cache.setex(
            f"phishing_click:{tracking_token}",
            3600,  # 1 hour
            "1"
        )

        logger.info(f"Tracked phishing click for user {phishing_result.user_id}")
        return True, redirect_url

    async def track_data_submission(
        self,
        tracking_token: str,
        submitted_data: Dict[str, Any]
    ) -> bool:
        """Track when a user submits data on the phishing landing page."""
        # Find the phishing result
        stmt = select(PhishingResult).where(
            PhishingResult.tracking_token == tracking_token
        )
        result = await self.db.execute(stmt)
        phishing_result = result.scalar_one_or_none()

        if not phishing_result:
            return False

        # Update result
        phishing_result.data_submitted_at = datetime.utcnow()
        phishing_result.submitted_data = submitted_data

        # Further decrease security score
        user = await self.db.get(User, phishing_result.user_id)
        if user:
            user.phishing_data_submitted = (user.phishing_data_submitted or 0) + 1
            user.security_score = max(0, (user.security_score or 100) - 15)

        await self.db.commit()

        logger.info(f"Tracked data submission for user {phishing_result.user_id}")
        return True

    async def get_campaign_results(
        self,
        campaign_id: int
    ) -> Dict[str, Any]:
        """Get detailed results for a phishing campaign."""
        campaign = await self.db.get(PhishingCampaign, campaign_id)
        if not campaign:
            raise ValidationError("Campaign not found")

        # Get all results
        stmt = select(PhishingResult).where(
            PhishingResult.campaign_id == campaign_id
        ).options(selectinload(PhishingResult.user))
        result = await self.db.execute(stmt)
        results = result.scalars().all()

        # Calculate statistics
        total_sent = len(results)
        total_clicked = sum(1 for r in results if r.clicked_at)
        total_submitted = sum(1 for r in results if r.data_submitted_at)

        # Time-based statistics
        click_times = [
            (r.clicked_at - r.sent_at).total_seconds()
            for r in results
            if r.clicked_at and r.sent_at
        ]
        avg_click_time = sum(click_times) / len(click_times) if click_times else 0

        # Department/role breakdown
        dept_stats = {}
        role_stats = {}

        for result in results:
            if result.user:
                # Department stats
                dept = result.user.department or "Unknown"
                if dept not in dept_stats:
                    dept_stats[dept] = {"total": 0, "clicked": 0, "submitted": 0}
                dept_stats[dept]["total"] += 1
                if result.clicked_at:
                    dept_stats[dept]["clicked"] += 1
                if result.data_submitted_at:
                    dept_stats[dept]["submitted"] += 1

                # Role stats
                role = result.user.role
                if role not in role_stats:
                    role_stats[role] = {"total": 0, "clicked": 0, "submitted": 0}
                role_stats[role]["total"] += 1
                if result.clicked_at:
                    role_stats[role]["clicked"] += 1
                if result.data_submitted_at:
                    role_stats[role]["submitted"] += 1

        return {
            "campaign_id": campaign_id,
            "campaign_name": campaign.name,
            "status": campaign.status,
            "start_date": campaign.start_date,
            "end_date": campaign.end_date,
            "statistics": {
                "total_targets": len(campaign.target_users),
                "emails_sent": total_sent,
                "emails_clicked": total_clicked,
                "data_submitted": total_submitted,
                "click_rate": (total_clicked / total_sent * 100) if total_sent > 0 else 0,
                "submission_rate": (total_submitted / total_sent * 100) if total_sent > 0 else 0,
                "average_click_time_seconds": avg_click_time,
            },
            "department_breakdown": dept_stats,
            "role_breakdown": role_stats,
            "timeline": self._generate_timeline(results),
            "user_results": [
                {
                    "user_id": r.user_id,
                    "user_name": f"{r.user.first_name} {r.user.last_name}" if r.user else "Unknown",
                    "department": r.user.department if r.user else None,
                    "sent_at": r.sent_at,
                    "clicked_at": r.clicked_at,
                    "data_submitted_at": r.data_submitted_at,
                    "time_to_click": (
                        (r.clicked_at - r.sent_at).total_seconds()
                        if r.clicked_at and r.sent_at else None
                    ),
                }
                for r in results
            ],
        }

    def _generate_timeline(self, results: List[PhishingResult]) -> List[Dict[str, Any]]:
        """Generate timeline of campaign events."""
        timeline = []

        # Group by hour
        hourly_stats = {}
        for result in results:
            if result.sent_at:
                hour = result.sent_at.replace(minute=0, second=0, microsecond=0)
                if hour not in hourly_stats:
                    hourly_stats[hour] = {"sent": 0, "clicked": 0, "submitted": 0}
                hourly_stats[hour]["sent"] += 1

            if result.clicked_at:
                hour = result.clicked_at.replace(minute=0, second=0, microsecond=0)
                if hour not in hourly_stats:
                    hourly_stats[hour] = {"sent": 0, "clicked": 0, "submitted": 0}
                hourly_stats[hour]["clicked"] += 1

            if result.data_submitted_at:
                hour = result.data_submitted_at.replace(minute=0, second=0, microsecond=0)
                if hour not in hourly_stats:
                    hourly_stats[hour] = {"sent": 0, "clicked": 0, "submitted": 0}
                hourly_stats[hour]["submitted"] += 1

        # Convert to timeline
        for hour, stats in sorted(hourly_stats.items()):
            timeline.append({
                "timestamp": hour,
                "sent": stats["sent"],
                "clicked": stats["clicked"],
                "submitted": stats["submitted"],
            })

        return timeline

    async def end_campaign(self, campaign_id: int) -> PhishingCampaign:
        """End an active phishing campaign."""
        campaign = await self.db.get(PhishingCampaign, campaign_id)
        if not campaign:
            raise ValidationError("Campaign not found")

        if campaign.status != CampaignStatus.ACTIVE:
            raise ValidationError(f"Campaign is not active (status: {campaign.status})")

        campaign.status = CampaignStatus.COMPLETED
        campaign.end_date = datetime.utcnow()

        # Send training emails to users who clicked
        await self._send_training_emails(campaign_id)

        await self.db.commit()
        return campaign

    async def _send_training_emails(self, campaign_id: int) -> None:
        """Send training emails to users who fell for phishing."""
        # Get users who clicked
        stmt = select(PhishingResult).where(
            PhishingResult.campaign_id == campaign_id,
            PhishingResult.clicked_at.isnot(None)
        )
        result = await self.db.execute(stmt)
        clicked_results = result.scalars().all()

        for result in clicked_results:
            try:
                # Send educational email
                await self.email_service.send_tracked_email(
                    user_id=result.user_id,
                    template_code="phishing_education",
                    variables={
                        "campaign_name": campaign.name,
                        "clicked_at": result.clicked_at,
                        "training_link": f"{settings.FRONTEND_URL}/training/phishing-awareness",
                    },
                )
            except Exception as e:
                logger.error(f"Failed to send training email to user {result.user_id}: {str(e)}")

    async def get_user_phishing_history(
        self,
        user_id: int,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get a user's phishing campaign history."""
        stmt = (
            select(PhishingResult)
            .where(PhishingResult.user_id == user_id)
            .options(selectinload(PhishingResult.campaign))
            .order_by(PhishingResult.sent_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        results = result.scalars().all()

        history = []
        for r in results:
            history.append({
                "campaign_id": r.campaign_id,
                "campaign_name": r.campaign.name if r.campaign else "Unknown",
                "sent_at": r.sent_at,
                "clicked": r.clicked_at is not None,
                "data_submitted": r.data_submitted_at is not None,
                "time_to_click": (
                    (r.clicked_at - r.sent_at).total_seconds()
                    if r.clicked_at and r.sent_at else None
                ),
            })

        return history