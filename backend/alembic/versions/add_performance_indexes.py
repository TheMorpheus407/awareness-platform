"""Add performance indexes for optimization

Revision ID: add_performance_indexes
Revises: 
Create Date: 2025-01-11 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_performance_indexes'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add performance indexes."""
    
    # Users table indexes
    op.create_index('idx_users_email_password', 'users', ['email', 'password_hash'])
    op.create_index('idx_users_company_role', 'users', ['company_id', 'role'])
    op.create_index('idx_users_is_active', 'users', ['is_active'])
    op.create_index('idx_users_created_at', 'users', ['created_at'])
    
    # Companies table indexes
    op.create_index('idx_companies_is_active', 'companies', ['is_active'])
    op.create_index('idx_companies_domain', 'companies', ['domain'])
    
    # Courses table indexes
    op.create_index('idx_courses_company_id', 'courses', ['company_id'])
    op.create_index('idx_courses_is_published', 'courses', ['is_published'])
    op.create_index('idx_courses_created_at', 'courses', ['created_at'])
    
    # User course progress indexes
    op.create_index('idx_user_course_progress_user_course', 'user_course_progress', ['user_id', 'course_id'])
    op.create_index('idx_user_course_progress_completed', 'user_course_progress', ['is_completed'])
    op.create_index('idx_user_course_progress_company', 'user_course_progress', ['company_id'])
    
    # User lesson progress indexes
    op.create_index('idx_user_lesson_progress_user_lesson', 'user_lesson_progress', ['user_id', 'lesson_id'])
    op.create_index('idx_user_lesson_progress_completed', 'user_lesson_progress', ['is_completed'])
    
    # Phishing results indexes
    op.create_index('idx_phishing_results_campaign_user', 'phishing_results', ['campaign_id', 'user_id'])
    op.create_index('idx_phishing_results_clicked', 'phishing_results', ['clicked'])
    op.create_index('idx_phishing_results_created_at', 'phishing_results', ['created_at'])
    
    # Analytics events indexes
    op.create_index('idx_analytics_events_user_event', 'analytics_events', ['user_id', 'event_type'])
    op.create_index('idx_analytics_events_company_event', 'analytics_events', ['company_id', 'event_type'])
    op.create_index('idx_analytics_events_created_at', 'analytics_events', ['created_at'])
    
    # Audit logs indexes
    op.create_index('idx_audit_logs_user_action', 'audit_logs', ['user_id', 'action'])
    op.create_index('idx_audit_logs_entity', 'audit_logs', ['entity_type', 'entity_id'])
    op.create_index('idx_audit_logs_created_at', 'audit_logs', ['created_at'])
    
    # Email logs indexes
    op.create_index('idx_email_logs_user_type', 'email_logs', ['user_id', 'email_type'])
    op.create_index('idx_email_logs_status', 'email_logs', ['status'])
    op.create_index('idx_email_logs_sent_at', 'email_logs', ['sent_at'])
    
    # Two FA attempts indexes
    op.create_index('idx_two_fa_attempts_user', 'two_fa_attempts', ['user_id'])
    op.create_index('idx_two_fa_attempts_created_at', 'two_fa_attempts', ['created_at'])
    
    # Composite indexes for common queries
    op.create_index('idx_users_company_active_role', 'users', ['company_id', 'is_active', 'role'])
    op.create_index('idx_courses_company_published', 'courses', ['company_id', 'is_published'])
    op.create_index('idx_analytics_date_range', 'analytics_events', ['company_id', 'created_at', 'event_type'])


def downgrade() -> None:
    """Drop performance indexes."""
    
    # Drop composite indexes
    op.drop_index('idx_analytics_date_range', 'analytics_events')
    op.drop_index('idx_courses_company_published', 'courses')
    op.drop_index('idx_users_company_active_role', 'users')
    
    # Drop two FA attempts indexes
    op.drop_index('idx_two_fa_attempts_created_at', 'two_fa_attempts')
    op.drop_index('idx_two_fa_attempts_user', 'two_fa_attempts')
    
    # Drop email logs indexes
    op.drop_index('idx_email_logs_sent_at', 'email_logs')
    op.drop_index('idx_email_logs_status', 'email_logs')
    op.drop_index('idx_email_logs_user_type', 'email_logs')
    
    # Drop audit logs indexes
    op.drop_index('idx_audit_logs_created_at', 'audit_logs')
    op.drop_index('idx_audit_logs_entity', 'audit_logs')
    op.drop_index('idx_audit_logs_user_action', 'audit_logs')
    
    # Drop analytics events indexes
    op.drop_index('idx_analytics_events_created_at', 'analytics_events')
    op.drop_index('idx_analytics_events_company_event', 'analytics_events')
    op.drop_index('idx_analytics_events_user_event', 'analytics_events')
    
    # Drop phishing results indexes
    op.drop_index('idx_phishing_results_created_at', 'phishing_results')
    op.drop_index('idx_phishing_results_clicked', 'phishing_results')
    op.drop_index('idx_phishing_results_campaign_user', 'phishing_results')
    
    # Drop user lesson progress indexes
    op.drop_index('idx_user_lesson_progress_completed', 'user_lesson_progress')
    op.drop_index('idx_user_lesson_progress_user_lesson', 'user_lesson_progress')
    
    # Drop user course progress indexes
    op.drop_index('idx_user_course_progress_company', 'user_course_progress')
    op.drop_index('idx_user_course_progress_completed', 'user_course_progress')
    op.drop_index('idx_user_course_progress_user_course', 'user_course_progress')
    
    # Drop courses table indexes
    op.drop_index('idx_courses_created_at', 'courses')
    op.drop_index('idx_courses_is_published', 'courses')
    op.drop_index('idx_courses_company_id', 'courses')
    
    # Drop companies table indexes
    op.drop_index('idx_companies_domain', 'companies')
    op.drop_index('idx_companies_is_active', 'companies')
    
    # Drop users table indexes
    op.drop_index('idx_users_created_at', 'users')
    op.drop_index('idx_users_is_active', 'users')
    op.drop_index('idx_users_company_role', 'users')
    op.drop_index('idx_users_email_password', 'users')