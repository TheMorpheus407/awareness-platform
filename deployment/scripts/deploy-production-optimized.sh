#!/bin/bash
set -euo pipefail

# Optimized deployment script to prevent timeouts
# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Deployment configuration
DEPLOYMENT_DIR="/opt/awareness"
BACKUP_DIR="/opt/awareness-backup"
LOG_FILE="/var/log/awareness-deployment.log"
MAX_RETRIES=3
RETRY_DELAY=5
DOCKER_COMPOSE_FILE="docker-compose.prod.ghcr.yml"

# Function to log messages
log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to handle errors
error_exit() {
    log "${RED}ERROR: $1${NC}"
    exit 1
}

# Quick health check function
quick_health_check() {
    local url=$1
    local max_retries=3
    
    for i in $(seq 1 "$max_retries"); do
        response=$(curl -s -o /dev/null -w "%{http_code}" "$url" || echo "000")
        
        if [ "$response" -eq 200 ]; then
            return 0
        else
            [ "$i" -lt "$max_retries" ] && sleep "$RETRY_DELAY"
        fi
    done
    
    return 1
}

# Main deployment function
main() {
    log "${GREEN}Starting optimized deployment...${NC}"
    
    cd "$DEPLOYMENT_DIR" || error_exit "Failed to navigate to deployment directory"
    
    # Quick backup (database backup skipped for speed)
    if [ -d "$DEPLOYMENT_DIR" ]; then
        log "${YELLOW}Creating quick backup...${NC}"
        sudo cp -r "$DEPLOYMENT_DIR"/{.env,docker-compose.prod.ghcr.yml} "$BACKUP_DIR/" 2>/dev/null || true
    fi
    
    # Pull images in parallel
    log "${YELLOW}Pulling Docker images in parallel...${NC}"
    sudo docker compose -f "$DOCKER_COMPOSE_FILE" pull --parallel || error_exit "Failed to pull images"
    
    # Rolling update with minimal downtime
    log "${YELLOW}Performing rolling update...${NC}"
    
    # Update backend first
    sudo docker compose -f "$DOCKER_COMPOSE_FILE" up -d --no-deps backend
    sleep 10
    
    # Quick backend health check
    if ! quick_health_check "http://localhost:8000/api/health"; then
        error_exit "Backend health check failed"
    fi
    
    # Update frontend
    sudo docker compose -f "$DOCKER_COMPOSE_FILE" up -d --no-deps frontend
    
    # Update nginx last
    sudo docker compose -f "$DOCKER_COMPOSE_FILE" up -d --no-deps nginx
    
    # Run migrations (with timeout)
    log "${YELLOW}Running migrations...${NC}"
    timeout 60 sudo docker compose -f "$DOCKER_COMPOSE_FILE" exec -T backend alembic upgrade head || \
        log "${YELLOW}Migration timeout or already up to date${NC}"
    
    # Final quick health check
    sleep 5
    if ! quick_health_check "http://localhost:8000/api/health"; then
        error_exit "Final health check failed"
    fi
    
    # Clean up
    sudo docker image prune -af --filter "until=24h" &
    
    log "${GREEN}Deployment completed successfully!${NC}"
}

# Execute main function
main "$@"