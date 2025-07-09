#!/bin/bash
# Script to fix backend structure issues on production server

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "${GREEN}Fixing backend structure issues...${NC}"

# Navigate to deployment directory
cd /opt/awareness || exit 1

# Check current container status
log "${BLUE}Current container status:${NC}"
docker-compose ps

# Check if backend is failing
if ! docker-compose ps | grep -q "awareness-backend.*Up"; then
    log "${YELLOW}Backend container is not running properly${NC}"
    
    # Check logs
    log "${BLUE}Backend logs:${NC}"
    docker-compose logs --tail=50 backend
    
    # Stop backend
    docker-compose stop backend
    docker-compose rm -f backend
    
    # Pull latest image
    log "${YELLOW}Pulling latest backend image...${NC}"
    docker-compose pull backend
    
    # Check image structure
    log "${BLUE}Checking backend image structure:${NC}"
    docker run --rm ghcr.io/themorpheus407/awareness-platform/backend:latest ls -la /app/ || true
    
    # Start backend with proper environment
    log "${YELLOW}Starting backend with correct configuration...${NC}"
    docker-compose up -d backend
    
    # Wait for startup
    sleep 20
    
    # Check health
    if curl -f http://localhost:8000/api/health; then
        log "${GREEN}✅ Backend is now healthy!${NC}"
    else
        log "${RED}❌ Backend is still unhealthy${NC}"
        docker-compose logs --tail=100 backend
    fi
else
    log "${GREEN}Backend container is running${NC}"
    
    # Just restart to ensure latest configuration
    log "${YELLOW}Restarting backend to ensure latest configuration...${NC}"
    docker-compose restart backend
    
    sleep 20
    
    # Health check
    if curl -f http://localhost:8000/api/health; then
        log "${GREEN}✅ Backend is healthy after restart${NC}"
    else
        log "${RED}❌ Backend health check failed${NC}"
    fi
fi

# Check all services
log "${BLUE}Final service status:${NC}"
docker-compose ps

# Test endpoints
log "${BLUE}Testing endpoints:${NC}"
curl -s http://localhost:8000/api/health | jq '.' || echo "API health check failed"
curl -s http://localhost:8000/api/v1/companies?skip=0&limit=1 | jq '.' || echo "Companies endpoint failed"

log "${GREEN}Fix script completed${NC}"