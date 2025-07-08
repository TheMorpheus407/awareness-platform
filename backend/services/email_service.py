"""Email service for sending emails."""

import os
from typing import Dict, Optional, List
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import logging

from backend.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails."""
    
    def __init__(self):
        """Initialize email service."""
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.smtp_tls = settings.SMTP_TLS
        self.from_email = settings.FROM_EMAIL
        self.from_name = settings.FROM_NAME
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        reply_to: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        attachments: Optional[List[Dict[str, any]]] = None
    ) -> bool:
        """Send an email.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML content of the email
            text_content: Plain text content (optional)
            from_email: Sender email (overrides default)
            from_name: Sender name (overrides default)
            reply_to: Reply-to email address
            headers: Additional email headers
            attachments: List of attachments
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{from_name or self.from_name} <{from_email or self.from_email}>"
            msg['To'] = to_email
            
            if reply_to:
                msg['Reply-To'] = reply_to
            
            # Add custom headers
            if headers:
                for key, value in headers.items():
                    msg[key] = value
            
            # Add text and HTML parts
            if text_content:
                part1 = MIMEText(text_content, 'plain')
                msg.attach(part1)
            
            part2 = MIMEText(html_content, 'html')
            msg.attach(part2)
            
            # Add attachments if any
            if attachments:
                for attachment in attachments:
                    # TODO: Implement attachment handling
                    pass
            
            # Send email
            if settings.ENVIRONMENT == "production":
                # Use actual SMTP in production
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    if self.smtp_tls:
                        server.starttls()
                    if self.smtp_user and self.smtp_password:
                        server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)
            else:
                # In development, just log the email
                logger.info(f"Email (dev mode) - To: {to_email}, Subject: {subject}")
                logger.debug(f"HTML Content: {html_content[:200]}...")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    def send_verification_email(self, to_email: str, verification_link: str) -> bool:
        """Send email verification email."""
        subject = "Verify your email address"
        html_content = f"""
        <html>
            <body>
                <h2>Email Verification</h2>
                <p>Please click the link below to verify your email address:</p>
                <p><a href="{verification_link}">Verify Email</a></p>
                <p>If you didn't request this, please ignore this email.</p>
            </body>
        </html>
        """
        
        return self.send_email(to_email, subject, html_content)
    
    def send_password_reset_email(self, to_email: str, reset_link: str) -> bool:
        """Send password reset email."""
        subject = "Reset your password"
        html_content = f"""
        <html>
            <body>
                <h2>Password Reset</h2>
                <p>You requested a password reset. Click the link below to reset your password:</p>
                <p><a href="{reset_link}">Reset Password</a></p>
                <p>This link will expire in 1 hour.</p>
                <p>If you didn't request this, please ignore this email.</p>
            </body>
        </html>
        """
        
        return self.send_email(to_email, subject, html_content)
    
    def send_welcome_email(self, to_email: str, first_name: str) -> bool:
        """Send welcome email to new user."""
        subject = "Welcome to Awareness Training Platform"
        html_content = f"""
        <html>
            <body>
                <h2>Welcome {first_name}!</h2>
                <p>Thank you for joining our cybersecurity awareness training platform.</p>
                <p>You can now access all our training courses and phishing simulations.</p>
                <p>Get started by logging in to your account.</p>
            </body>
        </html>
        """
        
        return self.send_email(to_email, subject, html_content)
    
    def send_phishing_campaign_notification(
        self,
        to_email: str,
        campaign_name: str,
        total_recipients: int
    ) -> bool:
        """Send notification about phishing campaign launch."""
        subject = f"Phishing Campaign '{campaign_name}' Launched"
        html_content = f"""
        <html>
            <body>
                <h2>Phishing Campaign Started</h2>
                <p>Your phishing campaign '{campaign_name}' has been launched successfully.</p>
                <p>Total recipients: {total_recipients}</p>
                <p>You can monitor the progress in your dashboard.</p>
            </body>
        </html>
        """
        
        return self.send_email(to_email, subject, html_content)