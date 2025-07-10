"""
Basic email service using SMTP/SendGrid for sending emails.
"""

import asyncio
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional, Dict, Any
import logging
from pathlib import Path

from core.config import settings
from core.exceptions import EmailError

logger = logging.getLogger(__name__)


class EmailService:
    """Basic email service for sending emails via SMTP."""

    def __init__(self):
        """Initialize the email service with configuration."""
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.smtp_tls = settings.SMTP_TLS
        self.smtp_ssl = settings.SMTP_SSL
        self.smtp_timeout = settings.SMTP_TIMEOUT
        self.from_name = settings.EMAIL_FROM_NAME
        self.from_email = settings.EMAIL_FROM_EMAIL

    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        reply_to: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> bool:
        """
        Send an email asynchronously.

        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Plain text body
            html_body: Optional HTML body
            attachments: Optional list of attachments
            cc: Optional list of CC recipients
            bcc: Optional list of BCC recipients
            reply_to: Optional reply-to address
            headers: Optional custom headers

        Returns:
            bool: True if email was sent successfully

        Raises:
            EmailError: If email sending fails
        """
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._send_email_sync,
            to_email,
            subject,
            body,
            html_body,
            attachments,
            cc,
            bcc,
            reply_to,
            headers,
        )

    def _send_email_sync(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        reply_to: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> bool:
        """Synchronous email sending implementation."""
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = to_email

            if cc:
                msg["Cc"] = ", ".join(cc)
            if reply_to:
                msg["Reply-To"] = reply_to

            # Add custom headers
            if headers:
                for key, value in headers.items():
                    msg[key] = value

            # Add text parts
            msg.attach(MIMEText(body, "plain"))
            if html_body:
                msg.attach(MIMEText(html_body, "html"))

            # Add attachments
            if attachments:
                for attachment in attachments:
                    self._attach_file(msg, attachment)

            # Prepare recipients
            recipients = [to_email]
            if cc:
                recipients.extend(cc)
            if bcc:
                recipients.extend(bcc)

            # Send email
            if self.smtp_ssl:
                server = smtplib.SMTP_SSL(
                    self.smtp_host, self.smtp_port, timeout=self.smtp_timeout
                )
            else:
                server = smtplib.SMTP(
                    self.smtp_host, self.smtp_port, timeout=self.smtp_timeout
                )
                if self.smtp_tls:
                    server.starttls()

            if self.smtp_user and self.smtp_password:
                server.login(self.smtp_user, self.smtp_password)

            server.send_message(msg, to_addrs=recipients)
            server.quit()

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            raise EmailError(f"Failed to send email: {str(e)}")

    def _attach_file(self, msg: MIMEMultipart, attachment: Dict[str, Any]) -> None:
        """Attach a file to the email message."""
        try:
            # attachment dict should have: filename, content, mimetype
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.get("content", b""))
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f'attachment; filename="{attachment.get("filename", "attachment")}"',
            )
            msg.attach(part)
        except Exception as e:
            logger.error(f"Failed to attach file: {str(e)}")

    async def send_bulk_emails(
        self,
        recipients: List[Dict[str, Any]],
        subject: str,
        body_template: str,
        html_body_template: Optional[str] = None,
        rate_limit: int = 10,  # emails per second
    ) -> Dict[str, List[str]]:
        """
        Send bulk emails with rate limiting.

        Args:
            recipients: List of recipient dicts with email and optional vars
            subject: Email subject (can contain template vars)
            body_template: Body template with {var} placeholders
            html_body_template: Optional HTML body template
            rate_limit: Maximum emails per second

        Returns:
            Dict with 'success' and 'failed' email lists
        """
        results = {"success": [], "failed": []}
        semaphore = asyncio.Semaphore(rate_limit)

        async def send_with_limit(recipient: Dict[str, Any]):
            async with semaphore:
                try:
                    email = recipient["email"]
                    vars = recipient.get("vars", {})

                    # Format subject and body with variables
                    formatted_subject = subject.format(**vars)
                    formatted_body = body_template.format(**vars)
                    formatted_html = None
                    if html_body_template:
                        formatted_html = html_body_template.format(**vars)

                    await self.send_email(
                        email,
                        formatted_subject,
                        formatted_body,
                        formatted_html,
                    )
                    results["success"].append(email)
                except Exception as e:
                    logger.error(f"Failed to send email to {recipient['email']}: {e}")
                    results["failed"].append(recipient["email"])

                # Rate limiting delay
                await asyncio.sleep(1.0 / rate_limit)

        # Send all emails concurrently with rate limiting
        tasks = [send_with_limit(recipient) for recipient in recipients]
        await asyncio.gather(*tasks, return_exceptions=True)

        return results

    async def verify_smtp_connection(self) -> bool:
        """Verify SMTP connection and credentials."""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._verify_smtp_sync)
        except Exception as e:
            logger.error(f"SMTP verification failed: {str(e)}")
            return False

    def _verify_smtp_sync(self) -> bool:
        """Synchronous SMTP verification."""
        try:
            if self.smtp_ssl:
                server = smtplib.SMTP_SSL(
                    self.smtp_host, self.smtp_port, timeout=self.smtp_timeout
                )
            else:
                server = smtplib.SMTP(
                    self.smtp_host, self.smtp_port, timeout=self.smtp_timeout
                )
                if self.smtp_tls:
                    server.starttls()

            if self.smtp_user and self.smtp_password:
                server.login(self.smtp_user, self.smtp_password)

            server.quit()
            return True
        except Exception:
            return False