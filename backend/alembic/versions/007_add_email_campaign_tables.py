"""Add email campaign tables

Revision ID: 007_add_email_campaign_tables
Revises: 006_add_analytics_tables
Create Date: 2025-01-08

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '007_add_email_campaign_tables'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade():
    """Create email campaign related tables."""
    
    # Create email_templates table
    op.create_table(
        'email_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(255), nullable=False),
        sa.Column('type', sa.Enum('transactional', 'campaign', 'newsletter', 'notification', 
                                  'welcome', 'course_update', 'phishing_alert', 'security_alert',
                                  name='emailtemplatetype'), nullable=False),
        sa.Column('subject', sa.String(500), nullable=False),
        sa.Column('html_content', sa.Text(), nullable=False),
        sa.Column('text_content', sa.Text(), nullable=True),
        sa.Column('variables', sa.JSON(), nullable=True),
        sa.Column('preview_text', sa.String(500), nullable=True),
        sa.Column('from_name', sa.String(255), nullable=True),
        sa.Column('from_email', sa.String(255), nullable=True),
        sa.Column('reply_to', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('is_default', sa.Boolean(), nullable=True, default=False),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('total_sent', sa.Integer(), nullable=True, default=0),
        sa.Column('total_opened', sa.Integer(), nullable=True, default=0),
        sa.Column('total_clicked', sa.Integer(), nullable=True, default=0),
        sa.Column('avg_open_rate', sa.Float(), nullable=True, default=0.0),
        sa.Column('avg_click_rate', sa.Float(), nullable=True, default=0.0),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug'),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
    )
    op.create_index('idx_email_template_type_active', 'email_templates', ['type', 'is_active'])
    op.create_index('idx_email_template_slug', 'email_templates', ['slug'])
    
    # Create email_campaigns table
    op.create_table(
        'email_campaigns',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('template_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.Enum('draft', 'scheduled', 'sending', 'sent', 'paused', 
                                    'cancelled', 'completed', name='campaignstatus'), 
                  nullable=True, default='draft'),
        sa.Column('scheduled_at', sa.DateTime(), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('target_all_users', sa.Boolean(), nullable=True, default=False),
        sa.Column('target_user_roles', sa.JSON(), nullable=True),
        sa.Column('target_user_ids', sa.JSON(), nullable=True),
        sa.Column('target_segments', sa.JSON(), nullable=True),
        sa.Column('exclude_unsubscribed', sa.Boolean(), nullable=True, default=True),
        sa.Column('custom_subject', sa.String(500), nullable=True),
        sa.Column('custom_preview_text', sa.String(500), nullable=True),
        sa.Column('custom_variables', sa.JSON(), nullable=True),
        sa.Column('total_recipients', sa.Integer(), nullable=True, default=0),
        sa.Column('total_sent', sa.Integer(), nullable=True, default=0),
        sa.Column('total_delivered', sa.Integer(), nullable=True, default=0),
        sa.Column('total_opened', sa.Integer(), nullable=True, default=0),
        sa.Column('total_clicked', sa.Integer(), nullable=True, default=0),
        sa.Column('total_bounced', sa.Integer(), nullable=True, default=0),
        sa.Column('total_unsubscribed', sa.Integer(), nullable=True, default=0),
        sa.Column('delivery_rate', sa.Float(), nullable=True, default=0.0),
        sa.Column('open_rate', sa.Float(), nullable=True, default=0.0),
        sa.Column('click_rate', sa.Float(), nullable=True, default=0.0),
        sa.Column('bounce_rate', sa.Float(), nullable=True, default=0.0),
        sa.Column('unsubscribe_rate', sa.Float(), nullable=True, default=0.0),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['template_id'], ['email_templates.id'], ),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
    )
    op.create_index('idx_campaign_status_company', 'email_campaigns', ['status', 'company_id'])
    op.create_index('idx_campaign_scheduled', 'email_campaigns', ['scheduled_at', 'status'])
    
    # Create email_logs table
    op.create_table(
        'email_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('campaign_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('template_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('to_email', sa.String(255), nullable=False),
        sa.Column('from_email', sa.String(255), nullable=False),
        sa.Column('subject', sa.String(500), nullable=False),
        sa.Column('status', sa.Enum('pending', 'sent', 'delivered', 'opened', 'clicked',
                                    'bounced', 'failed', 'unsubscribed', 'marked_spam',
                                    name='emailstatus'), nullable=True, default='pending'),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('delivered_at', sa.DateTime(), nullable=True),
        sa.Column('opened_at', sa.DateTime(), nullable=True),
        sa.Column('first_opened_at', sa.DateTime(), nullable=True),
        sa.Column('clicked_at', sa.DateTime(), nullable=True),
        sa.Column('first_clicked_at', sa.DateTime(), nullable=True),
        sa.Column('bounced_at', sa.DateTime(), nullable=True),
        sa.Column('unsubscribed_at', sa.DateTime(), nullable=True),
        sa.Column('open_count', sa.Integer(), nullable=True, default=0),
        sa.Column('click_count', sa.Integer(), nullable=True, default=0),
        sa.Column('clicked_links', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('bounce_type', sa.String(50), nullable=True),
        sa.Column('provider', sa.String(50), nullable=True),
        sa.Column('message_id', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['campaign_id'], ['email_campaigns.id'], ),
        sa.ForeignKeyConstraint(['template_id'], ['email_templates.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    )
    op.create_index('idx_email_log_user_status', 'email_logs', ['user_id', 'status'])
    op.create_index('idx_email_log_campaign_status', 'email_logs', ['campaign_id', 'status'])
    op.create_index('idx_email_log_sent_at', 'email_logs', ['sent_at'])
    op.create_index('idx_email_log_message_id', 'email_logs', ['message_id'])
    
    # Create email_events table
    op.create_table(
        'email_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email_log_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('location', sa.JSON(), nullable=True),
        sa.Column('device_type', sa.String(50), nullable=True),
        sa.Column('os', sa.String(50), nullable=True),
        sa.Column('browser', sa.String(50), nullable=True),
        sa.Column('clicked_url', sa.Text(), nullable=True),
        sa.Column('click_position', sa.Integer(), nullable=True),
        sa.Column('bounce_reason', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['email_log_id'], ['email_logs.id'], ),
    )
    op.create_index('idx_email_event_log_type', 'email_events', ['email_log_id', 'event_type'])
    op.create_index('idx_email_event_timestamp', 'email_events', ['timestamp'])
    
    # Create email_preferences table
    op.create_table(
        'email_preferences',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_subscribed', sa.Boolean(), nullable=True, default=True),
        sa.Column('unsubscribed_at', sa.DateTime(), nullable=True),
        sa.Column('unsubscribe_token', sa.String(255), nullable=True),
        sa.Column('marketing_emails', sa.Boolean(), nullable=True, default=True),
        sa.Column('course_updates', sa.Boolean(), nullable=True, default=True),
        sa.Column('security_alerts', sa.Boolean(), nullable=True, default=True),
        sa.Column('newsletter', sa.Boolean(), nullable=True, default=True),
        sa.Column('promotional', sa.Boolean(), nullable=True, default=True),
        sa.Column('email_frequency', sa.Enum('immediately', 'daily', 'weekly', 'monthly', 'never',
                                           name='emailfrequency'), nullable=True, default='immediately'),
        sa.Column('digest_day', sa.Integer(), nullable=True),
        sa.Column('digest_hour', sa.Integer(), nullable=True, default=9),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
        sa.UniqueConstraint('unsubscribe_token'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    )
    op.create_index('idx_email_pref_user', 'email_preferences', ['user_id'])
    op.create_index('idx_email_pref_token', 'email_preferences', ['unsubscribe_token'])
    
    # Create email_bounces table
    op.create_table(
        'email_bounces',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('bounce_type', sa.String(50), nullable=False),
        sa.Column('bounce_count', sa.Integer(), nullable=True, default=1),
        sa.Column('last_bounce_at', sa.DateTime(), nullable=True),
        sa.Column('is_suppressed', sa.Boolean(), nullable=True, default=False),
        sa.Column('suppressed_at', sa.DateTime(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('diagnostic_code', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email', name='uq_email_bounce_email'),
    )
    op.create_index('idx_email_bounce_email', 'email_bounces', ['email'])
    op.create_index('idx_email_bounce_suppressed', 'email_bounces', ['is_suppressed'])


def downgrade():
    """Drop email campaign related tables."""
    
    # Drop indexes
    op.drop_index('idx_email_bounce_suppressed', table_name='email_bounces')
    op.drop_index('idx_email_bounce_email', table_name='email_bounces')
    op.drop_index('idx_email_pref_token', table_name='email_preferences')
    op.drop_index('idx_email_pref_user', table_name='email_preferences')
    op.drop_index('idx_email_event_timestamp', table_name='email_events')
    op.drop_index('idx_email_event_log_type', table_name='email_events')
    op.drop_index('idx_email_log_message_id', table_name='email_logs')
    op.drop_index('idx_email_log_sent_at', table_name='email_logs')
    op.drop_index('idx_email_log_campaign_status', table_name='email_logs')
    op.drop_index('idx_email_log_user_status', table_name='email_logs')
    op.drop_index('idx_campaign_scheduled', table_name='email_campaigns')
    op.drop_index('idx_campaign_status_company', table_name='email_campaigns')
    op.drop_index('idx_email_template_slug', table_name='email_templates')
    op.drop_index('idx_email_template_type_active', table_name='email_templates')
    
    # Drop tables
    op.drop_table('email_bounces')
    op.drop_table('email_preferences')
    op.drop_table('email_events')
    op.drop_table('email_logs')
    op.drop_table('email_campaigns')
    op.drop_table('email_templates')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS emailfrequency')
    op.execute('DROP TYPE IF EXISTS emailstatus')
    op.execute('DROP TYPE IF EXISTS campaignstatus')
    op.execute('DROP TYPE IF EXISTS emailtemplatetype')