#!/bin/bash
# Deployment verification script

set -e

echo "=== Deployment Verification Script ==="
echo "This script checks if all critical components are working correctly"
echo

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if a service is running
check_service() {
    local service=$1
    local port=$2
    local description=$3
    
    echo -n "Checking $description... "
    
    if nc -z localhost $port 2>/dev/null; then
        echo -e "${GREEN}✓ Running on port $port${NC}"
        return 0
    else
        echo -e "${RED}✗ Not accessible on port $port${NC}"
        return 1
    fi
}

# Function to check HTTP endpoint
check_http_endpoint() {
    local url=$1
    local description=$2
    
    echo -n "Checking $description... "
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" || echo "000")
    
    if [ "$response" = "200" ]; then
        echo -e "${GREEN}✓ OK (200)${NC}"
        return 0
    elif [ "$response" = "000" ]; then
        echo -e "${RED}✗ Connection failed${NC}"
        return 1
    else
        echo -e "${YELLOW}⚠ Status $response${NC}"
        return 1
    fi
}

# Function to check database
check_database() {
    echo -n "Checking database connection... "
    
    if docker-compose exec -T db pg_isready -U postgres >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Database is ready${NC}"
        
        # Check if tables exist
        echo -n "Checking database tables... "
        table_count=$(docker-compose exec -T db psql -U postgres -d awareness_platform -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'" 2>/dev/null | xargs || echo "0")
        
        if [ "$table_count" -gt "0" ]; then
            echo -e "${GREEN}✓ $table_count tables found${NC}"
        else
            echo -e "${RED}✗ No tables found${NC}"
        fi
    else
        echo -e "${RED}✗ Database not accessible${NC}"
    fi
}

echo "1. Checking Services"
echo "==================="
check_service "PostgreSQL" 5432 "PostgreSQL Database"
check_service "Redis" 6379 "Redis Cache"
check_service "Backend API" 8000 "Backend API"
check_service "Frontend/Nginx" 80 "Frontend (Nginx)"

echo
echo "2. Checking API Endpoints"
echo "========================"
check_http_endpoint "http://localhost:8000/" "API Root"
check_http_endpoint "http://localhost:8000/api/v1/health" "API Health"
check_http_endpoint "http://localhost:8000/api/v1/health/db" "Database Health"
check_http_endpoint "http://localhost:8000/api/v1/debug/info" "Debug Info"
check_http_endpoint "http://localhost:8000/api/v1/auth/login" "Auth Login Endpoint"

echo
echo "3. Checking Frontend"
echo "==================="
check_http_endpoint "http://localhost/" "Frontend Root"
check_http_endpoint "http://localhost/login" "Login Page"
check_http_endpoint "http://localhost/register" "Register Page"

echo
echo "4. Checking Database"
echo "==================="
check_database

echo
echo "5. Checking Docker Containers"
echo "============================"
echo "Running containers:"
docker-compose ps

echo
echo "6. Recent Logs"
echo "=============="
echo "Last 10 lines of backend logs:"
docker-compose logs --tail=10 backend 2>/dev/null || echo "Could not fetch backend logs"

echo
echo "=== Verification Complete ==="
echo
echo "To debug issues:"
echo "1. Check full logs: docker-compose logs [service]"
echo "2. Check API routes: curl http://localhost:8000/api/v1/debug/routes"
echo "3. Check database: docker-compose exec db psql -U postgres -d awareness_platform"
echo "4. Restart services: docker-compose restart"