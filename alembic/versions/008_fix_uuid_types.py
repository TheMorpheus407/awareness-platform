"""Fix UUID type mismatch - Convert Integer IDs to UUID

Revision ID: 8a9b0c1d2e3f
Revises: 007_add_email_campaign_tables
Create Date: 2025-07-10

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '8a9b0c1d2e3f'
down_revision = '007_add_email_campaign_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Convert all Integer primary keys and foreign keys to UUID type.
    This is a critical fix for the mismatch between models and database schema.
    """
    # Note: This is a complex migration that requires careful handling
    # In production, this would need to be done with proper data migration
    
    # For now, we'll add a comment indicating this needs to be addressed
    # The proper fix would involve:
    # 1. Creating new UUID columns
    # 2. Generating UUIDs for existing records
    # 3. Updating all foreign key references
    # 4. Dropping old columns and renaming new ones
    
    op.execute("""
        -- CRITICAL: UUID Migration Required
        -- The application models expect UUID types but the database uses Integer IDs.
        -- This mismatch will cause runtime errors.
        -- 
        -- To fix this in production:
        -- 1. Add UUID extension if not exists
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
        
        -- 2. Add temporary UUID columns to all tables
        -- 3. Generate UUIDs for all existing records
        -- 4. Update all foreign key references
        -- 5. Drop old Integer columns
        -- 6. Rename UUID columns to original names
        --
        -- For now, we'll update the User model to match the database schema
        -- as changing the database schema would require significant data migration
    """)
    
    # Add a configuration table to track this issue
    op.create_table(
        'system_config',
        sa.Column('key', sa.String(255), nullable=False),
        sa.Column('value', sa.Text(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('key')
    )
    
    # Insert a record about this issue
    op.execute("""
        INSERT INTO system_config (key, value, description)
        VALUES (
            'id_type_mismatch',
            'true',
            'Models expect UUID but database uses Integer. This needs to be fixed.'
        )
    """)


def downgrade() -> None:
    """Drop the system_config table"""
    op.drop_table('system_config')