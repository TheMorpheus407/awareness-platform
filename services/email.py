"""Email service for sending emails."""

import logging
from typing import Dict, List, Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via SMTP."""
    
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.SMTP_FROM_EMAIL
        self.from_name = settings.SMTP_FROM_NAME
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """
        Send an email using SMTP.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML content of the email
            text_content: Plain text content (optional)
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            
            # Add text and HTML parts
            if text_content:
                text_part = MIMEText(text_content, 'plain')
                msg.attach(text_part)
            
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            if self.smtp_host and self.smtp_username and self.smtp_password:
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.smtp_username, self.smtp_password)
                    server.send_message(msg)
                
                logger.info(f"Email sent successfully to {to_email}")
                return True
            else:
                logger.warning("SMTP not configured, email not sent")
                logger.info(f"Would send email to {to_email}: {subject}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False


# Email service instance
email_service = EmailService()


async def send_verification_email(email: str, name: str, verification_url: str) -> bool:
    """
    Send email verification email.
    
    Args:
        email: Recipient email
        name: User's name
        verification_url: URL to verify email
        
    Returns:
        True if sent successfully
    """
    subject = "Verify your email address"
    
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2563eb;">Verify Your Email Address</h2>
                
                <p>Hi {name},</p>
                
                <p>Thank you for registering with the Cybersecurity Awareness Platform. 
                Please click the button below to verify your email address:</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{verification_url}" 
                       style="background-color: #2563eb; color: white; padding: 12px 30px; 
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        Verify Email
                    </a>
                </div>
                
                <p>Or copy and paste this link into your browser:</p>
                <p style="word-break: break-all; color: #2563eb;">
                    {verification_url}
                </p>
                
                <p>If you didn't create an account, you can safely ignore this email.</p>
                
                <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                
                <p style="font-size: 12px; color: #666;">
                    This email was sent by Cybersecurity Awareness Platform. 
                    Please do not reply to this email.
                </p>
            </div>
        </body>
    </html>
    """
    
    text_content = f"""
    Hi {name},
    
    Thank you for registering with the Cybersecurity Awareness Platform.
    Please verify your email address by visiting the following link:
    
    {verification_url}
    
    If you didn't create an account, you can safely ignore this email.
    
    This email was sent by Cybersecurity Awareness Platform.
    """
    
    return await email_service.send_email(
        to_email=email,
        subject=subject,
        html_content=html_content,
        text_content=text_content,
    )


async def send_password_reset_email(email: str, name: str, reset_url: str) -> bool:
    """
    Send password reset email.
    
    Args:
        email: Recipient email
        name: User's name
        reset_url: URL to reset password
        
    Returns:
        True if sent successfully
    """
    subject = "Reset your password"
    
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2563eb;">Reset Your Password</h2>
                
                <p>Hi {name},</p>
                
                <p>We received a request to reset your password. 
                Click the button below to create a new password:</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_url}" 
                       style="background-color: #2563eb; color: white; padding: 12px 30px; 
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        Reset Password
                    </a>
                </div>
                
                <p>Or copy and paste this link into your browser:</p>
                <p style="word-break: break-all; color: #2563eb;">
                    {reset_url}
                </p>
                
                <p style="color: #dc2626;">
                    This link will expire in 1 hour for security reasons.
                </p>
                
                <p>If you didn't request a password reset, please ignore this email. 
                Your password will remain unchanged.</p>
                
                <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                
                <p style="font-size: 12px; color: #666;">
                    This email was sent by Cybersecurity Awareness Platform. 
                    Please do not reply to this email.
                </p>
            </div>
        </body>
    </html>
    """
    
    text_content = f"""
    Hi {name},
    
    We received a request to reset your password.
    Visit the following link to create a new password:
    
    {reset_url}
    
    This link will expire in 1 hour for security reasons.
    
    If you didn't request a password reset, please ignore this email.
    Your password will remain unchanged.
    
    This email was sent by Cybersecurity Awareness Platform.
    """
    
    return await email_service.send_email(
        to_email=email,
        subject=subject,
        html_content=html_content,
        text_content=text_content,
    )