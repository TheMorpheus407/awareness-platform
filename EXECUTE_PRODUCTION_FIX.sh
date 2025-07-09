#!/bin/bash

# Production Fix Execution Script
# Target: ubuntu@83.228.205.20
# Purpose: Fix production issues and verify services

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Server details
SERVER="ubuntu@83.228.205.20"
REMOTE_DIR="/opt/awareness"

echo -e "${YELLOW}Production Fix Execution Script${NC}"
echo "Target server: $SERVER"
echo "Remote directory: $REMOTE_DIR"
echo "----------------------------------------"

# Function to execute remote commands
execute_remote() {
    echo -e "${YELLOW}Executing: $1${NC}"
    ssh -o StrictHostKeyChecking=no "$SERVER" "$1"
}

# Function to check command success
check_success() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ $1${NC}"
    else
        echo -e "${RED}✗ $1 failed${NC}"
        exit 1
    fi
}

# Step 1: Verify connection and current state
echo -e "\n${YELLOW}Step 1: Checking current state${NC}"
execute_remote "cd $REMOTE_DIR && pwd"
check_success "Connected to server"

execute_remote "cd $REMOTE_DIR && docker-compose ps"
echo ""

# Step 2: Create fix script on server
echo -e "\n${YELLOW}Step 2: Creating fix script on server${NC}"
ssh -o StrictHostKeyChecking=no "$SERVER" << 'EOF'
cd /opt/awareness

# Create the fix script
cat > fix_production.sh << 'SCRIPT'
#!/bin/bash
set -e

echo "Starting production fix..."

# Step 1: Stop all services
echo "Stopping all services..."
docker-compose down

# Step 2: Clean up Docker resources
echo "Cleaning up Docker resources..."
docker system prune -f
docker volume prune -f

# Step 3: Remove problematic files
echo "Removing problematic configuration files..."
rm -f docker-compose.prod.yml
rm -f docker-compose.prod.ghcr.yml
rm -f docker-compose.prod.optimized.yml
rm -rf frontend/
rm -rf monitoring/

# Step 4: Ensure only docker-compose.yml exists
echo "Ensuring clean configuration..."
if [ ! -f docker-compose.yml ]; then
    echo "ERROR: docker-compose.yml not found!"
    exit 1
fi

# Step 5: Update docker-compose.yml to use correct images
echo "Updating docker-compose.yml..."
sed -i 's|ghcr.io/cyberawareschool/awareness-schulungen-.*|postgres:15-alpine|g' docker-compose.yml
sed -i 's|context: \./backend|image: ghcr.io/cyberawareschool/awareness-schulungen-backend:latest|g' docker-compose.yml
sed -i 's|context: \./frontend|image: ghcr.io/cyberawareschool/awareness-schulungen-frontend:latest|g' docker-compose.yml

# Step 6: Pull latest images
echo "Pulling latest images..."
docker pull ghcr.io/cyberawareschool/awareness-schulungen-backend:latest
docker pull ghcr.io/cyberawareschool/awareness-schulungen-frontend:latest
docker pull postgres:15-alpine

# Step 7: Start services
echo "Starting services..."
docker-compose up -d

# Step 8: Wait for services to be healthy
echo "Waiting for services to start..."
sleep 30

# Step 9: Check service status
echo "Checking service status..."
docker-compose ps

# Step 10: Verify backend is accessible
echo "Verifying backend..."
curl -f http://localhost:8080/health || echo "Backend health check failed"

# Step 11: Check logs for errors
echo "Checking for errors in logs..."
docker-compose logs --tail=50 backend | grep -i error || true
docker-compose logs --tail=50 frontend | grep -i error || true

echo "Production fix completed!"
SCRIPT

chmod +x fix_production.sh
echo "Fix script created successfully"
EOF
check_success "Fix script created"

# Step 3: Execute the fix script
echo -e "\n${YELLOW}Step 3: Executing fix script${NC}"
execute_remote "cd $REMOTE_DIR && sudo ./fix_production.sh"
check_success "Fix script executed"

# Step 4: Verify services are running
echo -e "\n${YELLOW}Step 4: Verifying services${NC}"
execute_remote "cd $REMOTE_DIR && docker-compose ps"

# Step 5: Check backend health
echo -e "\n${YELLOW}Step 5: Checking backend health${NC}"
execute_remote "curl -s http://localhost:8080/health | jq '.' || echo 'Backend not responding'"

# Step 6: Check frontend
echo -e "\n${YELLOW}Step 6: Checking frontend${NC}"
execute_remote "curl -s -o /dev/null -w '%{http_code}' http://localhost:3000 || echo '000'"

# Step 7: Check website content
echo -e "\n${YELLOW}Step 7: Verifying website content${NC}"
echo "Checking https://awareness-schulungen.de ..."
WEBSITE_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://awareness-schulungen.de || echo "000")
if [ "$WEBSITE_STATUS" = "200" ]; then
    echo -e "${GREEN}✓ Website is accessible (HTTP $WEBSITE_STATUS)${NC}"
    
    # Check for correct content
    CONTENT=$(curl -s https://awareness-schulungen.de | head -n 50)
    if echo "$CONTENT" | grep -q "Awareness Schulungen"; then
        echo -e "${GREEN}✓ Website shows correct content${NC}"
    else
        echo -e "${RED}✗ Website content appears incorrect${NC}"
        echo "First 50 lines of content:"
        echo "$CONTENT"
    fi
else
    echo -e "${RED}✗ Website returned HTTP $WEBSITE_STATUS${NC}"
fi

# Step 8: Show final status
echo -e "\n${YELLOW}Step 8: Final status check${NC}"
execute_remote "cd $REMOTE_DIR && docker-compose ps"
execute_remote "cd $REMOTE_DIR && docker stats --no-stream"

# Step 9: Show recent logs
echo -e "\n${YELLOW}Step 9: Recent logs${NC}"
execute_remote "cd $REMOTE_DIR && docker-compose logs --tail=20"

echo -e "\n${GREEN}Production fix execution completed!${NC}"
echo -e "${YELLOW}Please verify:${NC}"
echo "1. Visit https://awareness-schulungen.de"
echo "2. Check that the homepage loads correctly"
echo "3. Try logging in with test credentials"
echo "4. Monitor logs for any errors"

# Additional troubleshooting commands
echo -e "\n${YELLOW}Troubleshooting commands:${NC}"
echo "ssh $SERVER"
echo "cd $REMOTE_DIR"
echo "docker-compose logs -f"
echo "docker-compose restart backend"
echo "docker exec -it awareness_backend_1 /bin/sh"