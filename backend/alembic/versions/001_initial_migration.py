"""Initial migration with users and companies - Fixed enum handling

Revision ID: 1a2b3c4d5e6f
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '1a2b3c4d5e6f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Get connection for raw SQL execution
    connection = op.get_bind()
    
    # Drop all existing enums first to ensure clean state
    connection.execute(text("DROP TYPE IF EXISTS userrole CASCADE"))
    connection.execute(text("DROP TYPE IF EXISTS companysize CASCADE"))
    connection.execute(text("DROP TYPE IF EXISTS subscriptiontier CASCADE"))
    connection.execute(text("DROP TYPE IF EXISTS companystatus CASCADE"))
    
    # Create enum types using raw SQL to avoid SQLAlchemy auto-creation
    connection.execute(text("CREATE TYPE userrole AS ENUM ('system_admin', 'company_admin', 'manager', 'employee')"))
    connection.execute(text("CREATE TYPE companysize AS ENUM ('small', 'medium', 'large', 'enterprise')"))
    connection.execute(text("CREATE TYPE subscriptiontier AS ENUM ('free', 'starter', 'professional', 'enterprise')"))
    connection.execute(text("CREATE TYPE companystatus AS ENUM ('trial', 'active', 'suspended', 'cancelled')"))
    
    # Create companies table
    op.create_table('companies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('domain', sa.String(length=255), nullable=False),
        sa.Column('size', postgresql.ENUM('small', 'medium', 'large', 'enterprise', name='companysize', create_type=False), nullable=False, server_default='small'),
        sa.Column('status', postgresql.ENUM('trial', 'active', 'suspended', 'cancelled', name='companystatus', create_type=False), nullable=False, server_default='trial'),
        sa.Column('subscription_tier', postgresql.ENUM('free', 'starter', 'professional', 'enterprise', name='subscriptiontier', create_type=False), nullable=False, server_default='free'),
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
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('role', postgresql.ENUM('system_admin', 'company_admin', 'manager', 'employee', name='userrole', create_type=False), nullable=False, server_default='employee'),
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
        sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
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
    
    # Drop indexes and tables
    op.drop_index(op.f('ix_users_company_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.drop_index(op.f('ix_companies_name'), table_name='companies')
    op.drop_index(op.f('ix_companies_domain'), table_name='companies')
    op.drop_table('companies')
    
    # Drop enum types with CASCADE to handle dependencies
    connection = op.get_bind()
    connection.execute(text("DROP TYPE IF EXISTS userrole CASCADE"))
    connection.execute(text("DROP TYPE IF EXISTS companysize CASCADE"))
    connection.execute(text("DROP TYPE IF EXISTS subscriptiontier CASCADE"))
    connection.execute(text("DROP TYPE IF EXISTS companystatus CASCADE"))