#!/bin/bash
# Quick fix script for common deployment issues

set -e

echo "=== Deployment Issues Fix Script ==="
echo "This script attempts to fix common deployment issues"
echo

# Function to run a fix
run_fix() {
    local description=$1
    local command=$2
    
    echo -n "→ $description... "
    if eval "$command" >/dev/null 2>&1; then
        echo "✓ Done"
    else
        echo "✗ Failed"
    fi
}

echo "1. Stopping all containers"
docker-compose down

echo
echo "2. Cleaning up"
run_fix "Removing old containers" "docker-compose rm -f"
run_fix "Clearing Docker build cache" "docker system prune -f"

echo
echo "3. Rebuilding images"
run_fix "Building backend image" "docker-compose build backend"
run_fix "Building nginx image" "docker-compose build nginx"

echo
echo "4. Starting services"
run_fix "Starting database" "docker-compose up -d db"
echo "   Waiting for database to be ready..."
sleep 10

run_fix "Starting Redis" "docker-compose up -d redis"
sleep 5

echo
echo "5. Initializing database"
# Run database initialization directly
docker-compose run --rm backend python scripts/init_db_production.py

echo
echo "6. Starting application services"
run_fix "Starting backend" "docker-compose up -d backend"
echo "   Waiting for backend to start..."
sleep 10

run_fix "Starting nginx" "docker-compose up -d nginx"

echo
echo "7. Running verification"
sleep 5
bash scripts/verify_deployment.sh

echo
echo "=== Fix Script Complete ==="
echo
echo "If issues persist:"
echo "1. Check logs: docker-compose logs -f [service]"
echo "2. Rebuild from scratch: docker-compose down -v && docker-compose up --build"
echo "3. Check environment variables in .env files"