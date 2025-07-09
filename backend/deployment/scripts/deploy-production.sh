#!/bin/bash
set -e

# Production deployment script for awareness platform
# This script is executed on the production server

DEPLOY_DIR="/opt/awareness-platform"
BACKUP_DIR="/var/backups/awareness-platform"
LOG_FILE="/var/log/awareness-platform/deploy.log"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1" | tee -a "$LOG_FILE"
}

# Create necessary directories
mkdir -p "$BACKUP_DIR"
mkdir -p "$(dirname "$LOG_FILE")"

log "Starting deployment process..."

# Change to deployment directory
cd "$DEPLOY_DIR" || error "Failed to change to deployment directory"

# Pull latest code
log "Pulling latest code from repository..."
git pull origin main || error "Failed to pull latest code"

# Backup current deployment
log "Creating backup of current deployment..."
if [ -d "$DEPLOY_DIR" ]; then
    tar -czf "$BACKUP_DIR/backup_${TIMESTAMP}.tar.gz" \
        --exclude='*.log' \
        --exclude='__pycache__' \
        --exclude='node_modules' \
        --exclude='.git' \
        "$DEPLOY_DIR"
fi

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    error ".env file not found!"
fi

# Health check function
health_check() {
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost/api/health > /dev/null 2>&1; then
            log "Health check passed!"
            return 0
        fi
        
        warning "Health check attempt $attempt/$max_attempts failed, retrying..."
        sleep 5
        ((attempt++))
    done
    
    return 1
}

# Database backup
log "Backing up database..."
docker-compose -f docker-compose.prod.yml exec -T postgres pg_dump -U postgres awareness_db > "$BACKUP_DIR/db_backup_${TIMESTAMP}.sql" || warning "Database backup failed"

# Pull latest Docker images
log "Pulling latest Docker images..."
docker-compose -f docker-compose.prod.yml pull || error "Failed to pull Docker images"

# Stop current containers
log "Stopping current containers..."
docker-compose -f docker-compose.prod.yml down || error "Failed to stop containers"

# Start new containers
log "Starting new containers..."
docker-compose -f docker-compose.prod.yml up -d || error "Failed to start containers"

# Wait for services to be ready
log "Waiting for services to be ready..."
sleep 10

# Run database migrations
log "Running database migrations..."
docker-compose -f docker-compose.prod.yml exec -T backend alembic upgrade head || {
    error "Migration failed! Rolling back..."
    docker-compose -f docker-compose.prod.yml down
    # Restore from backup would go here
    exit 1
}

# Apply RLS policies
log "Applying Row Level Security policies..."
docker-compose -f docker-compose.prod.yml exec -T backend python scripts/init_database_with_rls.py || warning "RLS setup had issues"

# Run health check
log "Running health check..."
if ! health_check; then
    error "Health check failed! Rolling back..."
    docker-compose -f docker-compose.prod.yml down
    # Restore from backup would go here
    exit 1
fi

# Clean up old Docker images
log "Cleaning up old Docker images..."
docker image prune -f

# Clean up old backups (keep last 7 days)
log "Cleaning up old backups..."
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete
find "$BACKUP_DIR" -name "*.sql" -mtime +7 -delete

# Verify deployment
log "Verifying deployment..."
docker-compose -f docker-compose.prod.yml ps

log "Deployment completed successfully!"

# Send notification (optional - requires configuration)
# curl -X POST https://hooks.slack.com/services/YOUR/WEBHOOK/URL \
#     -H 'Content-type: application/json' \
#     --data "{\"text\":\"Deployment completed successfully at $(date)\"}"