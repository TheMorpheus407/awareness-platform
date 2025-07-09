#!/bin/bash

# Emergency Production Fix - Quick Recovery
# For immediate issues when the site is down

set -e

SERVER="ubuntu@83.228.205.20"
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${RED}EMERGENCY PRODUCTION FIX${NC}"
echo "This will quickly restore services using the latest images"
echo ""

# Quick fix commands
ssh -o StrictHostKeyChecking=no "$SERVER" << 'EOF'
cd /opt/awareness

echo "1. Stopping all services..."
docker-compose down

echo "2. Removing problematic files..."
rm -f docker-compose.prod*.yml

echo "3. Creating minimal docker-compose.yml..."
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
    restart: always

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
      - postgres
    restart: always

  frontend:
    image: ghcr.io/cyberawareschool/awareness-schulungen-frontend:latest
    ports:
      - "3000:80"
    environment:
      REACT_APP_API_URL: https://awareness-schulungen.de/api
    depends_on:
      - backend
    restart: always

volumes:
  postgres_data:
COMPOSE

echo "4. Pulling latest images..."
docker pull ghcr.io/cyberawareschool/awareness-schulungen-backend:latest
docker pull ghcr.io/cyberawareschool/awareness-schulungen-frontend:latest

echo "5. Starting services..."
docker-compose up -d

echo "6. Waiting for services to start..."
sleep 20

echo "7. Checking status..."
docker-compose ps

echo "Emergency fix completed!"
EOF

# Quick verification
echo -e "\n${YELLOW}Verifying...${NC}"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://awareness-schulungen.de || echo "000")

if [ "$STATUS" = "200" ]; then
    echo -e "${GREEN}✓ Website is back online!${NC}"
else
    echo -e "${RED}✗ Website still not accessible (HTTP $STATUS)${NC}"
    echo "Check logs with: ssh $SERVER 'cd /opt/awareness && docker-compose logs'"
fi