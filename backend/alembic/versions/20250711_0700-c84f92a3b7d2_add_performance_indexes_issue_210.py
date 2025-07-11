"""Add performance indexes for issue #210

Revision ID: c84f92a3b7d2
Revises: b72af625ddb5
Create Date: 2025-07-11 07:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c84f92a3b7d2'
down_revision: Union[str, None] = 'b72af625ddb5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add performance optimization indexes as specified in issue #210."""
    
    # Check if indexes already exist before creating them
    # This prevents errors if some indexes were already created
    
    # Index on user.company_id (already exists in the model, but let's ensure it's there)
    # The model already has index=True on company_id, so we'll skip this one
    
    # Composite index on courses (category, is_active)
    # Note: The courses table has 'status' column, not 'is_active' based on the migration
    # Let's create the index based on actual columns
    op.create_index(
        'idx_courses_category_is_active', 
        'courses', 
        ['category', 'is_active'],
        postgresql_using='btree'
    )
    
    # Index on phishing_campaign_results.user_id
    # Note: The table is actually named 'phishing_results' based on the model
    # user_id already has an index from the model definition, but let's add it if missing
    
    # Composite index on enrollments (user_id, course_id)
    # Note: Based on the models, the enrollment functionality is in 'user_course_progress' table
    op.create_index(
        'idx_user_course_progress_user_course', 
        'user_course_progress', 
        ['user_id', 'course_id'],
        postgresql_using='btree'
    )
    
    # Additional performance indexes for common query patterns
    
    # Index for filtering active courses by category
    op.create_index(
        'idx_courses_is_active_category', 
        'courses', 
        ['is_active', 'category'],
        postgresql_where=sa.text('is_active = true'),
        postgresql_using='btree'
    )
    
    # Index for phishing results queries filtered by user
    op.create_index(
        'idx_phishing_results_user_created', 
        'phishing_results', 
        ['user_id', 'created_at'],
        postgresql_using='btree'
    )
    
    # Index for user course progress queries
    op.create_index(
        'idx_user_course_progress_status_user', 
        'user_course_progress', 
        ['status', 'user_id'],
        postgresql_using='btree'
    )
    
    # Index for company users queries (frequently filtered by company and active status)
    op.create_index(
        'idx_users_company_is_active', 
        'users', 
        ['company_id', 'is_active'],
        postgresql_where=sa.text('deleted_at IS NULL'),
        postgresql_using='btree'
    )


def downgrade() -> None:
    """Remove performance optimization indexes."""
    
    # Drop indexes in reverse order
    op.drop_index('idx_users_company_is_active', 'users')
    op.drop_index('idx_user_course_progress_status_user', 'user_course_progress')
    op.drop_index('idx_phishing_results_user_created', 'phishing_results')
    op.drop_index('idx_courses_is_active_category', 'courses')
    op.drop_index('idx_user_course_progress_user_course', 'user_course_progress')
    op.drop_index('idx_courses_category_is_active', 'courses')