"""Email template service with Jinja2 support."""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import re
import hashlib
import base64
from urllib.parse import urlencode
import uuid

from jinja2 import Environment, Template, TemplateSyntaxError, select_autoescape
from markupsafe import Markup
import premailer
from bs4 import BeautifulSoup

from core.config import settings

logger = logging.getLogger(__name__)


class EmailTemplateEngine:
    """Email template rendering engine with Jinja2."""
    
    def __init__(self):
        self.env = Environment(
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        
        # Add custom filters
        self.env.filters['format_date'] = self._format_date
        self.env.filters['format_currency'] = self._format_currency
        self.env.filters['truncate_words'] = self._truncate_words
        self.env.filters['track_link'] = self._track_link
        
        # Add global variables
        self.env.globals['current_year'] = datetime.utcnow().year
        self.env.globals['app_name'] = settings.APP_NAME
        self.env.globals['app_url'] = settings.FRONTEND_URL
        self.env.globals['support_email'] = settings.SUPPORT_EMAIL or settings.SMTP_FROM_EMAIL or "hallo@bootstrap-awareness.de"
        
    def render_template(
        self,
        html_content: str,
        variables: Dict[str, Any],
        text_content: Optional[str] = None,
        email_log_id: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Render email template with variables.
        
        Args:
            html_content: HTML template content
            variables: Template variables
            text_content: Optional text template
            email_log_id: Optional email log ID for tracking
            
        Returns:
            Dict with rendered html and text content
        """
        try:
            # Add tracking variables if email_log_id provided
            if email_log_id:
                variables['tracking_pixel'] = self._get_tracking_pixel(email_log_id)
                variables['unsubscribe_url'] = self._get_unsubscribe_url(
                    variables.get('user_id'),
                    variables.get('unsubscribe_token')
                )
                # Store email_log_id for link tracking
                self._current_email_log_id = email_log_id
            
            # Render HTML template
            html_template = self.env.from_string(html_content)
            rendered_html = html_template.render(**variables)
            
            # Apply CSS inlining for better email client support
            rendered_html = self._inline_css(rendered_html)
            
            # Add tracking to links if email_log_id provided
            if email_log_id:
                rendered_html = self._add_link_tracking(rendered_html, email_log_id)
            
            # Render text template if provided
            rendered_text = None
            if text_content:
                text_template = self.env.from_string(text_content)
                rendered_text = text_template.render(**variables)
            else:
                # Auto-generate text from HTML
                rendered_text = self._html_to_text(rendered_html)
            
            return {
                'html': rendered_html,
                'text': rendered_text,
            }
            
        except TemplateSyntaxError as e:
            logger.error(f"Template syntax error: {str(e)}")
            raise ValueError(f"Invalid template syntax: {str(e)}")
        except Exception as e:
            logger.error(f"Template rendering error: {str(e)}")
            raise
    
    def _format_date(self, date: datetime, format: str = '%B %d, %Y') -> str:
        """Format date for display."""
        if not date:
            return ''
        return date.strftime(format)
    
    def _format_currency(self, amount: float, currency: str = 'USD') -> str:
        """Format currency for display."""
        if currency == 'USD':
            return f'${amount:,.2f}'
        elif currency == 'EUR':
            return f'€{amount:,.2f}'
        else:
            return f'{currency} {amount:,.2f}'
    
    def _truncate_words(self, text: str, words: int = 50) -> str:
        """Truncate text to specified number of words."""
        word_list = text.split()
        if len(word_list) <= words:
            return text
        return ' '.join(word_list[:words]) + '...'
    
    def _track_link(self, url: str, position: Optional[int] = None) -> str:
        """Create tracked link URL."""
        if not hasattr(self, '_current_email_log_id'):
            return url
            
        # Create tracking URL
        params = {
            'url': url,
            'id': self._current_email_log_id,
        }
        if position is not None:
            params['pos'] = position
            
        track_url = f"{settings.BACKEND_URL}/api/v1/email/track/click?{urlencode(params)}"
        return track_url
    
    def _get_tracking_pixel(self, email_log_id: str) -> Markup:
        """Get email open tracking pixel."""
        track_url = f"{settings.BACKEND_URL}/api/v1/email/track/open/{email_log_id}"
        return Markup(f'<img src="{track_url}" width="1" height="1" style="display:block;" alt="" />')
    
    def _get_unsubscribe_url(self, user_id: Optional[str], token: Optional[str]) -> str:
        """Get unsubscribe URL."""
        if not user_id or not token:
            return f"{settings.FRONTEND_URL}/unsubscribe"
        
        params = {
            'user': user_id,
            'token': token,
        }
        return f"{settings.FRONTEND_URL}/unsubscribe?{urlencode(params)}"
    
    def _inline_css(self, html: str) -> str:
        """Inline CSS for better email client support."""
        try:
            # Use premailer to inline CSS
            return premailer.transform(
                html,
                base_url=settings.FRONTEND_URL,
                preserve_internal_links=True,
                keep_style_tags=True,
                strip_important=False,
            )
        except Exception as e:
            logger.warning(f"Failed to inline CSS: {str(e)}")
            return html
    
    def _add_link_tracking(self, html: str, email_log_id: str) -> str:
        """Add tracking to all links in HTML."""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            position = 0
            
            for link in soup.find_all('a', href=True):
                href = link['href']
                
                # Skip mailto, tel, and anchor links
                if href.startswith(('mailto:', 'tel:', '#')):
                    continue
                
                # Skip unsubscribe links
                if 'unsubscribe' in href.lower():
                    continue
                
                # Create tracked URL
                params = {
                    'url': href,
                    'id': email_log_id,
                    'pos': position,
                }
                track_url = f"{settings.BACKEND_URL}/api/v1/email/track/click?{urlencode(params)}"
                link['href'] = track_url
                
                position += 1
            
            return str(soup)
            
        except Exception as e:
            logger.warning(f"Failed to add link tracking: {str(e)}")
            return html
    
    def _html_to_text(self, html: str) -> str:
        """Convert HTML to plain text."""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style elements
            for element in soup(['script', 'style']):
                element.decompose()
            
            # Get text
            text = soup.get_text()
            
            # Break into lines and remove leading/trailing space
            lines = (line.strip() for line in text.splitlines())
            
            # Break multi-headlines into a line each
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            
            # Drop blank lines
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            return text
            
        except Exception as e:
            logger.warning(f"Failed to convert HTML to text: {str(e)}")
            return ''


class EmailPersonalization:
    """Email personalization service."""
    
    @staticmethod
    def get_default_variables(user: Any, company: Optional[Any] = None) -> Dict[str, Any]:
        """
        Get default personalization variables for a user.
        
        Args:
            user: User object
            company: Optional company object
            
        Returns:
            Dict of template variables
        """
        variables = {
            'user_id': str(user.id),
            'user_name': user.full_name or user.email.split('@')[0],
            'user_email': user.email,
            'user_first_name': user.first_name or user.email.split('@')[0],
            'user_last_name': user.last_name or '',
            'user_role': user.role.value if user.role else 'user',
            'user_created_at': user.created_at,
        }
        
        if company:
            variables.update({
                'company_id': str(company.id),
                'company_name': company.name,
                'company_size': company.size.value if company.size else '',
                'company_industry': company.industry,
                'company_subscription': company.subscription_tier.value if company.subscription_tier else '',
            })
        
        return variables
    
    @staticmethod
    def merge_variables(*variable_dicts: Dict[str, Any]) -> Dict[str, Any]:
        """Merge multiple variable dictionaries."""
        result = {}
        for var_dict in variable_dicts:
            if var_dict:
                result.update(var_dict)
        return result


# Global template engine instance
template_engine = EmailTemplateEngine()