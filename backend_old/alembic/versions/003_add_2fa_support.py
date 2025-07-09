"""Add 2FA support

Revision ID: 3c4d5e6f7a8b
Revises: 2b3c4d5e6f7a
Create Date: 2025-01-07

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '3c4d5e6f7a8b'
down_revision = '2b3c4d5e6f7a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add 2FA fields to users table
    op.add_column('users', sa.Column('totp_secret', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('totp_enabled', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('totp_verified_at', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('backup_codes', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('two_fa_recovery_codes_used', sa.Integer(), nullable=False, server_default='0'))
    
    # Create index for faster 2FA lookups
    op.create_index('idx_users_totp_enabled', 'users', ['totp_enabled'])
    
    # Create table for 2FA verification attempts (for rate limiting)
    op.create_table('two_fa_attempts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('attempt_type', sa.String(50), nullable=False),  # 'totp', 'backup_code'
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create index for rate limiting queries
    op.create_index('idx_2fa_attempts_user_created', 'two_fa_attempts', ['user_id', 'created_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_2fa_attempts_user_created', table_name='two_fa_attempts')
    op.drop_index('idx_users_totp_enabled', table_name='users')
    
    # Drop table
    op.drop_table('two_fa_attempts')
    
    # Remove columns from users table
    op.drop_column('users', 'two_fa_recovery_codes_used')
    op.drop_column('users', 'backup_codes')
    op.drop_column('users', 'totp_verified_at')
    op.drop_column('users', 'totp_enabled')
    op.drop_column('users', 'totp_secret')