#!/bin/bash
set -euo pipefail

# Enhanced deployment script with proper backend structure handling
# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Deployment configuration
DEPLOYMENT_DIR="/opt/awareness"
BACKUP_DIR="/opt/awareness-backup-$(date +%Y%m%d-%H%M%S)"
LOG_FILE="/var/log/awareness-deployment-$(date +%Y%m%d-%H%M%S).log"
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

# Function to check service health
check_health() {
    local service=$1
    local url=$2
    local max_retries=10
    local retry_delay=5
    
    log "${BLUE}Checking health of $service...${NC}"
    
    for i in $(seq 1 "$max_retries"); do
        response=$(curl -s -o /dev/null -w "%{http_code}" "$url" || echo "000")
        
        if [ "$response" -eq 200 ]; then
            log "${GREEN}✅ $service is healthy${NC}"
            return 0
        else
            log "${YELLOW}$service returned status: $response (attempt $i/$max_retries)${NC}"
            [ "$i" -lt "$max_retries" ] && sleep "$retry_delay"
        fi
    done
    
    return 1
}

# Function to verify container is running
verify_container() {
    local container_name=$1
    
    if docker ps --format "table {{.Names}}" | grep -q "$container_name"; then
        log "${GREEN}✅ Container $container_name is running${NC}"
        return 0
    else
        log "${RED}❌ Container $container_name is not running${NC}"
        return 1
    fi
}

# Main deployment function
main() {
    log "${GREEN}========================================${NC}"
    log "${GREEN}Starting Enhanced Deployment Process${NC}"
    log "${GREEN}========================================${NC}"
    
    # Verify we're in the correct directory
    cd "$DEPLOYMENT_DIR" || error_exit "Failed to navigate to deployment directory"
    
    # Create backup
    log "${YELLOW}Creating backup...${NC}"
    if [ -d "$DEPLOYMENT_DIR" ]; then
        sudo mkdir -p "$BACKUP_DIR"
        sudo cp -r "$DEPLOYMENT_DIR"/{.env*,docker-compose*.yml,nginx,scripts} "$BACKUP_DIR/" 2>/dev/null || true
        
        # Backup database
        if docker ps --format "table {{.Names}}" | grep -q "postgres"; then
            log "${YELLOW}Backing up database...${NC}"
            docker exec awareness-postgres-1 pg_dump -U awareness_user awareness_platform > "$BACKUP_DIR/database_backup.sql" || \
                log "${YELLOW}Database backup skipped or failed (non-critical)${NC}"
        fi
    fi
    
    # Verify Docker Compose file exists
    if [ ! -f "$DOCKER_COMPOSE_FILE" ]; then
        error_exit "Docker Compose file not found: $DOCKER_COMPOSE_FILE"
    fi
    
    # Pull new images
    log "${YELLOW}Pulling new Docker images...${NC}"
    docker compose -f "$DOCKER_COMPOSE_FILE" pull || error_exit "Failed to pull images"
    
    # Check if backend image has correct structure
    log "${BLUE}Verifying backend image structure...${NC}"
    docker run --rm "$REGISTRY/$IMAGE_NAME/backend:latest" ls -la /app/ || \
        log "${YELLOW}Could not verify backend structure${NC}"
    
    # Stop old containers gracefully
    log "${YELLOW}Stopping old containers...${NC}"
    docker compose -f "$DOCKER_COMPOSE_FILE" down --remove-orphans || true
    
    # Start database and Redis first
    log "${YELLOW}Starting infrastructure services...${NC}"
    docker compose -f "$DOCKER_COMPOSE_FILE" up -d postgres redis
    
    # Wait for database to be ready
    log "${BLUE}Waiting for database to be ready...${NC}"
    sleep 15
    
    # Start backend
    log "${YELLOW}Starting backend service...${NC}"
    docker compose -f "$DOCKER_COMPOSE_FILE" up -d backend
    
    # Wait for backend to be ready
    sleep 20
    
    # Verify backend is healthy
    if ! check_health "Backend API" "http://localhost:8000/api/health"; then
        log "${RED}Backend health check failed!${NC}"
        log "${YELLOW}Checking backend logs...${NC}"
        docker compose -f "$DOCKER_COMPOSE_FILE" logs --tail=50 backend
        error_exit "Backend failed to start properly"
    fi
    
    # Run database migrations
    log "${YELLOW}Running database migrations...${NC}"
    docker compose -f "$DOCKER_COMPOSE_FILE" exec -T backend alembic upgrade head || \
        log "${YELLOW}Migrations may have already been applied${NC}"
    
    # Create admin user if needed
    log "${YELLOW}Ensuring admin user exists...${NC}"
    docker compose -f "$DOCKER_COMPOSE_FILE" exec -T backend python /app/scripts/create_production_admin.py || \
        log "${YELLOW}Admin user creation skipped (may already exist)${NC}"
    
    # Start frontend
    log "${YELLOW}Starting frontend service...${NC}"
    docker compose -f "$DOCKER_COMPOSE_FILE" up -d frontend
    
    # Start nginx
    log "${YELLOW}Starting nginx service...${NC}"
    docker compose -f "$DOCKER_COMPOSE_FILE" up -d nginx
    
    # Wait for all services to stabilize
    sleep 10
    
    # Verify all containers are running
    log "${BLUE}Verifying container status...${NC}"
    verify_container "awareness-postgres-1" || error_exit "PostgreSQL container not running"
    verify_container "awareness-redis-1" || error_exit "Redis container not running"
    verify_container "awareness-backend-1" || error_exit "Backend container not running"
    verify_container "awareness-frontend-1" || error_exit "Frontend container not running"
    verify_container "awareness-nginx-1" || error_exit "Nginx container not running"
    
    # Final health checks
    log "${BLUE}Running final health checks...${NC}"
    check_health "Backend API" "http://localhost:8000/api/health" || error_exit "Backend final health check failed"
    check_health "Frontend (via nginx)" "http://localhost" || log "${YELLOW}Frontend check via localhost failed (may be normal)${NC}"
    
    # Check external URL if available
    if command -v curl &> /dev/null; then
        check_health "Production Site" "https://bootstrap-awareness.de/api/health" || \
            log "${YELLOW}External health check failed (DNS/SSL may need time)${NC}"
    fi
    
    # Show final status
    log "${BLUE}Deployment Status:${NC}"
    docker compose -f "$DOCKER_COMPOSE_FILE" ps
    
    # Clean up old images
    log "${YELLOW}Cleaning up old Docker images...${NC}"
    docker image prune -af --filter "until=48h" || true
    
    # Success!
    log "${GREEN}========================================${NC}"
    log "${GREEN}✅ Deployment completed successfully!${NC}"
    log "${GREEN}========================================${NC}"
    
    # Show important URLs
    log "${BLUE}Access URLs:${NC}"
    log "  - Frontend: https://bootstrap-awareness.de"
    log "  - API: https://bootstrap-awareness.de/api"
    log "  - Health: https://bootstrap-awareness.de/api/health"
    
    # Show logs location
    log "${BLUE}Logs saved to: $LOG_FILE${NC}"
}

# Execute main function with error handling
if main "$@"; then
    exit 0
else
    log "${RED}Deployment failed! Check logs at: $LOG_FILE${NC}"
    exit 1
fi