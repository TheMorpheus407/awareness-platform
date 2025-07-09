#!/bin/bash
# Deploy Stage 1 to production server

set -e

echo "=== Deploying Stage 1 to Production Server ==="

SERVER_IP="83.228.205.20"
SERVER_USER="ubuntu"
SSH_KEY="bootstrap-awareness private key.txt"
REMOTE_DIR="/opt/awareness"

# Step 1: Upload deployment package
echo "1. Uploading deployment package..."
scp -i "$SSH_KEY" stage1_deployment.tar.gz deploy_on_server.sh .env.production.template $SERVER_USER@$SERVER_IP:/tmp/

# Step 2: Extract and deploy on server
echo "2. Deploying on server..."
ssh -i "$SSH_KEY" $SERVER_USER@$SERVER_IP << 'ENDSSH'
set -e

echo "=== Server Deployment Starting ==="

# Navigate to project directory
cd /opt/awareness

# Backup current state
echo "Backing up current deployment..."
sudo tar -czf /tmp/backup_$(date +%Y%m%d_%H%M%S).tar.gz .

# Extract new deployment
echo "Extracting new deployment..."
cd /tmp
tar -xzf stage1_deployment.tar.gz

# Copy files to project directory
echo "Copying files..."
sudo cp -r backend/* /opt/awareness/backend/
sudo cp -r frontend/* /opt/awareness/frontend/
sudo cp -r deployment/* /opt/awareness/deployment/
sudo cp docker-compose.prod.yml /opt/awareness/

# Ensure correct permissions
sudo chown -R ubuntu:ubuntu /opt/awareness

# Navigate back to project
cd /opt/awareness

# Check if .env exists, if not create from template
if [ ! -f .env ]; then
    echo "Creating .env file..."
    sudo cp /tmp/.env.production.template .env
    echo "IMPORTANT: Please edit .env with production values!"
fi

# Pull latest changes from git
echo "Pulling latest changes..."
sudo git fetch origin main
sudo git reset --hard origin/main

# Stop current services
echo "Stopping current services..."
sudo docker compose -f docker-compose.prod.yml down || true

# Build new images
echo "Building new Docker images..."
sudo docker compose -f docker-compose.prod.yml build

# Start database first
echo "Starting database..."
sudo docker compose -f docker-compose.prod.yml up -d postgres redis

# Wait for database
echo "Waiting for database..."
sleep 20

# Run migrations
echo "Running database migrations..."
sudo docker compose -f docker-compose.prod.yml run --rm backend alembic upgrade head

# Apply RLS policies
echo "Applying RLS policies..."
if [ -f backend/scripts/setup_row_level_security.sql ]; then
    sudo docker compose -f docker-compose.prod.yml exec -T postgres psql -U awareness awareness_platform < backend/scripts/setup_row_level_security.sql
fi

# Start all services
echo "Starting all services..."
sudo docker compose -f docker-compose.prod.yml up -d

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 30

# Run seed data if needed
echo "Running seed data..."
sudo docker compose -f docker-compose.prod.yml run --rm backend python scripts/seed_data_enhanced.py || \
sudo docker compose -f docker-compose.prod.yml run --rm backend python scripts/seed_data.py || \
echo "Seed data already exists or script not found"

# Check service status
echo "Checking service status..."
sudo docker compose -f docker-compose.prod.yml ps

# Test endpoints
echo "Testing endpoints..."
curl -f http://localhost:8000/health || echo "Backend health check failed"
curl -f http://localhost:3000 || echo "Frontend health check failed"

echo "=== Deployment Complete ==="
echo "Please verify:"
echo "1. https://bootstrap-awareness.de - Main site"
echo "2. https://bootstrap-awareness.de/api/docs - API documentation"
echo "3. Check logs: sudo docker compose -f docker-compose.prod.yml logs"

ENDSSH

echo "=== Local deployment script complete ==="