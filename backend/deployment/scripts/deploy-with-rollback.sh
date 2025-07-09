#!/bin/bash
set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Deployment configuration
DEPLOYMENT_DIR="/opt/awareness"
BACKUP_DIR="/opt/awareness-backup"
LOG_FILE="/var/log/awareness-deployment.log"
MAX_RETRIES=5
RETRY_DELAY=10
DOCKER_COMPOSE_FILE="docker-compose.prod.ghcr.yml"

# Function to log messages
log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to handle errors
error_exit() {
    log "${RED}ERROR: $1${NC}"
    rollback
    exit 1
}

# Function to create backup
create_backup() {
    log "${YELLOW}Creating backup...${NC}"
    
    # Backup current deployment
    if [ -d "$DEPLOYMENT_DIR" ]; then
        sudo rm -rf "$BACKUP_DIR"
        sudo cp -r "$DEPLOYMENT_DIR" "$BACKUP_DIR"
        
        # Backup database
        if sudo docker compose -f "$DEPLOYMENT_DIR/$DOCKER_COMPOSE_FILE" ps | grep -q postgres; then
            sudo docker compose -f "$DEPLOYMENT_DIR/$DOCKER_COMPOSE_FILE" exec -T postgres \
                pg_dump -U awareness_user awareness_platform > "$BACKUP_DIR/database_backup.sql" || \
                log "${YELLOW}Warning: Database backup failed${NC}"
        fi
        
        log "${GREEN}Backup created successfully${NC}"
    else
        log "${YELLOW}No existing deployment found, skipping backup${NC}"
    fi
}

# Function to rollback deployment
rollback() {
    log "${YELLOW}Rolling back deployment...${NC}"
    
    if [ -d "$BACKUP_DIR" ]; then
        # Stop current containers
        cd "$DEPLOYMENT_DIR" || true
        sudo docker compose down || true
        
        # Restore backup
        sudo rm -rf "$DEPLOYMENT_DIR"
        sudo cp -r "$BACKUP_DIR" "$DEPLOYMENT_DIR"
        
        # Start previous version
        cd "$DEPLOYMENT_DIR"
        sudo docker compose up -d
        
        # Restore database if backup exists
        if [ -f "$BACKUP_DIR/database_backup.sql" ]; then
            sleep 10
            sudo docker compose exec -T postgres \
                psql -U awareness_user awareness_platform < "$BACKUP_DIR/database_backup.sql" || \
                log "${YELLOW}Warning: Database restore failed${NC}"
        fi
        
        log "${GREEN}Rollback completed${NC}"
    else
        log "${RED}No backup found for rollback${NC}"
    fi
}

# Function to perform health check
health_check() {
    local url=$1
    local max_retries=${2:-$MAX_RETRIES}
    
    for i in $(seq 1 "$max_retries"); do
        log "Health check attempt $i/$max_retries for $url"
        
        response=$(curl -s -o /dev/null -w "%{http_code}" "$url" || echo "000")
        
        if [ "$response" -eq 200 ]; then
            log "${GREEN}Health check passed${NC}"
            return 0
        else
            log "Health check failed with status $response"
            
            if [ "$i" -lt "$max_retries" ]; then
                log "Retrying in $RETRY_DELAY seconds..."
                sleep "$RETRY_DELAY"
            fi
        fi
    done
    
    return 1
}

# Function to verify deployment
verify_deployment() {
    log "${YELLOW}Verifying deployment...${NC}"
    
    # Check if containers are running
    local containers=("backend" "frontend" "postgres" "redis")
    for container in "${containers[@]}"; do
        if ! sudo docker compose -f "$DOCKER_COMPOSE_FILE" ps | grep -q "$container.*Up"; then
            error_exit "Container $container is not running"
        fi
    done
    
    # Check API health
    if ! health_check "http://localhost:8000/api/health"; then
        error_exit "Backend health check failed"
    fi
    
    # Check frontend
    if ! health_check "http://localhost:3000" 3; then
        log "${YELLOW}Warning: Frontend health check failed, but continuing${NC}"
    fi
    
    # Check database connectivity
    if ! sudo docker compose -f "$DOCKER_COMPOSE_FILE" exec -T backend python -c "
from sqlalchemy import create_engine
import os
engine = create_engine(os.environ['DATABASE_URL'])
engine.connect()
print('Database connection successful')
    "; then
        error_exit "Database connectivity check failed"
    fi
    
    log "${GREEN}Deployment verification successful${NC}"
}

# Main deployment function
main() {
    log "${GREEN}Starting deployment process...${NC}"
    
    # Create backup
    create_backup
    
    # Navigate to deployment directory
    cd "$DEPLOYMENT_DIR" || error_exit "Failed to navigate to deployment directory"
    
    # Stop existing containers
    log "${YELLOW}Stopping existing containers...${NC}"
    sudo docker compose -f "$DOCKER_COMPOSE_FILE" down || log "${YELLOW}No existing containers to stop${NC}"
    
    # Pull latest images
    log "${YELLOW}Pulling latest Docker images...${NC}"
    if ! sudo docker compose -f "$DOCKER_COMPOSE_FILE" pull; then
        error_exit "Failed to pull Docker images"
    fi
    
    # Start new containers
    log "${YELLOW}Starting new containers...${NC}"
    if ! sudo docker compose -f "$DOCKER_COMPOSE_FILE" up -d; then
        error_exit "Failed to start containers"
    fi
    
    # Wait for services to be ready
    log "${YELLOW}Waiting for services to initialize...${NC}"
    sleep 30
    
    # Run database migrations
    log "${YELLOW}Running database migrations...${NC}"
    if ! sudo docker compose -f "$DOCKER_COMPOSE_FILE" exec -T backend alembic upgrade head; then
        error_exit "Database migration failed"
    fi
    
    # Create superuser if needed
    log "${YELLOW}Creating superuser...${NC}"
    sudo docker compose -f "$DOCKER_COMPOSE_FILE" exec -T backend python scripts/create_superuser.py || \
        log "${YELLOW}Superuser creation skipped (may already exist)${NC}"
    
    # Verify deployment
    verify_deployment
    
    # Clean up old images
    log "${YELLOW}Cleaning up old Docker images...${NC}"
    sudo docker image prune -f
    
    # Remove backup after successful deployment
    sudo rm -rf "$BACKUP_DIR"
    
    log "${GREEN}Deployment completed successfully!${NC}"
}

# Execute main function
main "$@"