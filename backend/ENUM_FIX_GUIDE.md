# Enum Type Conflict Fix Guide

## Problem
PostgreSQL enum types already exist when running Alembic migrations, causing errors like:
- `sqlalchemy.exc.ProgrammingError: (psycopg2.errors.DuplicateObject) type "companysize" already exists`

## Root Causes
1. Enum types persist in the database even after failed migrations
2. Enum types may exist in different schemas
3. Alembic doesn't handle enum type conflicts well by default

## Solutions Applied

### 1. Updated Migration File (001_initial_migration.py)
- Added comprehensive enum existence checking
- Handles enums in different schemas
- Uses a helper function `create_enum_type_if_not_exists()` that:
  - Checks if enum exists in any schema
  - Drops enums from wrong schemas
  - Creates enums only if they don't exist in current schema
  - Handles creation failures gracefully

### 2. Fix Scripts Created

#### a) fix_enum_conflicts.py
- Comprehensive enum conflict resolution
- Checks all schemas for existing enums
- Ensures enums exist only in current schema
- Verifies enum values match expected values
- Reports on existing tables

**Usage:**
```bash
cd backend
source venv/bin/activate
python scripts/fix_enum_conflicts.py
```

#### b) Updated ci_migration_fix.py
- CI/CD specific enum handling
- Works with environment variables
- Drops enums from all schemas before migration

### 3. Migration Workflow

#### For Local Development:
```bash
# 1. Start database
docker compose up -d db

# 2. Fix enum conflicts
cd backend
source venv/bin/activate
python scripts/fix_enum_conflicts.py

# 3. Run migrations
alembic upgrade head
```

#### For CI/CD:
```bash
# The CI/CD pipeline should:
DATABASE_URL=$DATABASE_URL python scripts/ci_migration_fix.py
alembic upgrade head
```

#### If Tables Already Exist:
```bash
# Option 1: Drop everything and start fresh
alembic downgrade base
python scripts/fix_enum_conflicts.py
alembic upgrade head

# Option 2: Mark current state as migrated
alembic stamp head
```

## Key Changes Made

1. **Migration File**: Enhanced enum creation logic with schema awareness
2. **Enum Handling**: Proper checks for existing types across all schemas
3. **Error Recovery**: Graceful handling of "already exists" errors
4. **CI/CD Support**: Separate script for automated deployments

## Testing the Fix

1. Run the fix script and check output:
   ```bash
   python scripts/fix_enum_conflicts.py
   ```

2. Verify migrations work:
   ```bash
   alembic upgrade head
   alembic current
   ```

3. Test rollback:
   ```bash
   alembic downgrade base
   alembic upgrade head
   ```

## Preventing Future Issues

1. Always run `fix_enum_conflicts.py` before migrations in development
2. CI/CD pipeline includes `ci_migration_fix.py` before migrations
3. Use `create_type=False` in all `sa.Enum` column definitions
4. Handle schema-specific enum creation in migrations