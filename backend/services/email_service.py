"""
Extended email service with additional features like tracking, analytics, and templates.
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from services.email import EmailService
from services.email_template import EmailTemplateService
from models import EmailLog, EmailStatus, EmailEvent, User, EmailBounce
from core.cache import cache
from core.exceptions import EmailError

logger = logging.getLogger(__name__)


class ExtendedEmailService(EmailService):
    """Extended email service with tracking, analytics, and database integration."""

    def __init__(self, db: AsyncSession, cache=None):
        """Initialize extended email service."""
        super().__init__()
        self.db = db
        self.cache = cache
        self.template_service = EmailTemplateService(db)

    async def send_tracked_email(
        self,
        user_id: int,
        template_id: Optional[int] = None,
        template_code: Optional[str] = None,
        subject: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        campaign_id: Optional[int] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        track_opens: bool = True,
        track_clicks: bool = True,
    ) -> EmailLog:
        """
        Send an email with tracking capabilities.

        Args:
            user_id: ID of the recipient user
            template_id: Optional template ID
            template_code: Optional template code (alternative to ID)
            subject: Optional custom subject (overrides template)
            variables: Template variables
            campaign_id: Optional campaign ID for grouping
            attachments: Optional attachments
            track_opens: Whether to track email opens
            track_clicks: Whether to track link clicks

        Returns:
            EmailLog: The created email log entry
        """
        # Get user
        user = await self.db.get(User, user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Generate tracking ID
        tracking_id = str(uuid.uuid4())

        # Prepare email content
        if template_id or template_code:
            # Use template
            content = await self.template_service.render_template(
                template_id=template_id,
                template_code=template_code,
                variables={
                    **(variables or {}),
                    "user": user,
                    "tracking_id": tracking_id if track_opens else None,
                }
            )
            email_subject = subject or content["subject"]
            body = content["body_text"]
            html_body = content["body_html"]
        else:
            # Direct content
            email_subject = subject or "No Subject"
            body = variables.get("body_text", "")
            html_body = variables.get("body_html", None)

        # Add tracking pixel if enabled
        if track_opens and html_body:
            pixel_url = f"{settings.FRONTEND_URL}/api/v1/email/track/open/{tracking_id}"
            tracking_pixel = f'<img src="{pixel_url}" width="1" height="1" style="display:none;" />'
            html_body = html_body.replace("</body>", f"{tracking_pixel}</body>")

        # Replace links with tracking links if enabled
        if track_clicks and html_body:
            html_body = await self._replace_links_with_tracking(html_body, tracking_id)

        # Create email log entry
        email_log = EmailLog(
            user_id=user_id,
            recipient_email=user.email,
            subject=email_subject,
            template_id=template_id,
            campaign_id=campaign_id,
            tracking_id=tracking_id,
            status=EmailStatus.PENDING,
            variables=variables,
            track_opens=track_opens,
            track_clicks=track_clicks,
        )
        self.db.add(email_log)
        await self.db.flush()

        try:
            # Send email
            success = await self.send_email(
                to_email=user.email,
                subject=email_subject,
                body=body,
                html_body=html_body,
                attachments=attachments,
                headers={
                    "X-Email-ID": str(email_log.id),
                    "X-Tracking-ID": tracking_id,
                }
            )

            if success:
                email_log.status = EmailStatus.SENT
                email_log.sent_at = datetime.utcnow()
            else:
                email_log.status = EmailStatus.FAILED

        except Exception as e:
            email_log.status = EmailStatus.FAILED
            email_log.error_message = str(e)
            logger.error(f"Failed to send tracked email to {user.email}: {e}")
            raise

        await self.db.commit()
        return email_log

    async def _replace_links_with_tracking(
        self, html_content: str, tracking_id: str
    ) -> str:
        """Replace links in HTML with tracking links."""
        import re
        from urllib.parse import quote

        def replace_link(match):
            url = match.group(1)
            # Skip mailto and tel links
            if url.startswith(("mailto:", "tel:", "#")):
                return match.group(0)
            # Create tracking URL
            tracking_url = f"{settings.FRONTEND_URL}/api/v1/email/track/click/{tracking_id}?url={quote(url)}"
            return f'href="{tracking_url}"'

        # Replace all href attributes
        pattern = r'href="([^"]+)"'
        return re.sub(pattern, replace_link, html_content)

    async def track_event(
        self,
        tracking_id: str,
        event_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Track an email event (open, click, etc.)."""
        # Find email log by tracking ID
        stmt = select(EmailLog).where(EmailLog.tracking_id == tracking_id)
        result = await self.db.execute(stmt)
        email_log = result.scalar_one_or_none()

        if not email_log:
            logger.warning(f"Email log not found for tracking ID: {tracking_id}")
            return

        # Create event record
        event = EmailEvent(
            email_log_id=email_log.id,
            event_type=event_type,
            metadata=metadata or {},
        )
        self.db.add(event)

        # Update email log status based on event
        if event_type == "open" and email_log.status == EmailStatus.SENT:
            email_log.status = EmailStatus.OPENED
            email_log.opened_at = datetime.utcnow()
        elif event_type == "click":
            email_log.clicked_at = datetime.utcnow()

        # Cache recent event to prevent duplicate tracking
        cache_key = f"email_event:{tracking_id}:{event_type}"
        await self.cache.setex(cache_key, 300, "1")  # 5 minutes TTL

        await self.db.commit()

    async def handle_bounce(
        self,
        email: str,
        bounce_type: str,
        bounce_subtype: Optional[str] = None,
        diagnostic_code: Optional[str] = None,
    ) -> None:
        """Handle email bounce notifications."""
        # Create bounce record
        bounce = EmailBounce(
            email=email,
            bounce_type=bounce_type,
            bounce_subtype=bounce_subtype,
            diagnostic_code=diagnostic_code,
        )
        self.db.add(bounce)

        # Update user if permanent bounce
        if bounce_type == "permanent":
            stmt = update(User).where(User.email == email).values(
                email_deliverable=False,
                email_bounce_count=User.email_bounce_count + 1,
            )
            await self.db.execute(stmt)

        # Update recent email logs
        cutoff = datetime.utcnow() - timedelta(hours=24)
        stmt = (
            update(EmailLog)
            .where(
                EmailLog.recipient_email == email,
                EmailLog.sent_at >= cutoff,
                EmailLog.status.in_([EmailStatus.SENT, EmailStatus.OPENED])
            )
            .values(
                status=EmailStatus.BOUNCED,
                error_message=diagnostic_code,
            )
        )
        await self.db.execute(stmt)

        await self.db.commit()

    async def get_email_stats(
        self,
        user_id: Optional[int] = None,
        campaign_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get email statistics."""
        # Build query
        query = select(EmailLog)
        
        if user_id:
            query = query.where(EmailLog.user_id == user_id)
        if campaign_id:
            query = query.where(EmailLog.campaign_id == campaign_id)
        if start_date:
            query = query.where(EmailLog.created_at >= start_date)
        if end_date:
            query = query.where(EmailLog.created_at <= end_date)

        result = await self.db.execute(query)
        logs = result.scalars().all()

        # Calculate statistics
        total = len(logs)
        sent = sum(1 for log in logs if log.status != EmailStatus.PENDING)
        delivered = sum(1 for log in logs if log.status in [
            EmailStatus.SENT, EmailStatus.OPENED, EmailStatus.CLICKED
        ])
        opened = sum(1 for log in logs if log.opened_at is not None)
        clicked = sum(1 for log in logs if log.clicked_at is not None)
        bounced = sum(1 for log in logs if log.status == EmailStatus.BOUNCED)
        failed = sum(1 for log in logs if log.status == EmailStatus.FAILED)

        return {
            "total": total,
            "sent": sent,
            "delivered": delivered,
            "opened": opened,
            "clicked": clicked,
            "bounced": bounced,
            "failed": failed,
            "delivery_rate": (delivered / sent * 100) if sent > 0 else 0,
            "open_rate": (opened / delivered * 100) if delivered > 0 else 0,
            "click_rate": (clicked / delivered * 100) if delivered > 0 else 0,
            "bounce_rate": (bounced / sent * 100) if sent > 0 else 0,
        }

    async def cleanup_old_logs(self, days: int = 90) -> int:
        """Clean up old email logs."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        # Delete old events first (foreign key constraint)
        stmt = select(EmailEvent).join(EmailLog).where(EmailLog.created_at < cutoff)
        result = await self.db.execute(stmt)
        events = result.scalars().all()
        for event in events:
            await self.db.delete(event)

        # Delete old logs
        stmt = select(EmailLog).where(EmailLog.created_at < cutoff)
        result = await self.db.execute(stmt)
        logs = result.scalars().all()
        count = len(logs)
        for log in logs:
            await self.db.delete(log)

        await self.db.commit()
        return count