# Database Management Scripts

This directory contains scripts for managing the database initialization and migrations.

## Scripts Overview

### `init_database.py`
Main database initialization script that:
- Checks if the database exists and creates it if needed
- Cleans up conflicting enum types
- Runs all Alembic migrations
- Verifies essential tables exist

### `init_dev_db.sh`
Convenience script for development setup:
```bash
# Basic initialization
./scripts/init_dev_db.sh

# With test data (when implemented)
./scripts/init_dev_db.sh --with-test-data
```

### `run_migrations.sh`
Run migrations manually:
```bash
./scripts/run_migrations.sh
```

### `check_db_status.py`
Check database connection and migration status:
```bash
python scripts/check_db_status.py
```

### `fix_enum_migration.py`
Legacy script for fixing enum type conflicts (called automatically by init_database.py)

## Production Deployment

The production Docker container automatically runs database initialization on startup via `start-prod.sh`.

## Development Setup

1. Create your `.env` file:
```bash
cp .env.example .env
```

2. Update DATABASE_URL in `.env` to point to your PostgreSQL instance

3. Run initialization:
```bash
./scripts/init_dev_db.sh
```

## Troubleshooting

### "No tables exist" Error
This means the database initialization hasn't run. Execute:
```bash
python scripts/init_database.py
```

### Enum Type Conflicts
The initialization script automatically handles enum type conflicts. If you still encounter issues:
```bash
python scripts/fix_enum_migration.py
alembic upgrade head
```

### Migration Failures
1. Check current status:
```bash
python scripts/check_db_status.py
```

2. If needed, reset migrations:
```bash
alembic downgrade base
alembic upgrade head
```

### Docker Issues
Ensure the database service is running before the backend:
```bash
docker-compose up -d db
# Wait for database to be ready
docker-compose up backend
```

## Database Schema

Key tables created by migrations:
- `users` - User accounts
- `organizations` - Organization/company records  
- `roles` - Role definitions
- `permissions` - Permission definitions
- `role_permissions` - Role-permission mappings
- `user_roles` - User-role assignments
- `courses` - Training courses
- `subscriptions` - Subscription management
- And many more...

## Environment Variables

Required for database connection:
- `DATABASE_URL` - PostgreSQL connection string
- `DATABASE_HOST` - Database host (for Docker)
- `DATABASE_PORT` - Database port (default: 5432)
- `DATABASE_USER` - Database username
- `DATABASE_PASSWORD` - Database password