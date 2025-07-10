"""Add missing database indexes for performance optimization

Revision ID: b72af625ddb5
Revises: 007_add_email_campaign_tables
Create Date: 2025-07-10 16:51:55.971078+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b72af625ddb5'
down_revision: Union[str, None] = '007_add_email_campaign_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add indexes for User model
    op.create_index('idx_users_email_verified', 'users', ['email_verified'])
    op.create_index('idx_users_last_login_at', 'users', ['last_login_at'])
    op.create_index('idx_users_company_role', 'users', ['company_id', 'role'])
    op.create_index('idx_users_is_active_deleted', 'users', ['is_active', 'deleted_at'])
    
    # Add indexes for Company model
    op.create_index('idx_companies_status', 'companies', ['status'])
    op.create_index('idx_companies_subscription_tier', 'companies', ['subscription_tier'])
    op.create_index('idx_companies_status_deleted', 'companies', ['status', 'deleted_at'])
    
    # Add indexes for Course model
    op.create_index('idx_courses_status', 'courses', ['status'])
    op.create_index('idx_courses_published_at', 'courses', ['published_at'])
    op.create_index('idx_courses_category_status', 'courses', ['category', 'status'])
    op.create_index('idx_courses_is_free', 'courses', ['is_free'])
    
    # Add indexes for CourseEnrollment model (optimize N+1 queries)
    op.create_index('idx_course_enrollments_user_status', 'course_enrollments', ['user_id', 'status'])
    op.create_index('idx_course_enrollments_course_status', 'course_enrollments', ['course_id', 'status'])
    op.create_index('idx_course_enrollments_company_status', 'course_enrollments', ['company_id', 'status'])
    op.create_index('idx_course_enrollments_completed_at', 'course_enrollments', ['completed_at'])
    
    # Add indexes for Module and Lesson models
    op.create_index('idx_modules_course_order', 'modules', ['course_id', 'order_index'])
    op.create_index('idx_lessons_module_order', 'lessons', ['module_id', 'order_index'])
    op.create_index('idx_lessons_content_type', 'lessons', ['content_type'])
    
    # Add indexes for Quiz models
    op.create_index('idx_quiz_attempts_user_quiz', 'quiz_attempts', ['user_id', 'quiz_id'])
    op.create_index('idx_quiz_attempts_submitted_at', 'quiz_attempts', ['submitted_at'])
    
    # Add indexes for Phishing models
    op.create_index('idx_phishing_templates_is_public', 'phishing_templates', ['is_public'])
    op.create_index('idx_phishing_templates_category_public', 'phishing_templates', ['category', 'is_public'])
    op.create_index('idx_phishing_results_campaign_clicked', 'phishing_results', ['campaign_id', 'link_clicked_at'])
    op.create_index('idx_phishing_results_user_campaigns', 'phishing_results', ['user_id', 'campaign_id'])
    
    # Add composite indexes for common join queries
    op.create_index('idx_users_company_active_verified', 'users', ['company_id', 'is_active', 'email_verified'])
    op.create_index('idx_course_enrollments_user_course_completed', 'course_enrollments', ['user_id', 'course_id', 'completed_at'])


def downgrade() -> None:
    # Drop indexes in reverse order
    op.drop_index('idx_course_enrollments_user_course_completed', 'course_enrollments')
    op.drop_index('idx_users_company_active_verified', 'users')
    
    op.drop_index('idx_phishing_results_user_campaigns', 'phishing_results')
    op.drop_index('idx_phishing_results_campaign_clicked', 'phishing_results')
    op.drop_index('idx_phishing_templates_category_public', 'phishing_templates')
    op.drop_index('idx_phishing_templates_is_public', 'phishing_templates')
    
    op.drop_index('idx_quiz_attempts_submitted_at', 'quiz_attempts')
    op.drop_index('idx_quiz_attempts_user_quiz', 'quiz_attempts')
    
    op.drop_index('idx_lessons_content_type', 'lessons')
    op.drop_index('idx_lessons_module_order', 'lessons')
    op.drop_index('idx_modules_course_order', 'modules')
    
    op.drop_index('idx_course_enrollments_completed_at', 'course_enrollments')
    op.drop_index('idx_course_enrollments_company_status', 'course_enrollments')
    op.drop_index('idx_course_enrollments_course_status', 'course_enrollments')
    op.drop_index('idx_course_enrollments_user_status', 'course_enrollments')
    
    op.drop_index('idx_courses_is_free', 'courses')
    op.drop_index('idx_courses_category_status', 'courses')
    op.drop_index('idx_courses_published_at', 'courses')
    op.drop_index('idx_courses_status', 'courses')
    
    op.drop_index('idx_companies_status_deleted', 'companies')
    op.drop_index('idx_companies_subscription_tier', 'companies')
    op.drop_index('idx_companies_status', 'companies')
    
    op.drop_index('idx_users_is_active_deleted', 'users')
    op.drop_index('idx_users_company_role', 'users')
    op.drop_index('idx_users_last_login_at', 'users')
    op.drop_index('idx_users_email_verified', 'users')