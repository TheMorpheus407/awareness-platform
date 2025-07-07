"""Initial migration with users and companies

Revision ID: 001
Revises: 
Create Date: 2025-01-07 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create custom enums
    user_role_enum = postgresql.ENUM('user', 'company_admin', 'admin', name='userrole')
    user_role_enum.create(op.get_bind())
    
    company_size_enum = postgresql.ENUM('small', 'medium', 'large', 'enterprise', name='companysize')
    company_size_enum.create(op.get_bind())
    
    subscription_tier_enum = postgresql.ENUM('free', 'starter', 'professional', 'enterprise', name='subscriptiontier')
    subscription_tier_enum.create(op.get_bind())
    
    # Create companies table
    op.create_table('companies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('domain', sa.String(length=255), nullable=False),
        sa.Column('size', company_size_enum, nullable=False, server_default='small'),
        sa.Column('subscription_tier', subscription_tier_enum, nullable=False, server_default='free'),
        sa.Column('max_users', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('industry', sa.String(length=100), nullable=True),
        sa.Column('country', sa.String(length=100), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('address', sa.String(length=255), nullable=True),
        sa.Column('postal_code', sa.String(length=20), nullable=True),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('website', sa.String(length=255), nullable=True),
        sa.Column('logo_url', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('domain')
    )
    op.create_index(op.f('ix_companies_domain'), 'companies', ['domain'], unique=True)
    op.create_index(op.f('ix_companies_name'), 'companies', ['name'], unique=False)
    
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('role', sa.String(length=50), nullable=False, server_default='user'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.Column('password_changed_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('email_verification_token', sa.String(length=255), nullable=True),
        sa.Column('password_reset_token', sa.String(length=255), nullable=True),
        sa.Column('password_reset_expires', sa.DateTime(), nullable=True),
        sa.Column('avatar_url', sa.String(length=500), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('preferences', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_index(op.f('ix_users_company_id'), 'users', ['company_id'], unique=False)
    
    # Create updated_at trigger function
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    # Create triggers for updated_at
    op.execute("""
        CREATE TRIGGER update_companies_updated_at BEFORE UPDATE ON companies
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)
    
    op.execute("""
        CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade() -> None:
    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS update_users_updated_at ON users;")
    op.execute("DROP TRIGGER IF EXISTS update_companies_updated_at ON companies;")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column();")
    
    # Drop indexes
    op.drop_index(op.f('ix_users_company_id'), table_name='users')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    
    op.drop_index(op.f('ix_companies_name'), table_name='companies')
    op.drop_index(op.f('ix_companies_domain'), table_name='companies')
    op.drop_table('companies')
    
    # Drop enums
    subscription_tier_enum = postgresql.ENUM('free', 'starter', 'professional', 'enterprise', name='subscriptiontier')
    subscription_tier_enum.drop(op.get_bind())
    
    company_size_enum = postgresql.ENUM('small', 'medium', 'large', 'enterprise', name='companysize')
    company_size_enum.drop(op.get_bind())
    
    user_role_enum = postgresql.ENUM('user', 'company_admin', 'admin', name='userrole')
    user_role_enum.drop(op.get_bind())