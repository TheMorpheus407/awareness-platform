#!/bin/bash

# Safe Production Fix Execution Script with Rollback
# Target: ubuntu@83.228.205.20
# Purpose: Fix production issues with safety checks and rollback capability

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Server details
SERVER="ubuntu@83.228.205.20"
REMOTE_DIR="/opt/awareness"
BACKUP_DIR="/opt/awareness_backup_$(date +%Y%m%d_%H%M%S)"

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Production Fix Execution (Safe Mode)  ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo -e "Target server: ${YELLOW}$SERVER${NC}"
echo -e "Remote directory: ${YELLOW}$REMOTE_DIR${NC}"
echo -e "Backup directory: ${YELLOW}$BACKUP_DIR${NC}"
echo ""

# Function to execute remote commands
execute_remote() {
    ssh -o StrictHostKeyChecking=no "$SERVER" "$1"
}

# Function to check command success
check_success() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ $1${NC}"
        return 0
    else
        echo -e "${RED}✗ $1 failed${NC}"
        return 1
    fi
}

# Function to create backup
create_backup() {
    echo -e "\n${YELLOW}Creating backup...${NC}"
    execute_remote "sudo cp -r $REMOTE_DIR $BACKUP_DIR"
    check_success "Backup created at $BACKUP_DIR"
}

# Function to rollback
rollback() {
    echo -e "\n${RED}Rolling back changes...${NC}"
    execute_remote "cd $REMOTE_DIR && docker-compose down"
    execute_remote "sudo rm -rf $REMOTE_DIR && sudo mv $BACKUP_DIR $REMOTE_DIR"
    execute_remote "cd $REMOTE_DIR && docker-compose up -d"
    echo -e "${YELLOW}Rollback completed. Please check services manually.${NC}"
}

# Confirmation prompt
echo -e "${YELLOW}This script will:${NC}"
echo "1. Create a backup of the current state"
echo "2. Stop all Docker services"
echo "3. Clean up Docker resources"
echo "4. Fix configuration files"
echo "5. Restart services with correct images"
echo ""
read -p "Are you sure you want to proceed? (yes/no): " -r
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo -e "${RED}Operation cancelled.${NC}"
    exit 1
fi

# Step 1: Check current state and create backup
echo -e "\n${BLUE}═══ Step 1: Checking current state ═══${NC}"
execute_remote "cd $REMOTE_DIR && pwd"
check_success "Connected to server"

echo -e "\nCurrent services:"
execute_remote "cd $REMOTE_DIR && docker-compose ps"

create_backup

# Step 2: Create and execute fix script
echo -e "\n${BLUE}═══ Step 2: Creating fix script ═══${NC}"
ssh -o StrictHostKeyChecking=no "$SERVER" << 'EOF'
cd /opt/awareness

# Create comprehensive fix script
cat > fix_production_safe.sh << 'SCRIPT'
#!/bin/bash
set -e

echo "Starting safe production fix..."

# Function to check if service is healthy
check_service() {
    local service=$1
    local port=$2
    local max_attempts=30
    local attempt=0
    
    echo "Waiting for $service to be healthy..."
    while [ $attempt -lt $max_attempts ]; do
        if curl -f -s http://localhost:$port/health > /dev/null 2>&1; then
            echo "✓ $service is healthy"
            return 0
        fi
        attempt=$((attempt + 1))
        echo "Waiting for $service... ($attempt/$max_attempts)"
        sleep 2
    done
    echo "✗ $service failed to become healthy"
    return 1
}

# Stop services gracefully
echo "Stopping services gracefully..."
docker-compose stop
sleep 5
docker-compose down

# Clean up Docker resources
echo "Cleaning up Docker resources..."
docker system prune -af --volumes

# Remove problematic files
echo "Removing problematic files..."
rm -f docker-compose.prod*.yml
rm -rf frontend/ monitoring/

# Ensure docker-compose.yml is correct
echo "Fixing docker-compose.yml..."
if [ ! -f docker-compose.yml ]; then
    echo "Creating docker-compose.yml..."
    cat > docker-compose.yml << 'COMPOSE'
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: awareness_user
      POSTGRES_PASSWORD: supersecurepassword123
      POSTGRES_DB: awareness_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U awareness_user"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  backend:
    image: ghcr.io/cyberawareschool/awareness-schulungen-backend:latest
    ports:
      - "8080:8000"
    environment:
      DATABASE_URL: postgresql://awareness_user:supersecurepassword123@postgres:5432/awareness_db
      SECRET_KEY: your-secret-key-here
      ENVIRONMENT: production
      CORS_ORIGINS: https://awareness-schulungen.de,https://www.awareness-schulungen.de
    depends_on:
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  frontend:
    image: ghcr.io/cyberawareschool/awareness-schulungen-frontend:latest
    ports:
      - "3000:80"
    environment:
      REACT_APP_API_URL: https://awareness-schulungen.de/api
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  postgres_data:

