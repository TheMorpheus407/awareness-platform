"""Initial migration with users and companies

Revision ID: 1a2b3c4d5e6f
Revises: 
Create Date: 2025-01-07 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = '1a2b3c4d5e6f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create custom enums separately to avoid conflicts
    # Using sa.Enum in column definitions to prevent duplicate creation attempts
    
    # First, create the ENUM types if they don't exist
    connection = op.get_bind()
    
    # Get current schema
    current_schema = connection.execute(text("SELECT current_schema()")).scalar()
    
    # Helper function to safely create enum types
    def create_enum_type_if_not_exists(type_name, values):
        # Check if type exists in any schema
        result = connection.execute(
            text(f"""
                SELECT n.nspname, t.typname 
                FROM pg_type t 
                JOIN pg_namespace n ON t.typnamespace = n.oid 
                WHERE t.typname = '{type_name}'
            """)
        ).fetchone()
        
        if result:
            schema_name = result[0]
            if schema_name != current_schema:
                # Type exists in different schema, drop and recreate in current schema
                try:
                    connection.execute(text(f"DROP TYPE IF EXISTS {schema_name}.{type_name} CASCADE"))
                except Exception:
                    pass
            else:
                # Type already exists in current schema, skip creation
                return
        
        # Create the type in current schema
        try:
            values_str = ', '.join([f"'{v}'" for v in values])
            connection.execute(text(f"CREATE TYPE {type_name} AS ENUM ({values_str})"))
        except Exception as e:
            # If it still fails, try to drop and recreate
            if "already exists" in str(e):
                connection.execute(text(f"DROP TYPE IF EXISTS {type_name} CASCADE"))
                connection.execute(text(f"CREATE TYPE {type_name} AS ENUM ({values_str})"))
    
    # Create all enum types
    create_enum_type_if_not_exists('userrole', ['system_admin', 'company_admin', 'manager', 'employee'])
    create_enum_type_if_not_exists('companysize', ['small', 'medium', 'large', 'enterprise'])
    create_enum_type_if_not_exists('subscriptiontier', ['free', 'starter', 'professional', 'enterprise'])
    create_enum_type_if_not_exists('companystatus', ['trial', 'active', 'suspended', 'cancelled'])
    
    # Create companies table
    op.create_table('companies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('domain', sa.String(length=255), nullable=False),
        sa.Column('size', sa.Enum('small', 'medium', 'large', 'enterprise', name='companysize', create_type=False), nullable=False, server_default='small'),
        sa.Column('status', sa.Enum('trial', 'active', 'suspended', 'cancelled', name='companystatus', create_type=False), nullable=False, server_default='trial'),
        sa.Column('subscription_tier', sa.Enum('free', 'starter', 'professional', 'enterprise', name='subscriptiontier', create_type=False), nullable=False, server_default='free'),
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
        sa.Column('role', sa.Enum('system_admin', 'company_admin', 'manager', 'employee', name='userrole', create_type=False), nullable=False, server_default='employee'),
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
    
    # Drop enums - using raw SQL with proper schema handling
    connection = op.get_bind()
    
    # Get current schema
    current_schema = connection.execute(text("SELECT current_schema()")).scalar()
    
    # Drop ENUMs if they exist in the current schema
    connection.execute(text(f"DROP TYPE IF EXISTS {current_schema}.subscriptiontier CASCADE;"))
    connection.execute(text(f"DROP TYPE IF EXISTS {current_schema}.companystatus CASCADE;"))
    connection.execute(text(f"DROP TYPE IF EXISTS {current_schema}.companysize CASCADE;"))
    connection.execute(text(f"DROP TYPE IF EXISTS {current_schema}.userrole CASCADE;"))