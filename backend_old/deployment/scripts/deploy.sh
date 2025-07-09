#!/bin/bash
set -e

echo "Starting deployment..."

# Load environment variables
if [ -f /opt/awareness/.env ]; then
    export $(cat /opt/awareness/.env | xargs)
fi

# Pull latest images
echo "Pulling latest Docker images..."
docker compose pull

# Run database migrations
echo "Running database migrations..."
docker compose run --rm backend alembic upgrade head || true

# Stop old containers
echo "Stopping old containers..."
docker compose down

# Start new containers
echo "Starting new containers..."
docker compose up -d

# Wait for services to be healthy
echo "Waiting for services to be healthy..."
sleep 10

# Check health
for service in postgres redis backend frontend nginx; do
    if docker compose ps $service | grep -q "Up"; then
        echo "$service is running"
    else
        echo "ERROR: $service is not running"
        docker compose logs $service
        exit 1
    fi
done

# Clean up old images
echo "Cleaning up old images..."
docker image prune -f

echo "Deployment completed successfully!"