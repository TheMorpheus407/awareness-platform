"""Seed default email templates."""

import sys
from pathlib import Path

# Add backend directory to path
sys.path.append(str(Path(__file__).parent.parent))

from datetime import datetime
from sqlalchemy.orm import Session

from core.db import SessionLocal, engine
from models.email_campaign import EmailTemplate, EmailTemplateType


def create_default_templates(db: Session):
    """Create default email templates."""
    
    templates = [
        {
            "name": "Welcome Email",
            "slug": "welcome-email",
            "type": EmailTemplateType.WELCOME,
            "subject": "Welcome to {{ app_name }}!",
            "preview_text": "Get started with your cybersecurity training",
            "html_content": """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #2563eb; color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
        .content { background-color: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; }
        .button { display: inline-block; padding: 12px 30px; background-color: #2563eb; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }
        .footer { text-align: center; margin-top: 30px; font-size: 12px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Welcome to {{ app_name }}!</h1>
        </div>
        <div class="content">
            <h2>Hi {{ user_first_name }},</h2>
            
            <p>Thank you for joining {{ app_name }}! We're excited to help you strengthen your cybersecurity skills and protect yourself and your organization from digital threats.</p>
            
            <p><strong>Here's what you can do next:</strong></p>
            <ul>
                <li>Complete your profile to personalize your learning experience</li>
                <li>Take our placement assessment to find the right courses for you</li>
                <li>Browse our course catalog and start learning</li>
                <li>Join our community forums to connect with other learners</li>
            </ul>
            
            <center>
                <a href="{{ app_url }}/dashboard" class="button">Go to Dashboard</a>
            </center>
            
            <p>If you have any questions, our support team is here to help at <a href="mailto:{{ support_email }}">{{ support_email }}</a>.</p>
            
            <p>Best regards,<br>The {{ app_name }} Team</p>
        </div>
        <div class="footer">
            <p>© {{ current_year }} {{ app_name }}. All rights reserved.</p>
            <p><a href="{{ unsubscribe_url }}">Unsubscribe</a> | <a href="{{ app_url }}/privacy">Privacy Policy</a></p>
        </div>
    </div>
    {{ tracking_pixel }}
</body>
</html>
            """,
            "text_content": """
Welcome to {{ app_name }}!

Hi {{ user_first_name }},

Thank you for joining {{ app_name }}! We're excited to help you strengthen your cybersecurity skills and protect yourself and your organization from digital threats.

Here's what you can do next:
- Complete your profile to personalize your learning experience
- Take our placement assessment to find the right courses for you
- Browse our course catalog and start learning
- Join our community forums to connect with other learners

Go to Dashboard: {{ app_url }}/dashboard

If you have any questions, our support team is here to help at {{ support_email }}.

Best regards,
The {{ app_name }} Team

© {{ current_year }} {{ app_name }}. All rights reserved.
Unsubscribe: {{ unsubscribe_url }}
            """,
            "variables": {
                "user_first_name": "User's first name",
                "app_name": "Application name",
                "app_url": "Application URL",
                "support_email": "Support email address",
                "unsubscribe_url": "Unsubscribe URL"
            }
        },
        {
            "name": "Course Update Notification",
            "slug": "course-update",
            "type": EmailTemplateType.COURSE_UPDATE,
            "subject": "New Course Available: {{ course_title }}",
            "preview_text": "Check out our latest cybersecurity course",
            "html_content": """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #10b981; color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
        .content { background-color: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; }
        .course-card { background: white; padding: 20px; border-radius: 8px; margin: 20px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .button { display: inline-block; padding: 12px 30px; background-color: #10b981; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }
        .footer { text-align: center; margin-top: 30px; font-size: 12px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>New Course Available!</h1>
        </div>
        <div class="content">
            <h2>Hi {{ user_first_name }},</h2>
            
            <p>We're excited to announce a new course that we think you'll love:</p>
            
            <div class="course-card">
                <h3>{{ course_title }}</h3>
                <p><strong>Difficulty:</strong> {{ course_difficulty }}</p>
                <p><strong>Duration:</strong> {{ course_duration }}</p>
                <p>{{ course_description }}</p>
                
                <center>
                    <a href="{{ course_url }}" class="button">Start Learning</a>
                </center>
            </div>
            
            <p><strong>What you'll learn:</strong></p>
            <ul>
                {{ course_objectives }}
            </ul>
            
            <p>Don't miss out on this opportunity to enhance your cybersecurity skills!</p>
            
            <p>Happy learning,<br>The {{ app_name }} Team</p>
        </div>
        <div class="footer">
            <p>© {{ current_year }} {{ app_name }}. All rights reserved.</p>
            <p><a href="{{ unsubscribe_url }}">Unsubscribe</a> | <a href="{{ app_url }}/email-preferences">Email Preferences</a></p>
        </div>
    </div>
    {{ tracking_pixel }}
</body>
</html>
            """,
            "variables": {
                "course_title": "Course title",
                "course_description": "Course description",
                "course_difficulty": "Course difficulty level",
                "course_duration": "Course duration",
                "course_objectives": "Course learning objectives",
                "course_url": "Course URL"
            }
        },
        {
            "name": "Security Alert",
            "slug": "security-alert",
            "type": EmailTemplateType.SECURITY_ALERT,
            "subject": "Security Alert: {{ alert_type }}",
            "preview_text": "Important security notification for your account",
            "html_content": """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #dc2626; color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
        .content { background-color: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; }
        .alert-box { background: #fee2e2; border: 1px solid #dc2626; padding: 20px; border-radius: 8px; margin: 20px 0; }
        .button { display: inline-block; padding: 12px 30px; background-color: #dc2626; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }
        .footer { text-align: center; margin-top: 30px; font-size: 12px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Security Alert</h1>
        </div>
        <div class="content">
            <h2>Hi {{ user_first_name }},</h2>
            
            <div class="alert-box">
                <h3>{{ alert_type }}</h3>
                <p>{{ alert_description }}</p>
                <p><strong>Date:</strong> {{ alert_date }}</p>
                <p><strong>Location:</strong> {{ alert_location }}</p>
            </div>
            
            <p><strong>What should you do?</strong></p>
            <ul>
                {{ recommended_actions }}
            </ul>
            
            <center>
                <a href="{{ action_url }}" class="button">{{ action_button_text }}</a>
            </center>
            
            <p>If you didn't perform this action or have any concerns, please contact our security team immediately at <a href="mailto:security@{{ app_name }}.com">security@{{ app_name }}.com</a>.</p>
            
            <p>Stay safe,<br>The {{ app_name }} Security Team</p>
        </div>
        <div class="footer">
            <p>© {{ current_year }} {{ app_name }}. All rights reserved.</p>
            <p>This is a security notification and cannot be unsubscribed from.</p>
        </div>
    </div>
    {{ tracking_pixel }}
</body>
</html>
            """,
            "variables": {
                "alert_type": "Type of security alert",
                "alert_description": "Description of the security event",
                "alert_date": "Date and time of the event",
                "alert_location": "Location/IP of the event",
                "recommended_actions": "Recommended security actions",
                "action_url": "URL for primary action",
                "action_button_text": "Text for action button"
            }
        },
        {
            "name": "Phishing Simulation Result",
            "slug": "phishing-result",
            "type": EmailTemplateType.PHISHING_ALERT,
            "subject": "Phishing Simulation: {{ result }}",
            "preview_text": "Learn from your phishing simulation experience",
            "html_content": """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #f59e0b; color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
        .content { background-color: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; }
        .result-box { padding: 20px; border-radius: 8px; margin: 20px 0; }
        .result-passed { background: #d1fae5; border: 1px solid #10b981; }
        .result-failed { background: #fee2e2; border: 1px solid #dc2626; }
        .tips { background: white; padding: 20px; border-radius: 8px; margin: 20px 0; }
        .button { display: inline-block; padding: 12px 30px; background-color: #f59e0b; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }
        .footer { text-align: center; margin-top: 30px; font-size: 12px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Phishing Simulation Results</h1>
        </div>
        <div class="content">
            <h2>Hi {{ user_first_name }},</h2>
            
            <div class="result-box {% if result == 'Passed' %}result-passed{% else %}result-failed{% endif %}">
                <h3>You {{ result }} the phishing simulation</h3>
                <p>{{ result_description }}</p>
            </div>
            
            <div class="tips">
                <h3>How to Spot Phishing Emails:</h3>
                <ul>
                    <li>Check the sender's email address carefully</li>
                    <li>Look for spelling and grammar mistakes</li>
                    <li>Be suspicious of urgent or threatening language</li>
                    <li>Hover over links to see where they really go</li>
                    <li>Never enter passwords after clicking email links</li>
                </ul>
            </div>
            
            <p>Want to improve your phishing detection skills?</p>
            
            <center>
                <a href="{{ training_url }}" class="button">Take Anti-Phishing Course</a>
            </center>
            
            <p>Remember: When in doubt, don't click!</p>
            
            <p>Stay vigilant,<br>The {{ app_name }} Security Team</p>
        </div>
        <div class="footer">
            <p>© {{ current_year }} {{ app_name }}. All rights reserved.</p>
            <p><a href="{{ unsubscribe_url }}">Unsubscribe</a> | <a href="{{ app_url }}/email-preferences">Email Preferences</a></p>
        </div>
    </div>
    {{ tracking_pixel }}
</body>
</html>
            """,
            "variables": {
                "result": "Passed or Failed",
                "result_description": "Description of what happened",
                "training_url": "URL to anti-phishing training"
            }
        },
        {
            "name": "Weekly Digest",
            "slug": "digest-email",
            "type": EmailTemplateType.NEWSLETTER,
            "subject": "Your Weekly {{ app_name }} Digest",
            "preview_text": "Your personalized learning summary",
            "html_content": """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #6366f1; color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
        .content { background-color: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; }
        .section { background: white; padding: 20px; border-radius: 8px; margin: 20px 0; }
        .stat { display: inline-block; text-align: center; margin: 10px; }
        .stat-number { font-size: 24px; font-weight: bold; color: #6366f1; }
        .button { display: inline-block; padding: 12px 30px; background-color: #6366f1; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }
        .footer { text-align: center; margin-top: 30px; font-size: 12px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Your Weekly Learning Digest</h1>
        </div>
        <div class="content">
            <h2>Hi {{ user_first_name }},</h2>
            
            <p>Here's your personalized summary for the week:</p>
            
            {% if course_progress %}
            <div class="section">
                <h3>📚 Course Progress</h3>
                {% for course in course_progress %}
                <p>• <strong>{{ course.course_title }}</strong>: {{ course.progress }}% complete</p>
                {% endfor %}
            </div>
            {% endif %}
            
            {% if new_courses %}
            <div class="section">
                <h3>🆕 New Courses Available</h3>
                {% for course in new_courses %}
                <p>• <a href="{{ app_url }}/courses/{{ course.id }}">{{ course.title }}</a> - {{ course.difficulty }}</p>
                {% endfor %}
            </div>
            {% endif %}
            
            {% if security_alerts %}
            <div class="section">
                <h3>🔒 Security Summary</h3>
                <p>Phishing simulations blocked: <span class="stat-number">{{ security_alerts.phishing_attempts }}</span></p>
            </div>
            {% endif %}
            
            <center>
                <a href="{{ app_url }}/dashboard" class="button">Continue Learning</a>
            </center>
            
            <p>Keep up the great work!</p>
            
            <p>Best regards,<br>The {{ app_name }} Team</p>
        </div>
        <div class="footer">
            <p>© {{ current_year }} {{ app_name }}. All rights reserved.</p>
            <p><a href="{{ unsubscribe_url }}">Unsubscribe</a> | <a href="{{ app_url }}/email-preferences">Update Preferences</a></p>
        </div>
    </div>
    {{ tracking_pixel }}
</body>
</html>
            """,
            "variables": {
                "course_progress": "List of courses with progress",
                "new_courses": "List of new available courses",
                "security_alerts": "Security summary data"
            }
        }
    ]
    
    for template_data in templates:
        # Check if template already exists
        existing = db.query(EmailTemplate).filter(
            EmailTemplate.slug == template_data["slug"]
        ).first()
        
        if not existing:
            template = EmailTemplate(**template_data)
            db.add(template)
            print(f"Created template: {template_data['name']}")
        else:
            print(f"Template already exists: {template_data['name']}")
    
    db.commit()
    print("Email templates seeded successfully!")


def main():
    """Main function."""
    db = SessionLocal()
    try:
        create_default_templates(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()