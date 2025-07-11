#!/bin/bash
set -e

# Wait for database to be ready
echo "Waiting for database..."
while ! pg_isready -h ${DATABASE_HOST:-db} -p ${DATABASE_PORT:-5432} -U ${DATABASE_USER:-postgres}; do
  echo "Database is unavailable - sleeping"
  sleep 1
done

echo "Database is ready!"

# Skip migrations for now - run manually
echo "Skipping automatic migrations - run manually after fixing enum issues"

# Start the application with gunicorn
echo "Starting application..."
exec gunicorn main:app \
  --bind 0.0.0.0:8000 \
  --workers ${WORKERS:-4} \
  --worker-class uvicorn.workers.UvicornWorker \
  --log-level ${LOG_LEVEL:-info} \
  --access-logfile - \
  --error-logfile - \
  --timeout 120 \
  --keep-alive 5 \
  --max-requests 1000 \
  --max-requests-jitter 100