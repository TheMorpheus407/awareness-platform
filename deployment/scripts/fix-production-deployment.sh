#!/bin/bash
# Production Fix Script - Fixes the deployment issues
# Run this on the production server as ubuntu user

set -e

echo "🚀 Bootstrap Awareness Production Fix Script"
echo "==========================================="
echo ""

# Configuration
APP_DIR="/opt/awareness"
REGISTRY="ghcr.io"
IMAGE_NAME="themorpheus407/awareness-platform"

echo "📁 Working directory: $APP_DIR"
cd $APP_DIR

echo ""
echo "1. 🔍 Checking current state..."
echo "------------------------------"
docker-compose ps

echo ""
echo "2. 🛠️ Creating fixed docker-compose.yml..."
echo "-----------------------------------------"
cat > docker-compose-fixed.yml << 'EOF'
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    restart: always
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-awareness_platform}
      POSTGRES_USER: ${POSTGRES_USER:-awareness_user}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_INITDB_ARGS: "--encoding=UTF8 --locale=en_US.utf8"
      POSTGRES_HOST_AUTH_METHOD: "scram-sha-256"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-awareness_user}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - backend-network

  redis:
    image: redis:7-alpine
    restart: always
    command: >
      redis-server
      --requirepass ${REDIS_PASSWORD}
      --maxmemory 512mb
      --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - backend-network

  backend:
    image: ${REGISTRY}/${IMAGE_NAME}/backend:${VERSION:-latest}
    restart: always
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    env_file:
      - .env.production
    environment:
      - WORKERS=4
      - MAX_REQUESTS=1000
      - MAX_REQUESTS_JITTER=50
      - TIMEOUT=120
    volumes:
      - uploaded_files:/app/uploads
      - ./logs:/app/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - backend-network
      - frontend-network

  frontend:
    image: ${REGISTRY}/${IMAGE_NAME}/frontend:${VERSION:-latest}
    restart: always
    depends_on:
      - backend
    environment:
      VITE_API_URL: ${VITE_API_URL:-https://bootstrap-awareness.de/api}
      VITE_APP_NAME: ${VITE_APP_NAME:-Bootstrap Awareness Platform}
    networks:
      - frontend-network

  nginx:
    image: nginx:alpine
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx-prod.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/sites-enabled:/etc/nginx/sites-enabled:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro
      - certbot_webroot:/var/www/certbot:ro
      - nginx_cache:/var/cache/nginx
      - nginx_logs:/var/log/nginx
    depends_on:
      - backend
      - frontend
    healthcheck:
      test: ["CMD", "nginx", "-t"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - frontend-network
      - monitoring

  certbot:
    image: certbot/certbot
    restart: unless-stopped
    volumes:
      - /etc/letsencrypt:/etc/letsencrypt
      - certbot_webroot:/var/www/certbot
    entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait $${!}; done;'"
    networks:
      - monitoring

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
  uploaded_files:
    driver: local
  certbot_webroot:
    driver: local
  nginx_cache:
    driver: local
  nginx_logs:
    driver: local

networks:
  backend-network:
    driver: bridge
    internal: true
  frontend-network:
    driver: bridge
  monitoring:
    driver: bridge
EOF

echo "✅ Fixed docker-compose.yml created"

echo ""
echo "3. 🔧 Fixing backend Dockerfile path issue..."
echo "--------------------------------------------"
# The backend was moved to backend/backend/ but the image might not reflect this
# We'll create a custom entrypoint script to handle this

cat > fix-backend-entrypoint.sh << 'EOF'
#!/bin/bash
# Fix backend path issue

# Check if main.py exists in the expected location
if [ -f "/app/backend/main.py" ]; then
    echo "🔧 Detected backend in /app/backend/, adjusting..."
    cd /app/backend
    export PYTHONPATH="/app/backend:$PYTHONPATH"
elif [ -f "/app/main.py" ]; then
    echo "✅ Backend already in correct location"
    cd /app
else
    echo "❌ Cannot find main.py in expected locations!"
    ls -la /app/
    exit 1
fi

# Run the application
exec uvicorn main:app --host 0.0.0.0 --port 8000 --workers ${WORKERS:-4}
EOF

chmod +x fix-backend-entrypoint.sh

echo ""
echo "4. 🔄 Redeploying with fixes..."
echo "--------------------------------"

# Stop current deployment
echo "Stopping current containers..."
docker-compose down

# Use the fixed compose file
mv docker-compose-fixed.yml docker-compose.yml

# Pull latest images
echo "Pulling latest images..."
docker-compose pull

# Start services
echo "Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "Waiting for services to be healthy..."
sleep 30

echo ""
echo "5. 🗄️ Initializing database..."
echo "------------------------------"

# First, let's check if the backend file structure is correct
BACKEND_CONTAINER=$(docker ps -q --filter "name=backend")
if [ -n "$BACKEND_CONTAINER" ]; then
    echo "Checking backend file structure..."
    docker exec $BACKEND_CONTAINER ls -la /app/
    
    # Try to run migrations with the correct path
    echo "Running database migrations..."
    if docker exec $BACKEND_CONTAINER test -f /app/backend/alembic.ini; then
        docker exec $BACKEND_CONTAINER sh -c "cd /app/backend && alembic upgrade head" || echo "⚠️  Migration failed, trying alternative approach..."
    elif docker exec $BACKEND_CONTAINER test -f /app/alembic.ini; then
        docker exec $BACKEND_CONTAINER alembic upgrade head || echo "⚠️  Migration failed"
    else
        echo "❌ Cannot find alembic.ini"
    fi
    
    # Try to create admin user
    echo "Creating admin user..."
    if docker exec $BACKEND_CONTAINER test -f /app/backend/scripts/create_production_admin.py; then
        docker exec $BACKEND_CONTAINER python /app/backend/scripts/create_production_admin.py || true
    elif docker exec $BACKEND_CONTAINER test -f /app/scripts/create_production_admin.py; then
        docker exec $BACKEND_CONTAINER python /app/scripts/create_production_admin.py || true
    fi
fi

echo ""
echo "6. 🔍 Verifying deployment..."
echo "-----------------------------"

# Check if services are running
docker-compose ps

# Test health endpoints
echo ""
echo "Testing API health..."
curl -s http://localhost:8000/api/health || echo "❌ Local API health check failed"

echo ""
echo "Testing external access..."
curl -s https://bootstrap-awareness.de/api/health || echo "❌ External API health check failed"

echo ""
echo "7. 📋 Manual steps required:"
echo "---------------------------"
echo ""
echo "If the backend is still failing due to path issues, run:"
echo "  docker exec -it $APP_DIR_backend_1 bash"
echo "  # Then check the file structure and adjust PYTHONPATH"
echo ""
echo "If the frontend is still showing Vite template:"
echo "  1. Check if the frontend image was built correctly"
echo "  2. Verify the nginx configuration is serving from correct path"
echo "  3. You may need to rebuild the frontend image with proper production build"
echo ""
echo "To rebuild images locally if needed:"
echo "  # For backend:"
echo "  docker build -t $REGISTRY/$IMAGE_NAME/backend:fixed -f backend/Dockerfile.prod backend/"
echo "  # For frontend:"
echo "  docker build -t $REGISTRY/$IMAGE_NAME/frontend:fixed -f frontend/Dockerfile.prod frontend/"
echo ""
echo "🎯 Fix script completed!"
echo "========================"