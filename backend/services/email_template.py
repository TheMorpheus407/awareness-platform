"""
Email template service for managing and rendering email templates with Jinja2.
"""

import os
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, Template, select_autoescape
from premailer import Premailer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models import EmailTemplate, EmailTemplateType, Company, User
from core.config import settings
from core.cache import get_cache

logger = logging.getLogger(__name__)


class EmailTemplateService:
    """Service for managing and rendering email templates."""

    def __init__(self, db: AsyncSession, cache=None):
        """Initialize template service."""
        self.db = db
        self.cache = cache or get_cache()
        
        # Set up Jinja2 environment
        template_dir = Path(__file__).parent.parent / "templates" / "email"
        if not template_dir.exists():
            template_dir.mkdir(parents=True, exist_ok=True)
            
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(['html', 'xml']),
            enable_async=True
        )
        
        # Add custom filters
        self.env.filters['datetime'] = self._format_datetime
        self.env.filters['currency'] = self._format_currency
        
        # Default template variables
        self.default_vars = {
            "app_name": settings.APP_NAME,
            "frontend_url": str(settings.FRONTEND_URL),
            "support_email": settings.EMAIL_FROM_EMAIL,
            "current_year": datetime.utcnow().year,
        }

    def _format_datetime(self, dt: datetime, format: str = "%B %d, %Y") -> str:
        """Format datetime for templates."""
        if not dt:
            return ""
        return dt.strftime(format)

    def _format_currency(self, amount: float, currency: str = "EUR") -> str:
        """Format currency for templates."""
        symbols = {"EUR": "€", "USD": "$", "GBP": "£"}
        symbol = symbols.get(currency, currency)
        return f"{symbol}{amount:,.2f}"

    async def get_template(
        self,
        template_id: Optional[int] = None,
        template_code: Optional[str] = None,
        company_id: Optional[int] = None,
    ) -> Optional[EmailTemplate]:
        """Get email template by ID or code."""
        query = select(EmailTemplate).where(EmailTemplate.is_active == True)
        
        if template_id:
            query = query.where(EmailTemplate.id == template_id)
        elif template_code:
            query = query.where(EmailTemplate.code == template_code)
        else:
            raise ValueError("Either template_id or template_code must be provided")
            
        if company_id:
            query = query.where(
                (EmailTemplate.company_id == company_id) |
                (EmailTemplate.company_id.is_(None))  # Global templates
            )
            
        result = await self.db.execute(query.order_by(EmailTemplate.company_id.desc()))
        return result.scalar_one_or_none()

    async def render_template(
        self,
        template_id: Optional[int] = None,
        template_code: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        company_id: Optional[int] = None,
    ) -> Dict[str, str]:
        """
        Render an email template with variables.

        Returns:
            Dict with 'subject', 'body_text', and 'body_html' keys
        """
        # Get template
        template = await self.get_template(template_id, template_code, company_id)
        if not template:
            raise ValueError("Template not found")

        # Merge variables
        context = {
            **self.default_vars,
            **(template.default_variables or {}),
            **(variables or {})
        }

        # Add company context if available
        if company_id or (variables and "user" in variables):
            company_id = company_id or variables["user"].company_id
            if company_id:
                company = await self.db.get(Company, company_id)
                if company:
                    context["company"] = company

        # Render templates
        try:
            # Render subject
            subject_template = Template(template.subject)
            subject = await subject_template.render_async(**context)

            # Render body text
            body_text_template = Template(template.body_text)
            body_text = await body_text_template.render_async(**context)

            # Render HTML body if available
            body_html = None
            if template.body_html:
                body_html_template = Template(template.body_html)
                body_html = await body_html_template.render_async(**context)
                
                # Apply CSS inlining for better email client compatibility
                if body_html:
                    body_html = self._inline_css(body_html)

            return {
                "subject": subject,
                "body_text": body_text,
                "body_html": body_html,
            }

        except Exception as e:
            logger.error(f"Failed to render template {template.code}: {str(e)}")
            raise

    def _inline_css(self, html: str) -> str:
        """Inline CSS styles for email compatibility."""
        try:
            premailer = Premailer(
                html,
                keep_style_tags=True,
                include_star_selectors=True,
                strip_classes=False,
            )
            return premailer.transform()
        except Exception as e:
            logger.warning(f"Failed to inline CSS: {str(e)}")
            return html

    async def create_template(
        self,
        code: str,
        name: str,
        template_type: EmailTemplateType,
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
        company_id: Optional[int] = None,
        default_variables: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
    ) -> EmailTemplate:
        """Create a new email template."""
        # Check if template code already exists
        existing = await self.get_template(template_code=code, company_id=company_id)
        if existing:
            raise ValueError(f"Template with code '{code}' already exists")

        template = EmailTemplate(
            code=code,
            name=name,
            template_type=template_type,
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            company_id=company_id,
            default_variables=default_variables,
            description=description,
        )
        
        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)
        
        # Clear cache
        await self._clear_template_cache(code, company_id)
        
        return template

    async def update_template(
        self,
        template_id: int,
        **kwargs
    ) -> EmailTemplate:
        """Update an existing template."""
        template = await self.db.get(EmailTemplate, template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")

        # Update fields
        for key, value in kwargs.items():
            if hasattr(template, key):
                setattr(template, key, value)

        template.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(template)
        
        # Clear cache
        await self._clear_template_cache(template.code, template.company_id)
        
        return template

    async def _clear_template_cache(self, code: str, company_id: Optional[int]):
        """Clear template cache."""
        cache_keys = [
            f"email_template:{code}",
            f"email_template:{code}:{company_id}",
        ]
        for key in cache_keys:
            await self.cache.delete(key)

    async def create_default_templates(self, company_id: Optional[int] = None):
        """Create default email templates."""
        default_templates = [
            {
                "code": "welcome",
                "name": "Welcome Email",
                "template_type": EmailTemplateType.TRANSACTIONAL,
                "subject": "Welcome to {{ app_name }}!",
                "body_text": """Hello {{ user.first_name }},

Welcome to {{ app_name }}! We're excited to have you on board.

To get started, please verify your email address by clicking the link below:
{{ verification_link }}

If you have any questions, feel free to reach out to our support team.

Best regards,
The {{ app_name }} Team""",
                "body_html": """<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #4CAF50; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; background-color: #f9f9f9; }
        .button { display: inline-block; padding: 10px 20px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 5px; }
        .footer { padding: 20px; text-align: center; font-size: 12px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Welcome to {{ app_name }}!</h1>
        </div>
        <div class="content">
            <p>Hello {{ user.first_name }},</p>
            <p>Welcome to {{ app_name }}! We're excited to have you on board.</p>
            <p>To get started, please verify your email address:</p>
            <p style="text-align: center;">
                <a href="{{ verification_link }}" class="button">Verify Email</a>
            </p>
            <p>If you have any questions, feel free to reach out to our support team.</p>
        </div>
        <div class="footer">
            <p>&copy; {{ current_year }} {{ app_name }}. All rights reserved.</p>
        </div>
    </div>
</body>
</html>""",
            },
            {
                "code": "password_reset",
                "name": "Password Reset",
                "template_type": EmailTemplateType.TRANSACTIONAL,
                "subject": "Reset Your Password",
                "body_text": """Hello {{ user.first_name }},

We received a request to reset your password. Click the link below to create a new password:
{{ reset_link }}

This link will expire in {{ expiry_hours }} hours.

If you didn't request this, please ignore this email.

Best regards,
The {{ app_name }} Team""",
            },
            {
                "code": "course_completed",
                "name": "Course Completion",
                "template_type": EmailTemplateType.TRANSACTIONAL,
                "subject": "Congratulations! You've completed {{ course.title }}",
                "body_text": """Hello {{ user.first_name }},

Congratulations on completing the course "{{ course.title }}"!

Your score: {{ score }}%
Completion date: {{ completion_date|datetime }}

You can download your certificate here: {{ certificate_link }}

Keep up the great work!

Best regards,
The {{ app_name }} Team""",
            },
            {
                "code": "phishing_campaign_start",
                "name": "Phishing Campaign Start",
                "template_type": EmailTemplateType.MARKETING,
                "subject": "Security Training Campaign Starting Soon",
                "body_text": """Hello {{ user.first_name }},

A new security awareness campaign is starting in your organization.

Campaign: {{ campaign.name }}
Start date: {{ campaign.start_date|datetime }}
Duration: {{ campaign.duration_days }} days

This campaign will help improve your ability to identify and respond to security threats.

Best regards,
The {{ app_name }} Team""",
            },
            {
                "code": "monthly_report",
                "name": "Monthly Security Report",
                "template_type": EmailTemplateType.MARKETING,
                "subject": "Your Monthly Security Report - {{ month }} {{ year }}",
                "body_text": """Hello {{ user.first_name }},

Here's your security awareness report for {{ month }} {{ year }}:

Courses completed: {{ courses_completed }}
Phishing simulations: {{ phishing_attempts }} ({{ phishing_success_rate }}% success rate)
Overall security score: {{ security_score }}/100

{{ recommendations }}

Best regards,
The {{ app_name }} Team""",
            },
        ]

        created_templates = []
        for template_data in default_templates:
            try:
                template = await self.create_template(
                    company_id=company_id,
                    **template_data
                )
                created_templates.append(template)
            except ValueError:
                # Template already exists
                pass

        return created_templates

    async def preview_template(
        self,
        template_id: int,
        sample_variables: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, str]:
        """Preview a template with sample data."""
        # Create sample data if not provided
        if not sample_variables:
            sample_variables = {
                "user": {
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "john.doe@example.com",
                },
                "verification_link": f"{settings.FRONTEND_URL}/verify-email?token=sample",
                "reset_link": f"{settings.FRONTEND_URL}/reset-password?token=sample",
                "course": {
                    "title": "Introduction to Cybersecurity",
                },
                "score": 95,
                "completion_date": datetime.utcnow(),
                "certificate_link": f"{settings.FRONTEND_URL}/certificates/sample",
                "campaign": {
                    "name": "Q4 Security Awareness",
                    "start_date": datetime.utcnow(),
                    "duration_days": 30,
                },
                "month": datetime.utcnow().strftime("%B"),
                "year": datetime.utcnow().year,
                "courses_completed": 3,
                "phishing_attempts": 5,
                "phishing_success_rate": 80,
                "security_score": 85,
                "recommendations": "Keep up the good work! Consider taking the Advanced Phishing Detection course.",
            }

        return await self.render_template(
            template_id=template_id,
            variables=sample_variables
        )