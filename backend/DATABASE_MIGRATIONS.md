# Database Migration Guide

## Overview
This guide covers database migration management using Alembic for the Cybersecurity Awareness Platform. It includes creating, applying, and managing database schema changes safely in development and production environments.

## Table of Contents
1. [Migration Fundamentals](#migration-fundamentals)
2. [Initial Setup](#initial-setup)
3. [Creating Migrations](#creating-migrations)
4. [Applying Migrations](#applying-migrations)
5. [Migration Best Practices](#migration-best-practices)
6. [Common Scenarios](#common-scenarios)
7. [Production Migrations](#production-migrations)
8. [Troubleshooting](#troubleshooting)
9. [Migration Templates](#migration-templates)

## Migration Fundamentals

### What are Migrations?
Migrations are version-controlled, incremental, reversible changes to your database schema. They allow you to:
- Track database schema changes over time
- Collaborate with team members
- Deploy schema changes safely
- Roll back changes if needed
- Keep development and production databases in sync

### Migration Structure
```
alembic/
├── versions/           # Migration files
│   ├── 001_initial_migration.py
│   ├── 002_add_core_tables.py
│   └── 003_add_2fa_support.py
├── alembic.ini        # Alembic configuration
├── env.py             # Migration environment
└── script.py.mako     # Migration template
```

## Initial Setup

### 1. Configure Alembic
```bash
# Initialize Alembic (already done in this project)
alembic init alembic

# Configure database URL in alembic.ini
# Or use environment variable
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost/dbname"
```

### 2. Configure env.py
```python
# alembic/env.py
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from sqlalchemy.ext.asyncio import AsyncEngine
from alembic import context
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.db.base import Base
from backend.core.config import settings

# Import all models to ensure they're registered
from backend.models import *  # noqa

config = context.config

# Set database URL from environment
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

target_metadata = Base.metadata


def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = AsyncEngine(
        engine_from_config(
            config.get_section(config.config_ini_section),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
            future=True,
        )
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

## Creating Migrations

### Auto-generate Migrations
```bash
# Generate migration from model changes
alembic revision --autogenerate -m "Add user preferences table"

# Review the generated migration
# ALWAYS review auto-generated migrations!
cat alembic/versions/*_add_user_preferences_table.py
```

### Manual Migration Creation
```bash
# Create empty migration
alembic revision -m "Add custom index"
```

### Migration Template
```python
"""Add user preferences table

Revision ID: abc123
Revises: def456
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers
revision = 'abc123'
down_revision = 'def456'
branch_labels = None
depends_on = None


def upgrade():
    """Apply migration."""
    # Create table
    op.create_table(
        'user_preferences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('theme', sa.String(50), nullable=False, server_default='light'),
        sa.Column('language', sa.String(10), nullable=False, server_default='en'),
        sa.Column('email_notifications', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id')
    )
    
    # Create indexes
    op.create_index('ix_user_preferences_user_id', 'user_preferences', ['user_id'])
    
    # Add column to existing table
    op.add_column('users', sa.Column('preferences_id', sa.Integer(), nullable=True))
    
    # Create foreign key
    op.create_foreign_key(
        'fk_users_preferences',
        'users', 'user_preferences',
        ['preferences_id'], ['id']
    )


def downgrade():
    """Revert migration."""
    # Drop foreign key
    op.drop_constraint('fk_users_preferences', 'users', type_='foreignkey')
    
    # Drop column
    op.drop_column('users', 'preferences_id')
    
    # Drop index
    op.drop_index('ix_user_preferences_user_id', table_name='user_preferences')
    
    # Drop table
    op.drop_table('user_preferences')
```

## Applying Migrations

### Development Environment
```bash
# Check current version
alembic current

# Check migration history
alembic history

# Apply all migrations
alembic upgrade head

# Apply specific migration
alembic upgrade abc123

# Apply next migration
alembic upgrade +1

# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade abc123

# Rollback all migrations
alembic downgrade base
```

### Testing Migrations
```bash
# Test migration up and down
alembic upgrade head
alembic downgrade -1
alembic upgrade head

# Show SQL without applying
alembic upgrade head --sql

# Check migration status
alembic check
```

## Migration Best Practices

### 1. Always Review Auto-generated Migrations
```python
# Auto-generated migrations may:
# - Miss custom constraints
# - Generate inefficient operations
# - Include unwanted changes

# Always check for:
# - Correct column types
# - Proper constraints
# - Index creation
# - Data migration needs
```

### 2. Data Migrations
```python
def upgrade():
    """Migrate data along with schema."""
    # Add new column
    op.add_column('users', sa.Column('role', sa.String(50), nullable=True))
    
    # Migrate data
    connection = op.get_bind()
    result = connection.execute('SELECT id, is_admin FROM users')
    for row in result:
        role = 'admin' if row.is_admin else 'user'
        connection.execute(
            f"UPDATE users SET role = '{role}' WHERE id = {row.id}"
        )
    
    # Make column non-nullable after data migration
    op.alter_column('users', 'role', nullable=False)
    
    # Drop old column
    op.drop_column('users', 'is_admin')
```

### 3. Safe Column Operations
```python
# Adding a column safely
def upgrade():
    # 1. Add column as nullable
    op.add_column('users', sa.Column('email_verified', sa.Boolean(), nullable=True))
    
    # 2. Set default values for existing rows
    op.execute("UPDATE users SET email_verified = false WHERE email_verified IS NULL")
    
    # 3. Make column non-nullable
    op.alter_column('users', 'email_verified', nullable=False, server_default='false')
```

### 4. Handle Large Tables
```python
def upgrade():
    """Add index to large table without locking."""
    # PostgreSQL concurrent index creation
    op.execute('SET statement_timeout = 0')
    op.execute('SET lock_timeout = 0')
    op.create_index(
        'ix_large_table_column',
        'large_table',
        ['column'],
        postgresql_concurrently=True
    )
```

## Common Scenarios

### Adding a Table with Relationships
```python
def upgrade():
    """Add company_departments table."""
    op.create_table(
        'company_departments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('manager_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['manager_id'], ['users.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('company_id', 'name', name='uq_company_department')
    )
    
    # Add indexes
    op.create_index('ix_company_departments_company_id', 'company_departments', ['company_id'])
    op.create_index('ix_company_departments_manager_id', 'company_departments', ['manager_id'])
```

### Renaming a Column
```python
def upgrade():
    """Rename column with data preservation."""
    # PostgreSQL
    op.alter_column('users', 'full_name', new_column_name='display_name')
    
    # For other databases, might need:
    # op.add_column('users', sa.Column('display_name', sa.String(255)))
    # op.execute('UPDATE users SET display_name = full_name')
    # op.drop_column('users', 'full_name')
```

### Adding Enum Type
```python
from sqlalchemy.dialects import postgresql

# Define enum
user_role = postgresql.ENUM('user', 'admin', 'manager', name='user_role')

def upgrade():
    """Add user role enum."""
    # Create enum type
    user_role.create(op.get_bind())
    
    # Add column using enum
    op.add_column('users', sa.Column('role', user_role, nullable=False, server_default='user'))


def downgrade():
    """Remove user role enum."""
    op.drop_column('users', 'role')
    
    # Drop enum type
    user_role.drop(op.get_bind())
```

### Complex Schema Changes
```python
def upgrade():
    """Split users table into users and profiles."""
    # 1. Create profiles table
    op.create_table(
        'user_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('avatar_url', sa.String(500), nullable=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id')
    )
    
    # 2. Migrate data
    connection = op.get_bind()
    result = connection.execute(
        'SELECT id, bio, avatar_url, phone, address FROM users'
    )
    
    profiles = []
    for row in result:
        if any([row.bio, row.avatar_url, row.phone, row.address]):
            profiles.append({
                'user_id': row.id,
                'bio': row.bio,
                'avatar_url': row.avatar_url,
                'phone': row.phone,
                'address': row.address
            })
    
    if profiles:
        op.bulk_insert('user_profiles', profiles)
    
    # 3. Drop columns from users table
    op.drop_column('users', 'bio')
    op.drop_column('users', 'avatar_url')
    op.drop_column('users', 'phone')
    op.drop_column('users', 'address')
```

## Production Migrations

### Pre-Migration Checklist
```bash
#!/bin/bash
# pre_migration_check.sh

echo "=== Pre-Migration Checklist ==="

# 1. Backup database
echo "Creating database backup..."
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. Check current migration status
echo "Current migration version:"
alembic current

# 3. Test migration on staging
echo "Have you tested this migration on staging? (y/n)"
read -r response
if [[ "$response" != "y" ]]; then
    echo "Please test on staging first!"
    exit 1
fi

# 4. Check for long-running queries
echo "Checking for long-running queries..."
psql $DATABASE_URL -c "SELECT pid, now() - pg_stat_activity.query_start AS duration, query 
FROM pg_stat_activity 
WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes';"

# 5. Estimate migration time
echo "Estimated migration time based on table sizes:"
psql $DATABASE_URL -c "SELECT schemaname,tablename,pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"
```

### Production Migration Process
```bash
#!/bin/bash
# migrate_production.sh

set -e  # Exit on error

# Configuration
MAINTENANCE_MODE=true
BACKUP_BEFORE=true
VERIFY_AFTER=true

echo "=== Starting Production Migration ==="

# 1. Enable maintenance mode
if [ "$MAINTENANCE_MODE" = true ]; then
    echo "Enabling maintenance mode..."
    touch /var/www/maintenance.flag
fi

# 2. Create backup
if [ "$BACKUP_BEFORE" = true ]; then
    echo "Creating database backup..."
    pg_dump $DATABASE_URL | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz
fi

# 3. Run migration
echo "Running migration..."
alembic upgrade head

# 4. Verify migration
if [ "$VERIFY_AFTER" = true ]; then
    echo "Verifying migration..."
    alembic current
    
    # Run basic health check
    curl -f http://localhost:8000/health || {
        echo "Health check failed! Rolling back..."
        alembic downgrade -1
        exit 1
    }
fi

# 5. Disable maintenance mode
if [ "$MAINTENANCE_MODE" = true ]; then
    echo "Disabling maintenance mode..."
    rm -f /var/www/maintenance.flag
fi

echo "=== Migration Complete ==="
```

### Zero-Downtime Migrations
```python
# For adding columns without downtime
def upgrade():
    """Add column with zero downtime."""
    # 1. Add column as nullable
    op.add_column('users', sa.Column('new_field', sa.String(100), nullable=True))
    
    # 2. Deploy new code that writes to both old and new columns
    # 3. Backfill data in batches
    
    connection = op.get_bind()
    total = connection.execute('SELECT COUNT(*) FROM users').scalar()
    batch_size = 1000
    
    for offset in range(0, total, batch_size):
        op.execute(f"""
            UPDATE users 
            SET new_field = COALESCE(old_field, 'default') 
            WHERE id IN (
                SELECT id FROM users 
                WHERE new_field IS NULL 
                LIMIT {batch_size}
            )
        """)
    
    # 4. Make column non-nullable in next deployment
    # 5. Remove old column in final deployment
```

## Troubleshooting

### Common Issues

#### 1. Migration Conflicts
```bash
# Error: Can't locate revision identified by 'abc123'

# Fix: Check migration history
alembic history

# Resolve branching
alembic merge -m "Merge migrations" rev1 rev2
```

#### 2. Database Lock Timeout
```python
# Add timeout configuration
def upgrade():
    # Set statement timeout for PostgreSQL
    op.execute('SET statement_timeout = 300000')  # 5 minutes
    
    # Your migration operations
    op.create_index(...)
```

#### 3. Failed Migration Rollback
```bash
# Manually fix migration state
alembic stamp head  # Force to latest
alembic stamp abc123  # Force to specific revision

# Or directly in database
UPDATE alembic_version SET version_num = 'abc123';
```

#### 4. Schema Mismatch
```bash
# Compare database with models
alembic check

# Generate SQL to see differences
alembic upgrade head --sql > migration.sql

# Review and apply manually if needed
psql $DATABASE_URL < migration.sql
```

### Migration Recovery
```sql
-- Check migration history
SELECT * FROM alembic_version;

-- Manually update version
UPDATE alembic_version SET version_num = 'previous_version';

-- Check for locks
SELECT * FROM pg_locks WHERE NOT granted;

-- Kill blocking queries
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE pid <> pg_backend_pid() 
AND query LIKE '%ALTER TABLE%';
```

## Migration Templates

### Adding Audit Fields
```python
def add_audit_fields(table_name):
    """Add standard audit fields to a table."""
    op.add_column(table_name, sa.Column('created_by', sa.Integer(), nullable=True))
    op.add_column(table_name, sa.Column('updated_by', sa.Integer(), nullable=True))
    op.add_column(table_name, sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    
    op.create_foreign_key(
        f'fk_{table_name}_created_by',
        table_name, 'users',
        ['created_by'], ['id'],
        ondelete='SET NULL'
    )
    
    op.create_foreign_key(
        f'fk_{table_name}_updated_by',
        table_name, 'users',
        ['updated_by'], ['id'],
        ondelete='SET NULL'
    )
    
    op.create_index(f'ix_{table_name}_deleted_at', table_name, ['deleted_at'])
```

### Adding Full-Text Search
```python
def upgrade():
    """Add full-text search to articles."""
    # Add tsvector column
    op.add_column(
        'articles',
        sa.Column(
            'search_vector',
            postgresql.TSVECTOR,
            nullable=True
        )
    )
    
    # Create GIN index
    op.create_index(
        'ix_articles_search_vector',
        'articles',
        ['search_vector'],
        postgresql_using='gin'
    )
    
    # Update search vectors
    op.execute("""
        UPDATE articles 
        SET search_vector = 
            setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
            setweight(to_tsvector('english', coalesce(content, '')), 'B')
    """)
    
    # Create trigger to maintain search vector
    op.execute("""
        CREATE OR REPLACE FUNCTION articles_search_trigger() RETURNS trigger AS $$
        BEGIN
            NEW.search_vector :=
                setweight(to_tsvector('english', coalesce(NEW.title, '')), 'A') ||
                setweight(to_tsvector('english', coalesce(NEW.content, '')), 'B');
            RETURN NEW;
        END
        $$ LANGUAGE plpgsql;
        
        CREATE TRIGGER articles_search_update
        BEFORE INSERT OR UPDATE ON articles
        FOR EACH ROW EXECUTE FUNCTION articles_search_trigger();
    """)
```

### Performance Optimization Migration
```python
def upgrade():
    """Optimize database performance."""
    # Add missing indexes
    op.create_index('ix_users_email_lower', 'users', [sa.text('LOWER(email)')])
    op.create_index('ix_users_created_at', 'users', ['created_at'])
    
    # Partial indexes
    op.create_index(
        'ix_users_active',
        'users',
        ['email'],
        postgresql_where='is_active = true'
    )
    
    # Composite indexes
    op.create_index(
        'ix_enrollments_user_course',
        'enrollments',
        ['user_id', 'course_id'],
        unique=True
    )
    
    # Update table statistics
    op.execute('ANALYZE users')
    op.execute('ANALYZE enrollments')
```

---

For more information on specific migration scenarios or advanced techniques, consult the Alembic documentation or contact the database administration team.