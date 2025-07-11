#!/bin/bash
# Script to run database migrations manually

set -e

echo "=== Running Database Migrations ==="

# Check if we're in the backend directory
if [ ! -f "alembic.ini" ]; then
    echo "Error: Must run this script from the backend directory"
    exit 1
fi

# Load environment variables if .env exists
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check database connection
echo "Checking database connection..."
if pg_isready -h ${DATABASE_HOST:-localhost} -p ${DATABASE_PORT:-5432} -U ${DATABASE_USER:-postgres}; then
    echo "Database is accessible"
else
    echo "Error: Cannot connect to database"
    exit 1
fi

# Run migrations
echo "Running Alembic migrations..."
alembic upgrade head

if [ $? -eq 0 ]; then
    echo "=== Migrations completed successfully ==="
else
    echo "=== Migration failed ==="
    exit 1
fi