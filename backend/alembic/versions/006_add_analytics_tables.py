"""Add analytics tables

Revision ID: 006
Revises: 005
Create Date: 2025-01-08

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create analytics schema
    op.execute("CREATE SCHEMA IF NOT EXISTS analytics")
    
    # Analytics event tracking table
    op.create_table(
        'analytics_events',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('event_category', sa.String(50), nullable=False),
        sa.Column('event_action', sa.String(100), nullable=False),
        sa.Column('event_label', sa.String(255)),
        sa.Column('event_value', sa.Numeric(10, 2)),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('company_id', sa.UUID(), nullable=True),
        sa.Column('session_id', sa.String(100)),
        sa.Column('metadata', sa.JSON),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='SET NULL'),
        schema='analytics'
    )
    
    # Course analytics aggregation table
    op.create_table(
        'course_analytics',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('course_id', sa.UUID(), nullable=False),
        sa.Column('company_id', sa.UUID(), nullable=True),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('enrollments_count', sa.Integer(), default=0),
        sa.Column('completions_count', sa.Integer(), default=0),
        sa.Column('avg_progress', sa.Numeric(5, 2), default=0),
        sa.Column('avg_score', sa.Numeric(5, 2), default=0),
        sa.Column('total_time_spent', sa.Integer(), default=0),  # in minutes
        sa.Column('unique_users', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('course_id', 'company_id', 'date', name='uq_course_company_date'),
        schema='analytics'
    )
    
    # User engagement analytics table
    op.create_table(
        'user_engagement',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('company_id', sa.UUID(), nullable=True),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('login_count', sa.Integer(), default=0),
        sa.Column('page_views', sa.Integer(), default=0),
        sa.Column('time_spent', sa.Integer(), default=0),  # in minutes
        sa.Column('courses_started', sa.Integer(), default=0),
        sa.Column('courses_completed', sa.Integer(), default=0),
        sa.Column('quizzes_taken', sa.Integer(), default=0),
        sa.Column('avg_quiz_score', sa.Numeric(5, 2)),
        sa.Column('phishing_attempts', sa.Integer(), default=0),
        sa.Column('phishing_reported', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'date', name='uq_user_date'),
        schema='analytics'
    )
    
    # Revenue analytics table
    op.create_table(
        'revenue_analytics',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('company_id', sa.UUID(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('subscription_revenue', sa.Numeric(10, 2), default=0),
        sa.Column('one_time_revenue', sa.Numeric(10, 2), default=0),
        sa.Column('total_revenue', sa.Numeric(10, 2), default=0),
        sa.Column('new_subscriptions', sa.Integer(), default=0),
        sa.Column('cancelled_subscriptions', sa.Integer(), default=0),
        sa.Column('active_subscriptions', sa.Integer(), default=0),
        sa.Column('mrr', sa.Numeric(10, 2), default=0),  # Monthly Recurring Revenue
        sa.Column('arr', sa.Numeric(10, 2), default=0),  # Annual Recurring Revenue
        sa.Column('currency', sa.String(3), default='EUR'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('company_id', 'date', name='uq_company_revenue_date'),
        schema='analytics'
    )
    
    # Phishing simulation analytics table
    op.create_table(
        'phishing_analytics',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('company_id', sa.UUID(), nullable=False),
        sa.Column('campaign_id', sa.UUID(), nullable=True),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('emails_sent', sa.Integer(), default=0),
        sa.Column('emails_opened', sa.Integer(), default=0),
        sa.Column('links_clicked', sa.Integer(), default=0),
        sa.Column('credentials_entered', sa.Integer(), default=0),
        sa.Column('reported_suspicious', sa.Integer(), default=0),
        sa.Column('open_rate', sa.Numeric(5, 2), default=0),
        sa.Column('click_rate', sa.Numeric(5, 2), default=0),
        sa.Column('report_rate', sa.Numeric(5, 2), default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['campaign_id'], ['phishing_campaigns.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('company_id', 'campaign_id', 'date', name='uq_company_campaign_date'),
        schema='analytics'
    )
    
    # Real-time metrics table (for dashboard)
    op.create_table(
        'realtime_metrics',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('metric_name', sa.String(100), nullable=False),
        sa.Column('metric_value', sa.Numeric(20, 4), nullable=False),
        sa.Column('metric_type', sa.String(50), nullable=False),  # counter, gauge, percentage
        sa.Column('company_id', sa.UUID(), nullable=True),
        sa.Column('dimension', sa.String(100)),  # e.g., course_id, user_role
        sa.Column('dimension_value', sa.String(255)),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('ttl', sa.Integer(), default=3600),  # Time to live in seconds
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        schema='analytics'
    )
    
    # Create indexes for performance
    op.create_index('idx_analytics_events_user_created', 'analytics_events', ['user_id', 'created_at'], schema='analytics')
    op.create_index('idx_analytics_events_company_created', 'analytics_events', ['company_id', 'created_at'], schema='analytics')
    op.create_index('idx_analytics_events_type_category', 'analytics_events', ['event_type', 'event_category'], schema='analytics')
    
    op.create_index('idx_course_analytics_course_date', 'course_analytics', ['course_id', 'date'], schema='analytics')
    op.create_index('idx_course_analytics_company_date', 'course_analytics', ['company_id', 'date'], schema='analytics')
    
    op.create_index('idx_user_engagement_user_date', 'user_engagement', ['user_id', 'date'], schema='analytics')
    op.create_index('idx_user_engagement_company_date', 'user_engagement', ['company_id', 'date'], schema='analytics')
    
    op.create_index('idx_revenue_analytics_company_date', 'revenue_analytics', ['company_id', 'date'], schema='analytics')
    
    op.create_index('idx_phishing_analytics_company_date', 'phishing_analytics', ['company_id', 'date'], schema='analytics')
    
    op.create_index('idx_realtime_metrics_name_company', 'realtime_metrics', ['metric_name', 'company_id'], schema='analytics')
    op.create_index('idx_realtime_metrics_timestamp', 'realtime_metrics', ['timestamp'], schema='analytics')
    
    # Create materialized views for dashboard performance
    op.execute("""
        CREATE MATERIALIZED VIEW analytics.company_overview AS
        SELECT 
            c.id as company_id,
            c.name as company_name,
            COUNT(DISTINCT u.id) as total_users,
            COUNT(DISTINCT CASE WHEN u.is_active = true THEN u.id END) as active_users,
            COUNT(DISTINCT e.id) as total_enrollments,
            COUNT(DISTINCT CASE WHEN e.completed_at IS NOT NULL THEN e.id END) as completed_courses,
            AVG(e.progress) as avg_course_progress,
            COUNT(DISTINCT s.id) as active_subscriptions,
            SUM(s.amount) as total_revenue
        FROM companies c
        LEFT JOIN users u ON u.company_id = c.id
        LEFT JOIN enrollments e ON e.user_id = u.id
        LEFT JOIN subscriptions s ON s.company_id = c.id AND s.status = 'active'
        GROUP BY c.id, c.name
    """)
    
    # Create refresh function for materialized view
    op.execute("""
        CREATE OR REPLACE FUNCTION analytics.refresh_company_overview()
        RETURNS void AS $$
        BEGIN
            REFRESH MATERIALIZED VIEW CONCURRENTLY analytics.company_overview;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # RLS policies for analytics tables
    op.execute("""
        ALTER TABLE analytics.analytics_events ENABLE ROW LEVEL SECURITY;
        ALTER TABLE analytics.course_analytics ENABLE ROW LEVEL SECURITY;
        ALTER TABLE analytics.user_engagement ENABLE ROW LEVEL SECURITY;
        ALTER TABLE analytics.revenue_analytics ENABLE ROW LEVEL SECURITY;
        ALTER TABLE analytics.phishing_analytics ENABLE ROW LEVEL SECURITY;
        ALTER TABLE analytics.realtime_metrics ENABLE ROW LEVEL SECURITY;
        
        -- Analytics events policies
        CREATE POLICY analytics_events_company_policy ON analytics.analytics_events
            FOR ALL USING (
                company_id IS NULL OR 
                company_id IN (
                    SELECT company_id FROM users WHERE id = current_setting('app.user_id')::uuid
                )
            );
            
        CREATE POLICY analytics_events_admin_policy ON analytics.analytics_events
            FOR ALL USING (
                EXISTS (
                    SELECT 1 FROM users 
                    WHERE id = current_setting('app.user_id')::uuid 
                    AND role = 'SUPER_ADMIN'
                )
            );
            
        -- Course analytics policies
        CREATE POLICY course_analytics_company_policy ON analytics.course_analytics
            FOR ALL USING (
                company_id IS NULL OR
                company_id IN (
                    SELECT company_id FROM users WHERE id = current_setting('app.user_id')::uuid
                )
            );
            
        CREATE POLICY course_analytics_admin_policy ON analytics.course_analytics
            FOR ALL USING (
                EXISTS (
                    SELECT 1 FROM users 
                    WHERE id = current_setting('app.user_id')::uuid 
                    AND role = 'SUPER_ADMIN'
                )
            );
            
        -- Similar policies for other tables
        CREATE POLICY user_engagement_policy ON analytics.user_engagement
            FOR ALL USING (
                user_id = current_setting('app.user_id')::uuid OR
                company_id IN (
                    SELECT company_id FROM users 
                    WHERE id = current_setting('app.user_id')::uuid 
                    AND role IN ('ADMIN', 'SUPER_ADMIN')
                )
            );
            
        CREATE POLICY revenue_analytics_policy ON analytics.revenue_analytics
            FOR ALL USING (
                company_id IN (
                    SELECT company_id FROM users 
                    WHERE id = current_setting('app.user_id')::uuid 
                    AND role IN ('ADMIN', 'SUPER_ADMIN')
                )
            );
            
        CREATE POLICY phishing_analytics_policy ON analytics.phishing_analytics
            FOR ALL USING (
                company_id IN (
                    SELECT company_id FROM users 
                    WHERE id = current_setting('app.user_id')::uuid 
                    AND role IN ('ADMIN', 'SUPER_ADMIN')
                )
            );
            
        CREATE POLICY realtime_metrics_policy ON analytics.realtime_metrics
            FOR ALL USING (
                company_id IS NULL OR
                company_id IN (
                    SELECT company_id FROM users WHERE id = current_setting('app.user_id')::uuid
                )
            );
    """)


