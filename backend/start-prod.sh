#!/bin/bash
set -e

# Wait for database to be ready
echo "Waiting for database..."
MAX_RETRIES=30
RETRY_COUNT=0

while ! pg_isready -h ${DATABASE_HOST:-db} -p ${DATABASE_PORT:-5432} -U ${DATABASE_USER:-postgres}; do
  RETRY_COUNT=$((RETRY_COUNT + 1))
  if [ $RETRY_COUNT -gt $MAX_RETRIES ]; then
    echo "Database did not become ready in time!"
    exit 1
  fi
  echo "Database is unavailable - sleeping (attempt $RETRY_COUNT/$MAX_RETRIES)"
  sleep 2
done

echo "Database is ready!"

# Initialize database with production script
echo "Initializing database..."
python scripts/init_db_production.py

# Check if initialization was successful
if [ $? -ne 0 ]; then
  echo "Database initialization failed!"
  # Try the original script as fallback
  echo "Trying fallback initialization..."
  python scripts/init_database.py
  if [ $? -ne 0 ]; then
    echo "Fallback initialization also failed!"
    exit 1
  fi
fi

echo "Database initialization complete!"

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