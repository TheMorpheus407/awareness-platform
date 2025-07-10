"""Add missing indexes for performance optimization

Revision ID: 9a0b1c2d3e4f
Revises: 8a9b0c1d2e3f
Create Date: 2025-07-10

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '9a0b1c2d3e4f'
down_revision = '8a9b0c1d2e3f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add missing indexes on foreign keys and frequently queried columns."""
    
    # Add indexes for foreign keys without indexes (found in analysis)
    
    # phishing_campaigns table
    op.create_index('ix_phishing_campaigns_created_by_id', 'phishing_campaigns', ['created_by_id'])
    
    # analytics_events table (if exists)
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'analytics_events') THEN
                CREATE INDEX IF NOT EXISTS ix_analytics_events_event_type ON analytics_events(event_type);
                CREATE INDEX IF NOT EXISTS ix_analytics_events_created_at ON analytics_events(created_at);
                CREATE INDEX IF NOT EXISTS ix_analytics_events_user_company ON analytics_events(user_id, company_id);
            END IF;
        END $$;
    """)
    
    # user_engagements table (if exists)
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'user_engagements') THEN
                CREATE INDEX IF NOT EXISTS ix_user_engagements_user_id ON user_engagements(user_id);
                CREATE INDEX IF NOT EXISTS ix_user_engagements_course_id ON user_engagements(course_id);
                CREATE INDEX IF NOT EXISTS ix_user_engagements_date ON user_engagements(date);
            END IF;
        END $$;
    """)
    
    # course_completions table (if exists)
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'course_completions') THEN
                CREATE INDEX IF NOT EXISTS ix_course_completions_user_course ON course_completions(user_id, course_id);
                CREATE INDEX IF NOT EXISTS ix_course_completions_completed_at ON course_completions(completed_at);
            END IF;
        END $$;
    """)
    
    # Add composite indexes for common query patterns
    
    # Users table - common lookups
    op.create_index('ix_users_email_active', 'users', ['email', 'is_active'])
    op.create_index('ix_users_company_role', 'users', ['company_id', 'role'])
    
    # Courses table - filtering
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'courses') THEN
                CREATE INDEX IF NOT EXISTS ix_courses_active_category ON courses(is_active, category);
                CREATE INDEX IF NOT EXISTS ix_courses_language_level ON courses(language, difficulty_level);
            END IF;
        END $$;
    """)
    
    # User course progress - performance critical
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'user_course_progress') THEN
                CREATE INDEX IF NOT EXISTS ix_user_course_progress_company_status ON user_course_progress(company_id, status);
                CREATE INDEX IF NOT EXISTS ix_user_course_progress_user_status ON user_course_progress(user_id, status);
            END IF;
        END $$;
    """)
    
    # Phishing results - reporting queries
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'phishing_results') THEN
                CREATE INDEX IF NOT EXISTS ix_phishing_results_campaign_clicked ON phishing_results(campaign_id, link_clicked_at);
                CREATE INDEX IF NOT EXISTS ix_phishing_results_dates ON phishing_results(email_sent_at, email_opened_at, link_clicked_at);
            END IF;
        END $$;
    """)
    
    # Password reset tokens - security lookups
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.columns 
                     WHERE table_name = 'users' 
                     AND column_name = 'password_reset_token') THEN
                CREATE INDEX IF NOT EXISTS ix_users_password_reset_token ON users(password_reset_token) 
                WHERE password_reset_token IS NOT NULL;
            END IF;
        END $$;
    """)
    
    # Two-factor authentication lookups
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'two_fa_attempts') THEN
                CREATE INDEX IF NOT EXISTS ix_two_fa_attempts_user_created ON two_fa_attempts(user_id, created_at);
            END IF;
        END $$;
    """)
    
    # Email campaign performance
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'email_campaigns') THEN
                CREATE INDEX IF NOT EXISTS ix_email_campaigns_company_status ON email_campaigns(company_id, status);
                CREATE INDEX IF NOT EXISTS ix_email_campaigns_scheduled ON email_campaigns(scheduled_at) 
                WHERE scheduled_at IS NOT NULL;
            END IF;
        END $$;
    """)


def downgrade() -> None:
    """Remove the added indexes."""
    
    # Drop indexes in reverse order
    op.drop_index('ix_users_email_active', 'users')
    op.drop_index('ix_users_company_role', 'users')
    op.drop_index('ix_phishing_campaigns_created_by_id', 'phishing_campaigns')
    
    # Drop conditional indexes
    op.execute("""
        DROP INDEX IF EXISTS ix_analytics_events_event_type;
        DROP INDEX IF EXISTS ix_analytics_events_created_at;
        DROP INDEX IF EXISTS ix_analytics_events_user_company;
        DROP INDEX IF EXISTS ix_user_engagements_user_id;
        DROP INDEX IF EXISTS ix_user_engagements_course_id;
        DROP INDEX IF EXISTS ix_user_engagements_date;
        DROP INDEX IF EXISTS ix_course_completions_user_course;
        DROP INDEX IF EXISTS ix_course_completions_completed_at;
        DROP INDEX IF EXISTS ix_courses_active_category;
        DROP INDEX IF EXISTS ix_courses_language_level;
        DROP INDEX IF EXISTS ix_user_course_progress_company_status;
        DROP INDEX IF EXISTS ix_user_course_progress_user_status;
        DROP INDEX IF EXISTS ix_phishing_results_campaign_clicked;
        DROP INDEX IF EXISTS ix_phishing_results_dates;
        DROP INDEX IF EXISTS ix_users_password_reset_token;
        DROP INDEX IF EXISTS ix_two_fa_attempts_user_created;
        DROP INDEX IF EXISTS ix_email_campaigns_company_status;
        DROP INDEX IF EXISTS ix_email_campaigns_scheduled;
    """)