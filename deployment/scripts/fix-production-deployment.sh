#!/bin/bash
set -e

echo "🔧 Starting production deployment fix..."

# Variables
DEPLOY_DIR="/opt/awareness"
BACKUP_DIR="/opt/awareness/backup-$(date +%Y%m%d-%H%M%S)"

# Create backup
echo "📦 Creating backup..."
sudo mkdir -p "$BACKUP_DIR"
sudo cp -r "$DEPLOY_DIR"/* "$BACKUP_DIR/" || true

# Fix Docker Compose file
echo "🐳 Fixing docker-compose.prod.yml..."
cat > "$DEPLOY_DIR/docker-compose.prod.yml" << 'EOF'
version: '3.8'

services:
  backend:
    image: ghcr.io/themorpheus407/awareness-platform/backend:latest
    container_name: backend-container
    env_file: .env.production
    environment:
      - DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
    networks:
      - app-network
    volumes:
      - ./backend/backend:/app
    working_dir: /app
    command: ["python", "main.py"]
    restart: unless-stopped

  frontend:
    image: ghcr.io/themorpheus407/awareness-platform/frontend:latest
    container_name: frontend-container
    networks:
      - app-network
    restart: unless-stopped

  postgres:
    image: postgres:15
    container_name: postgres-container
    env_file: .env.production
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - app-network
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: redis-container
    networks:
      - app-network
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    container_name: nginx-container
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - ./certbot/www:/var/www/certbot:ro
      - ./certbot/conf:/etc/letsencrypt:ro
    depends_on:
      - backend
      - frontend
    networks:
      - app-network
    restart: unless-stopped

  certbot:
    image: certbot/certbot
    container_name: certbot-container
    volumes:
      - ./certbot/www:/var/www/certbot
      - ./certbot/conf:/etc/letsencrypt
    entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait $${!}; done;'"

networks:
  app-network:
    driver: bridge

volumes:
  postgres_data:
EOF

# Create Dockerfile override for backend
echo "🔨 Creating backend Dockerfile override..."
cat > "$DEPLOY_DIR/backend/Dockerfile.prod" << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Copy from nested structure
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

# Create init script
echo "🚀 Creating initialization script..."
cat > "$DEPLOY_DIR/init-production.sh" << 'EOF'
#!/bin/bash
set -e

echo "Initializing production environment..."

# Wait for services
sleep 10

# Run migrations
echo "Running database migrations..."
docker exec backend-container alembic upgrade head || {
    echo "Migration failed, trying to fix enums..."
    docker exec backend-container python scripts/fix_enum_conflicts.py
    docker exec backend-container alembic upgrade head
}

# Initialize tables
echo "Initializing database tables..."
docker exec backend-container python scripts/init_db_tables.py || echo "Tables might already exist"

# Create admin user
echo "Creating admin user..."
docker exec backend-container python scripts/create_admin_user.py || echo "Admin might already exist"

echo "✅ Initialization complete!"
EOF

chmod +x "$DEPLOY_DIR/init-production.sh"

# Stop current containers
echo "🛑 Stopping current containers..."
cd "$DEPLOY_DIR"
sudo docker-compose -f docker-compose.prod.yml down || true

# Pull latest images
echo "📥 Pulling latest images..."
sudo docker pull ghcr.io/themorpheus407/awareness-platform/backend:latest || echo "Backend image pull failed"
sudo docker pull ghcr.io/themorpheus407/awareness-platform/frontend:latest || echo "Frontend image pull failed"

# Start services
echo "🚀 Starting services..."
sudo docker-compose -f docker-compose.prod.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 20

# Initialize database
echo "🗄️ Initializing database..."
sudo ./init-production.sh

# Check status
echo "📊 Checking service status..."
sudo docker ps
echo ""
echo "🔍 Backend health check:"
curl -f http://localhost:8000/api/health || echo "Backend health check failed"
echo ""
echo "🔍 Frontend check:"
curl -f http://localhost || echo "Frontend check failed"

echo "✅ Production fix complete! Check https://bootstrap-awareness.de"