networks:
  default:
    name: awareness_network
COMPOSE
fi

# Pull latest images
echo "Pulling latest images..."
docker pull ghcr.io/cyberawareschool/awareness-schulungen-backend:latest
docker pull ghcr.io/cyberawareschool/awareness-schulungen-frontend:latest
docker pull postgres:15-alpine

# Start database first
echo "Starting database..."
docker-compose up -d postgres
sleep 10

# Start backend
echo "Starting backend..."
docker-compose up -d backend
check_service "backend" "8080"

# Start frontend
echo "Starting frontend..."
docker-compose up -d frontend
sleep 5

# Final verification
echo "Verifying all services..."
docker-compose ps

echo "Safe production fix completed!"
SCRIPT

chmod +x fix_production_safe.sh
EOF

check_success "Fix script created" || { rollback; exit 1; }

# Step 3: Execute fix script
echo -e "\n${BLUE}═══ Step 3: Executing fix ═══${NC}"
if ! execute_remote "cd $REMOTE_DIR && sudo ./fix_production_safe.sh"; then
    echo -e "${RED}Fix script failed! Starting rollback...${NC}"
    rollback
    exit 1
fi

# Step 4: Comprehensive verification
echo -e "\n${BLUE}═══ Step 4: Verification ═══${NC}"

# Check Docker services
echo -e "\n${YELLOW}Docker services status:${NC}"
execute_remote "cd $REMOTE_DIR && docker-compose ps"

# Check backend health
echo -e "\n${YELLOW}Backend health check:${NC}"
BACKEND_HEALTH=$(execute_remote "curl -s http://localhost:8080/health" || echo "{}")
echo "$BACKEND_HEALTH" | jq '.' 2>/dev/null || echo "$BACKEND_HEALTH"

# Check frontend
echo -e "\n${YELLOW}Frontend check:${NC}"
FRONTEND_STATUS=$(execute_remote "curl -s -o /dev/null -w '%{http_code}' http://localhost:3000" || echo "000")
echo "Frontend HTTP status: $FRONTEND_STATUS"

# Check website
echo -e "\n${YELLOW}Website verification:${NC}"
WEBSITE_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://awareness-schulungen.de || echo "000")
echo "Website HTTP status: $WEBSITE_STATUS"

if [ "$WEBSITE_STATUS" = "200" ]; then
    echo -e "${GREEN}✓ Website is accessible${NC}"
    
    # Check content
    if curl -s https://awareness-schulungen.de | grep -q "Awareness Schulungen"; then
        echo -e "${GREEN}✓ Website content verified${NC}"
    else
        echo -e "${RED}✗ Website content may be incorrect${NC}"
    fi
else
    echo -e "${RED}✗ Website is not accessible (HTTP $WEBSITE_STATUS)${NC}"
    echo -e "${YELLOW}Consider rolling back with:${NC}"
    echo "ssh $SERVER 'cd /opt/awareness && docker-compose down && sudo rm -rf /opt/awareness && sudo mv $BACKUP_DIR /opt/awareness && cd /opt/awareness && docker-compose up -d'"
fi

# Step 5: Resource usage
echo -e "\n${BLUE}═══ Step 5: Resource Usage ═══${NC}"
execute_remote "docker stats --no-stream"

# Step 6: Recent logs
echo -e "\n${BLUE}═══ Step 6: Recent Logs ═══${NC}"
execute_remote "cd $REMOTE_DIR && docker-compose logs --tail=10"

# Summary
echo -e "\n${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║           Execution Summary            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"

if [ "$WEBSITE_STATUS" = "200" ]; then
    echo -e "${GREEN}✓ Fix executed successfully${NC}"
    echo -e "${GREEN}✓ Website is accessible${NC}"
    echo -e "${YELLOW}Backup saved at: $BACKUP_DIR${NC}"
else
    echo -e "${RED}⚠ Fix executed but website may have issues${NC}"
    echo -e "${YELLOW}Backup available at: $BACKUP_DIR${NC}"
fi

echo -e "\n${YELLOW}Next steps:${NC}"
echo "1. Visit https://awareness-schulungen.de"
echo "2. Test login functionality"
echo "3. Monitor logs: ssh $SERVER 'cd $REMOTE_DIR && docker-compose logs -f'"
echo "4. Check metrics: ssh $SERVER 'docker stats'"

echo -e "\n${YELLOW}Useful commands:${NC}"
echo "• Rollback: ssh $SERVER 'cd /opt/awareness && docker-compose down && sudo rm -rf /opt/awareness && sudo mv $BACKUP_DIR /opt/awareness && cd /opt/awareness && docker-compose up -d'"
echo "• Logs: ssh $SERVER 'cd $REMOTE_DIR && docker-compose logs -f'"
echo "• Restart: ssh $SERVER 'cd $REMOTE_DIR && docker-compose restart'"
echo "• Shell: ssh $SERVER 'docker exec -it awareness-backend-1 /bin/sh'"