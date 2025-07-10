"""
Phishing campaign service for managing phishing simulations and training.
"""

import asyncio
import secrets
import hashlib
import json
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
from core.exceptions import ValidationError, AuthorizationError
from core.cache import cache

logger = logging.getLogger(__name__)


class PhishingService:
    """Service for managing phishing campaigns and simulations."""

    def __init__(self, db: AsyncSession, cache=None):
        """Initialize phishing service."""
        self.db = db
        self.cache = cache
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
        formatted_body = body_text.replace('\n', '<br>')
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6;">
            {formatted_body}
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

    async def get_campaign_analytics(self, campaign_id: int) -> Dict[str, Any]:
        """Get detailed analytics for a phishing campaign."""
        campaign = await self.db.get(
            PhishingCampaign,
            campaign_id,
            options=[selectinload(PhishingCampaign.results)]
        )
        if not campaign:
            raise ValidationError("Campaign not found")

        # Get all results with user info
        stmt = select(PhishingResult).where(
            PhishingResult.campaign_id == campaign_id
        ).options(selectinload(PhishingResult.user))
        result = await self.db.execute(stmt)
        results = result.scalars().all()

        # Calculate metrics
        total_targets = len(campaign.target_users)
        emails_sent = len([r for r in results if r.sent_at])
        emails_opened = len([r for r in results if r.email_opened_at])
        links_clicked = len([r for r in results if r.clicked_at])
        data_submitted = len([r for r in results if r.data_submitted_at])
        reported = len([r for r in results if r.reported_at])

        # Calculate rates
        open_rate = (emails_opened / emails_sent * 100) if emails_sent > 0 else 0
        click_rate = (links_clicked / emails_sent * 100) if emails_sent > 0 else 0
        submit_rate = (data_submitted / emails_sent * 100) if emails_sent > 0 else 0
        report_rate = (reported / emails_sent * 100) if emails_sent > 0 else 0

        # Average time to click
        click_times = [
            (r.clicked_at - r.sent_at).total_seconds()
            for r in results
            if r.clicked_at and r.sent_at
        ]
        avg_time_to_click = sum(click_times) / len(click_times) if click_times else None

        # Hourly breakdown
        hourly_breakdown = self._generate_hourly_breakdown(results)

        # Department breakdown
        dept_breakdown = {}
        for result in results:
            if result.user and result.user.department:
                dept = result.user.department
                if dept not in dept_breakdown:
                    dept_breakdown[dept] = {
                        "total": 0,
                        "opened": 0,
                        "clicked": 0,
                        "submitted": 0,
                        "reported": 0
                    }
                dept_breakdown[dept]["total"] += 1
                if result.email_opened_at:
                    dept_breakdown[dept]["opened"] += 1
                if result.clicked_at:
                    dept_breakdown[dept]["clicked"] += 1
                if result.data_submitted_at:
                    dept_breakdown[dept]["submitted"] += 1
                if result.reported_at:
                    dept_breakdown[dept]["reported"] += 1

        # Risk assessment
        high_risk_users = len([
            r for r in results
            if r.data_submitted_at
        ])
        medium_risk_users = len([
            r for r in results
            if r.clicked_at and not r.data_submitted_at
        ])
        low_risk_users = len([
            r for r in results
            if not r.clicked_at
        ])

        risk_assessment = {
            "high_risk": high_risk_users,
            "medium_risk": medium_risk_users,
            "low_risk": low_risk_users,
            "average_risk_score": (
                (high_risk_users * 3 + medium_risk_users * 2 + low_risk_users) / 
                emails_sent
            ) if emails_sent > 0 else 0
        }

        return {
            "campaign_id": campaign_id,
            "campaign_name": campaign.name,
            "status": campaign.status,
            "total_targets": total_targets,
            "emails_sent": emails_sent,
            "emails_opened": emails_opened,
            "links_clicked": links_clicked,
            "data_submitted": data_submitted,
            "reported": reported,
            "open_rate": round(open_rate, 2),
            "click_rate": round(click_rate, 2),
            "submit_rate": round(submit_rate, 2),
            "report_rate": round(report_rate, 2),
            "average_time_to_click": avg_time_to_click,
            "hourly_breakdown": hourly_breakdown,
            "department_breakdown": dept_breakdown,
            "risk_assessment": risk_assessment,
        }

    def _generate_hourly_breakdown(self, results: List[PhishingResult]) -> List[Dict[str, Any]]:
        """Generate hourly breakdown of campaign events."""
        hourly_data = {}
        
        for result in results:
            # Email sent
            if result.sent_at:
                hour = result.sent_at.replace(minute=0, second=0, microsecond=0)
                if hour not in hourly_data:
                    hourly_data[hour] = {
                        "hour": hour,
                        "sent": 0,
                        "opened": 0,
                        "clicked": 0,
                        "submitted": 0,
                        "reported": 0
                    }
                hourly_data[hour]["sent"] += 1
            
            # Email opened
            if result.email_opened_at:
                hour = result.email_opened_at.replace(minute=0, second=0, microsecond=0)
                if hour not in hourly_data:
                    hourly_data[hour] = {
                        "hour": hour,
                        "sent": 0,
                        "opened": 0,
                        "clicked": 0,
                        "submitted": 0,
                        "reported": 0
                    }
                hourly_data[hour]["opened"] += 1
            
            # Link clicked
            if result.clicked_at:
                hour = result.clicked_at.replace(minute=0, second=0, microsecond=0)
                if hour not in hourly_data:
                    hourly_data[hour] = {
                        "hour": hour,
                        "sent": 0,
                        "opened": 0,
                        "clicked": 0,
                        "submitted": 0,
                        "reported": 0
                    }
                hourly_data[hour]["clicked"] += 1
            
            # Data submitted
            if result.data_submitted_at:
                hour = result.data_submitted_at.replace(minute=0, second=0, microsecond=0)
                if hour not in hourly_data:
                    hourly_data[hour] = {
                        "hour": hour,
                        "sent": 0,
                        "opened": 0,
                        "clicked": 0,
                        "submitted": 0,
                        "reported": 0
                    }
                hourly_data[hour]["submitted"] += 1
            
            # Reported
            if result.reported_at:
                hour = result.reported_at.replace(minute=0, second=0, microsecond=0)
                if hour not in hourly_data:
                    hourly_data[hour] = {
                        "hour": hour,
                        "sent": 0,
                        "opened": 0,
                        "clicked": 0,
                        "submitted": 0,
                        "reported": 0
                    }
                hourly_data[hour]["reported"] += 1
        
        # Convert to sorted list
        return sorted(hourly_data.values(), key=lambda x: x["hour"])

    async def generate_landing_page(
        self,
        campaign: PhishingCampaign,
        user_info: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate landing page HTML for phishing campaign."""
        # Get template
        template = await self.db.get(PhishingTemplate, campaign.template_id)
        
        # Use template's landing page if available
        if template and template.landing_page_html:
            html = template.landing_page_html
            
            # Replace placeholders if user info available
            if user_info:
                for key, value in user_info.items():
                    html = html.replace(f"{{{{{key}}}}}", str(value))
            
            return html
        
        # Generate default landing page
        user_name = "User"
        if user_info:
            user_name = f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}".strip()
        
        return f"""
        <!DOCTYPE html>
        <html lang="de">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Phishing Simulation - Awareness Training</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    margin: 0;
                    padding: 0;
                    background-color: #f4f4f4;
                }}
                .container {{
                    max-width: 800px;
                    margin: 50px auto;
                    padding: 20px;
                    background-color: white;
                    border-radius: 10px;
                    box-shadow: 0 0 10px rgba(0,0,0,0.1);
                }}
                .warning {{
                    background-color: #ff5252;
                    color: white;
                    padding: 20px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                    text-align: center;
                }}
                .warning h1 {{
                    margin: 0;
                }}
                .info {{
                    background-color: #e3f2fd;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .red-flags {{
                    background-color: #fff3e0;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .red-flags ul {{
                    margin: 10px 0;
                }}
                .btn {{
                    display: inline-block;
                    background-color: #2196f3;
                    color: white;
                    padding: 10px 20px;
                    text-decoration: none;
                    border-radius: 5px;
                    margin-top: 20px;
                }}
                .btn:hover {{
                    background-color: #1976d2;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="warning">
                    <h1>⚠️ Dies war eine Phishing-Simulation!</h1>
                    <p>Sie haben auf einen simulierten Phishing-Link geklickt.</p>
                </div>
                
                <div class="info">
                    <h2>Was ist passiert?</h2>
                    <p>Hallo {user_name},</p>
                    <p>Sie haben gerade an einer Phishing-Simulation teilgenommen, die von Ihrer IT-Sicherheitsabteilung durchgeführt wurde. 
                    Dies war kein echter Angriff, aber in einem realen Szenario hätten Cyberkriminelle jetzt Zugriff auf Ihre Anmeldedaten oder persönlichen Informationen haben können.</p>
                </div>
                
                <div class="red-flags">
                    <h2>🚩 Warnsignale in dieser E-Mail:</h2>
                    <ul>
                        <li><strong>Dringlichkeit:</strong> Die E-Mail erzeugte künstlichen Zeitdruck</li>
                        <li><strong>Absenderadresse:</strong> Die Domain war nicht offiziell</li>
                        <li><strong>Generische Anrede:</strong> Keine persönliche Ansprache</li>
                        <li><strong>Verdächtige Links:</strong> Der Link führte nicht zur erwarteten Webseite</li>
                        <li><strong>Rechtschreibfehler:</strong> Professionelle E-Mails enthalten selten Fehler</li>
                    </ul>
                </div>
                
                <h2>Was sollten Sie tun?</h2>
                <ul>
                    <li>✅ Überprüfen Sie immer die Absenderadresse sorgfältig</li>
                    <li>✅ Bewegen Sie die Maus über Links, um das Ziel zu sehen (ohne zu klicken)</li>
                    <li>✅ Seien Sie skeptisch bei dringenden Anfragen</li>
                    <li>✅ Melden Sie verdächtige E-Mails an Ihre IT-Abteilung</li>
                    <li>✅ Geben Sie niemals Passwörter über E-Mail-Links ein</li>
                </ul>
                
                <div style="text-align: center;">
                    <a href="/training/phishing-awareness" class="btn">Zum Awareness-Training</a>
                </div>
                
                <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center; color: #666;">
                    <p>Diese Simulation wurde durchgeführt von: {campaign.name}</p>
                    <p>Bei Fragen wenden Sie sich an Ihre IT-Sicherheitsabteilung</p>
                </div>
            </div>
        </body>
        </html>
        """

    async def schedule_campaign(
        self,
        campaign_id: int,
        scheduled_at: datetime,
        batch_size: int = 50,
        interval_minutes: int = 5
    ) -> None:
        """Schedule a phishing campaign for future execution."""
        # Store scheduling info in cache
        schedule_key = f"phishing_schedule:{campaign_id}"
        schedule_data = {
            "campaign_id": campaign_id,
            "scheduled_at": scheduled_at.isoformat(),
            "batch_size": batch_size,
            "interval_minutes": interval_minutes,
            "status": "scheduled"
        }
        
        # Calculate seconds until execution
        seconds_until = (scheduled_at - datetime.utcnow()).total_seconds()
        
        if seconds_until > 0:
            # Store in cache with expiration
            await self.cache.setex(
                schedule_key,
                int(seconds_until + 3600),  # Keep for 1 hour after scheduled time
                json.dumps(schedule_data)
            )
            
            logger.info(
                f"Campaign {campaign_id} scheduled for {scheduled_at} "
                f"(in {seconds_until} seconds)"
            )
        else:
            raise ValidationError("Scheduled time must be in the future")