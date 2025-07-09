#!/bin/bash
# Run this script on the production server

set -e

echo "=== Deploying Stage 1 to Production ==="

# Navigate to project directory
cd /opt/awareness-platform

# Backup database
echo "1. Backing up database..."
docker compose -f docker-compose.prod.yml exec postgres pg_dump -U awareness awareness_platform > backup_$(date +%Y%m%d_%H%M%S).sql

# Pull latest code
echo "2. Pulling latest code..."
git pull origin main

# Update environment
echo "3. Updating environment variables..."
echo "Please ensure .env is properly configured with production values"

# Stop services
echo "4. Stopping services..."
docker compose -f docker-compose.prod.yml down

# Build new images
echo "5. Building new images..."
docker compose -f docker-compose.prod.yml build

# Run migrations
echo "6. Running database migrations..."
docker compose -f docker-compose.prod.yml run --rm backend alembic upgrade head

# Apply RLS policies
echo "7. Applying RLS policies..."
docker compose -f docker-compose.prod.yml run --rm backend python -c "
import psycopg2
from core.config import settings
conn = psycopg2.connect(settings.DATABASE_URL)
with open('scripts/setup_row_level_security.sql', 'r') as f:
    conn.cursor().execute(f.read())
conn.commit()
conn.close()
print('RLS policies applied successfully')
"

# Start services
echo "8. Starting services..."
docker compose -f docker-compose.prod.yml up -d

# Wait for services to be healthy
echo "9. Waiting for services..."
sleep 30

# Run seed data
echo "10. Running seed data..."
docker compose -f docker-compose.prod.yml run --rm backend python scripts/seed_data_enhanced.py

# Check service health
echo "11. Checking service health..."
docker compose -f docker-compose.prod.yml ps

echo "Deployment complete!"