def downgrade() -> None:
    # Drop RLS policies
    op.execute("""
        DROP POLICY IF EXISTS analytics_events_company_policy ON analytics.analytics_events;
        DROP POLICY IF EXISTS analytics_events_admin_policy ON analytics.analytics_events;
        DROP POLICY IF EXISTS course_analytics_company_policy ON analytics.course_analytics;
        DROP POLICY IF EXISTS course_analytics_admin_policy ON analytics.course_analytics;
        DROP POLICY IF EXISTS user_engagement_policy ON analytics.user_engagement;
        DROP POLICY IF EXISTS revenue_analytics_policy ON analytics.revenue_analytics;
        DROP POLICY IF EXISTS phishing_analytics_policy ON analytics.phishing_analytics;
        DROP POLICY IF EXISTS realtime_metrics_policy ON analytics.realtime_metrics;
    """)
    
    # Drop materialized view and function
    op.execute("DROP MATERIALIZED VIEW IF EXISTS analytics.company_overview")
    op.execute("DROP FUNCTION IF EXISTS analytics.refresh_company_overview()")
    
    # Drop tables
    op.drop_table('realtime_metrics', schema='analytics')
    op.drop_table('phishing_analytics', schema='analytics')
    op.drop_table('revenue_analytics', schema='analytics')
    op.drop_table('user_engagement', schema='analytics')
    op.drop_table('course_analytics', schema='analytics')
    op.drop_table('analytics_events', schema='analytics')
    
    # Drop schema
    op.execute("DROP SCHEMA IF EXISTS analytics CASCADE")