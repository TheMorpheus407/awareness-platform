# Deployment & Infrastructure Spezifikation
**Version 1.0 | Docker-basiertes Deployment**

## 1. Architektur-Übersicht

### 1.1 Container-Struktur
```
cybersec-platform/
├── frontend (React App)
├── backend (Python FastAPI)
├── postgres (PostgreSQL Database)
├── redis (Cache & Queue)
├── nginx (Reverse Proxy)
└── celery (Background Workers)
```

### 1.2 Netzwerk-Architektur
- **External Network**: nginx ↔ Internet
- **Internal Network**: Container-zu-Container Kommunikation
- **Database Network**: Isoliertes Netzwerk für DB-Zugriffe

## 2. Docker Configuration

### 2.1 Docker Compose (docker-compose.yml)
```yaml
version: '3.9'

services:
  # Frontend Container
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      args:
        - NODE_ENV=production
    container_name: cybersec-frontend
    restart: unless-stopped
    volumes:
      - frontend-build:/app/build
    networks:
      - internal
    environment:
      - VITE_API_URL=https://api.cybersec-platform.de

  # Backend API Container
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: cybersec-backend
    restart: unless-stopped
    ports:
      - "8000:8000"
    volumes:
      - ./backend/app:/app
      - backend-static:/app/static
      - backend-media:/app/media
    networks:
      - internal
      - database
    environment:
      - DATABASE_URL=postgresql://cybersec_user:${DB_PASSWORD}@postgres:5432/cybersec_db
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
      - SMTP_HOST=${SMTP_HOST}
      - SMTP_PORT=${SMTP_PORT}
      - SMTP_USER=${SMTP_USER}
      - SMTP_PASSWORD=${SMTP_PASSWORD}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

  # Celery Worker
  celery:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: cybersec-celery
    restart: unless-stopped
    command: celery -A app.tasks.celery_app worker --loglevel=info
    volumes:
      - ./backend/app:/app
    networks:
      - internal
      - database
    environment:
      - DATABASE_URL=postgresql://cybersec_user:${DB_PASSWORD}@postgres:5432/cybersec_db
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      - backend
      - redis

  # Celery Beat Scheduler
  celery-beat:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: cybersec-celery-beat
    restart: unless-stopped
    command: celery -A app.tasks.celery_app beat --loglevel=info
    volumes:
      - ./backend/app:/app
    networks:
      - internal
    environment:
      - DATABASE_URL=postgresql://cybersec_user:${DB_PASSWORD}@postgres:5432/cybersec_db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - backend
      - redis

  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    container_name: cybersec-postgres
    restart: unless-stopped
    ports:
      - "5432:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d
    networks:
      - database
    environment:
      - POSTGRES_USER=cybersec_admin
      - POSTGRES_PASSWORD=${POSTGRES_ADMIN_PASSWORD}
      - POSTGRES_DB=cybersec_db
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U cybersec_admin"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: cybersec-redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    networks:
      - internal
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Nginx Reverse Proxy
  nginx:
    image: nginx:alpine
    container_name: cybersec-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/conf.d:/etc/nginx/conf.d
      - frontend-build:/var/www/frontend
      - ./certbot/conf:/etc/letsencrypt
      - ./certbot/www:/var/www/certbot
    networks:
      - internal
      - external
    depends_on:
      - frontend
      - backend

  # Certbot for SSL
  certbot:
    image: certbot/certbot
    container_name: cybersec-certbot
    volumes:
      - ./certbot/conf:/etc/letsencrypt
      - ./certbot/www:/var/www/certbot
    entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait $${!}; done;'"

networks:
  external:
    driver: bridge
  internal:
    driver: bridge
  database:
    driver: bridge

volumes:
  postgres-data:
  redis-data:
  frontend-build:
  backend-static:
  backend-media:
```

### 2.2 Frontend Dockerfile
```dockerfile
# frontend/Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci --only=production

# Copy source code
COPY . .

# Build application
ARG NODE_ENV=production
ENV NODE_ENV=${NODE_ENV}
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built application
COPY --from=builder /app/dist /usr/share/nginx/html

# Add health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:80 || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### 2.3 Backend Dockerfile
```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY ./app /app

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')"

EXPOSE 8000

# Run with gunicorn
CMD ["gunicorn", "main:app", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
```

## 3. Nginx Configuration

### 3.1 Main Nginx Config (nginx/nginx.conf)
```nginx
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for" '
                    'rt=$request_time uct="$upstream_connect_time" '
                    'uht="$upstream_header_time" urt="$upstream_response_time"';

    access_log /var/log/nginx/access.log main;

    # Performance
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    # Security
    server_tokens off;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' https: data: 'unsafe-inline' 'unsafe-eval';" always;

    # Gzip
    gzip on;
    gzip_disable "msie6";
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript 
               application/json application/javascript application/xml+rss 
               application/rss+xml application/atom+xml;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=auth:10m rate=5r/m;

    # Include site configurations
    include /etc/nginx/conf.d/*.conf;
}
```

### 3.2 Site Configuration (nginx/conf.d/cybersec-platform.conf)
```nginx
# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name cybersec-platform.de www.cybersec-platform.de;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$server_name$request_uri;
    }
}

# Main HTTPS server
server {
    listen 443 ssl http2;
    server_name cybersec-platform.de www.cybersec-platform.de;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/cybersec-platform.de/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/cybersec-platform.de/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Frontend
    location / {
        root /var/www/frontend;
        try_files $uri $uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # API Proxy
    location /api {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Rate limiting
        limit_req zone=api burst=20 nodelay;
    }

    # Auth endpoints with stricter rate limiting
    location /api/v1/auth {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        limit_req zone=auth burst=5 nodelay;
    }

    # WebSocket support for real-time updates
    location /ws {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health check endpoint
    location /health {
        access_log off;
        add_header Content-Type text/plain;
        return 200 'healthy';
    }
}
```

## 4. Environment Configuration

### 4.1 Production Environment (.env.production)
```bash
# Database
POSTGRES_ADMIN_PASSWORD=secure_admin_password_here
DB_PASSWORD=secure_db_password_here

# Redis
REDIS_PASSWORD=secure_redis_password_here

# Application
SECRET_KEY=your-very-long-random-secret-key-here
ENVIRONMENT=production
DEBUG=false

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=noreply@cybersec-platform.de
SMTP_PASSWORD=your-smtp-password

# External APIs
# (Optional services like SendGrid, Stripe can be configured here)

# Domains
ALLOWED_HOSTS=cybersec-platform.de,www.cybersec-platform.de,api.cybersec-platform.de
CORS_ORIGINS=https://cybersec-platform.de,https://www.cybersec-platform.de

# Security
SESSION_COOKIE_SECURE=true
CSRF_COOKIE_SECURE=true
SECURE_SSL_REDIRECT=true
```

### 4.2 Development Environment (.env.development)
```bash
# Database
POSTGRES_ADMIN_PASSWORD=dev_password
DB_PASSWORD=dev_password

# Redis
REDIS_PASSWORD=dev_redis_password

# Application
SECRET_KEY=dev-secret-key-for-local-development
ENVIRONMENT=development
DEBUG=true

# Email (Mailhog for local dev)
SMTP_HOST=mailhog
SMTP_PORT=1025
SMTP_USER=
SMTP_PASSWORD=

# External APIs
# (Optional services like SendGrid, Stripe can be configured here)

# Domains
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ORIGINS=http://localhost:3000

# Security
SESSION_COOKIE_SECURE=false
CSRF_COOKIE_SECURE=false
SECURE_SSL_REDIRECT=false
```

## 5. Deployment Scripts

### 5.1 Initial Setup Script (scripts/setup.sh)
```bash
#!/bin/bash
set -e

echo "🚀 Setting up Cybersec Awareness Platform..."

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "Docker is required but not installed. Aborting." >&2; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "Docker Compose is required but not installed. Aborting." >&2; exit 1; }

# Create necessary directories
mkdir -p nginx/conf.d
mkdir -p certbot/conf
mkdir -p certbot/www
mkdir -p init-scripts
mkdir -p backups

# Copy environment file
if [ ! -f .env ]; then
    cp .env.example .env
    echo "⚠️  Please edit .env file with your configuration"
    exit 1
fi

# Generate secrets if not exists
if grep -q "your-very-long-random-secret-key-here" .env; then
    SECRET_KEY=$(openssl rand -base64 32)
    sed -i "s/your-very-long-random-secret-key-here/$SECRET_KEY/g" .env
    echo "✅ Generated SECRET_KEY"
fi

# Create database initialization script
cat > init-scripts/01-init-db.sql << 'EOF'
-- Create application user
CREATE USER cybersec_user WITH PASSWORD :'user_password';

-- Create schemas
CREATE SCHEMA IF NOT EXISTS app;
CREATE SCHEMA IF NOT EXISTS audit;
CREATE SCHEMA IF NOT EXISTS reporting;

-- Grant permissions
GRANT ALL PRIVILEGES ON SCHEMA app TO cybersec_user;
GRANT ALL PRIVILEGES ON SCHEMA audit TO cybersec_user;
GRANT SELECT ON SCHEMA reporting TO cybersec_user;

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
EOF

echo "✅ Setup complete! Run 'docker-compose up -d' to start the platform."
```

### 5.2 Deployment Script (scripts/deploy.sh)
```bash
#!/bin/bash
set -e

echo "🚀 Deploying Cybersec Awareness Platform..."

# Load environment
source .env

# Pull latest code
echo "📥 Pulling latest code..."
git pull origin main

# Build and deploy
echo "🏗️  Building containers..."
docker-compose build --no-cache

# Run database migrations
echo "🗄️  Running database migrations..."
docker-compose run --rm backend alembic upgrade head

# Collect static files
echo "📁 Collecting static files..."
docker-compose run --rm backend python -m app.main collect-static

# Restart services
echo "🔄 Restarting services..."
docker-compose down
docker-compose up -d

# Health check
echo "❤️  Checking health..."
sleep 10
curl -f http://localhost/health || exit 1

echo "✅ Deployment complete!"
```

### 5.3 Backup Script (scripts/backup.sh)
```bash
#!/bin/bash
set -e

# Configuration
BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

echo "🔒 Starting backup..."

# Database backup
echo "📊 Backing up database..."
docker-compose exec -T postgres pg_dump -U cybersec_admin cybersec_db | gzip > "${BACKUP_DIR}/db_${TIMESTAMP}.sql.gz"

# Media files backup
echo "📁 Backing up media files..."
docker run --rm -v cybersec-platform_backend-media:/data -v ${BACKUP_DIR}:/backup alpine tar czf /backup/media_${TIMESTAMP}.tar.gz -C /data .

# Configuration backup
echo "⚙️  Backing up configuration..."
tar czf "${BACKUP_DIR}/config_${TIMESTAMP}.tar.gz" .env nginx/ docker-compose.yml

# Clean old backups
echo "🧹 Cleaning old backups..."
find ${BACKUP_DIR} -name "*.gz" -mtime +${RETENTION_DAYS} -delete

echo "✅ Backup complete!"
```

### 5.4 Monitoring Script (scripts/monitor.sh)
```bash
#!/bin/bash

# Health checks
check_service() {
    SERVICE=$1
    if docker-compose ps | grep -q "${SERVICE}.*Up"; then
        echo "✅ ${SERVICE} is running"
    else
        echo "❌ ${SERVICE} is down!"
        exit 1
    fi
}

# Check all services
check_service "frontend"
check_service "backend"
check_service "postgres"
check_service "redis"
check_service "nginx"
check_service "celery"

# Check disk space
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "⚠️  Disk usage is high: ${DISK_USAGE}%"
fi

# Check database connections
DB_CONNECTIONS=$(docker-compose exec -T postgres psql -U cybersec_admin -d cybersec_db -t -c "SELECT count(*) FROM pg_stat_activity;")
echo "📊 Active DB connections: ${DB_CONNECTIONS}"

# Check Redis
REDIS_PING=$(docker-compose exec -T redis redis-cli ping)
if [ "$REDIS_PING" = "PONG" ]; then
    echo "✅ Redis is responsive"
else
    echo "❌ Redis is not responding!"
fi
```

## 6. SSL Certificate Management

### 6.1 Initial SSL Setup (scripts/setup-ssl.sh)
```bash
#!/bin/bash
set -e

DOMAIN="cybersec-platform.de"
EMAIL="admin@cybersec-platform.de"

echo "🔐 Setting up SSL certificates..."

# Initial certificate request
docker-compose run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email ${EMAIL} \
    --agree-tos \
    --no-eff-email \
    -d ${DOMAIN} \
    -d www.${DOMAIN}

# Reload nginx
docker-compose exec nginx nginx -s reload

echo "✅ SSL setup complete!"
```

### 6.2 Certificate Renewal Cron
```bash
# Add to crontab
0 12 * * * /path/to/cybersec-platform/scripts/renew-ssl.sh >> /var/log/ssl-renewal.log 2>&1
```

## 7. Logging Configuration

### 7.1 Docker Logging (docker-compose.override.yml)
```yaml
version: '3.9'

services:
  frontend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "5"

  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "50m"
        max-file: "10"

  postgres:
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "10"
```

### 7.2 Application Logging
```python
# backend/app/core/logging.py
import logging
import json
from datetime import datetime

class StructuredFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "environment": os.getenv("ENVIRONMENT", "development")
        }
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ["message", "levelname", "module", "funcName", "lineno"]:
                log_obj[key] = value
        
        return json.dumps(log_obj)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.StreamHandler()
    ]
)

# Apply formatter
for handler in logging.root.handlers:
    handler.setFormatter(StructuredFormatter())
```

## 8. Monitoring & Alerting

### 8.1 Health Check Endpoints
```python
# backend/app/api/health.py
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

router = APIRouter()

@router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@router.get("/health/detailed")
async def detailed_health_check(db: Session = Depends(get_db)):
    checks = {
        "api": "healthy",
        "database": "unknown",
        "redis": "unknown",
        "disk_space": "unknown"
    }
    
    # Database check
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = "healthy"
    except Exception as e:
        checks["database"] = f"unhealthy: {str(e)}"
    
    # Redis check
    try:
        redis_client.ping()
        checks["redis"] = "healthy"
    except Exception as e:
        checks["redis"] = f"unhealthy: {str(e)}"
    
    # Disk space check
    import shutil
    total, used, free = shutil.disk_usage("/")
    free_percentage = (free / total) * 100
    if free_percentage > 20:
        checks["disk_space"] = f"healthy: {free_percentage:.1f}% free"
    else:
        checks["disk_space"] = f"warning: {free_percentage:.1f}% free"
    
    return checks
```

### 8.2 Prometheus Metrics
```python
# backend/app/core/metrics.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import Response

# Define metrics
request_count = Counter(
    'app_requests_total',
    'Total requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'app_request_duration_seconds',
    'Request duration',
    ['method', 'endpoint']
)

active_users = Gauge(
    'app_active_users',
    'Currently active users'
)

@router.get("/metrics")
async def get_metrics():
    return Response(generate_latest(), media_type="text/plain")
```

## 9. Security Hardening

### 9.1 System Security (scripts/harden.sh)
```bash
#!/bin/bash
set -e

echo "🔒 Hardening system security..."

# Set proper permissions
chmod 600 .env
chmod 700 scripts/*.sh

# Firewall rules (ufw)
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp  # SSH
ufw allow 80/tcp  # HTTP
ufw allow 443/tcp # HTTPS
ufw --force enable

# Fail2ban configuration
cat > /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true

[nginx-http-auth]
enabled = true

[nginx-limit-req]
enabled = true
logpath = /var/log/nginx/error.log
EOF

systemctl restart fail2ban

echo "✅ Security hardening complete!"
```

### 9.2 Docker Security
```yaml
# docker-compose.security.yml
version: '3.9'

services:
  backend:
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE

  postgres:
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
```

## 10. Disaster Recovery

### 10.1 Recovery Procedure
```bash
#!/bin/bash
# scripts/restore.sh
set -e

if [ $# -eq 0 ]; then
    echo "Usage: $0 <backup-timestamp>"
    exit 1
fi

TIMESTAMP=$1
BACKUP_DIR="/backups"

echo "🔄 Starting recovery from backup ${TIMESTAMP}..."

# Stop services
docker-compose down

# Restore database
echo "📊 Restoring database..."
docker-compose up -d postgres
sleep 10
gunzip < "${BACKUP_DIR}/db_${TIMESTAMP}.sql.gz" | docker-compose exec -T postgres psql -U cybersec_admin cybersec_db

# Restore media files
echo "📁 Restoring media files..."
docker run --rm -v cybersec-platform_backend-media:/data -v ${BACKUP_DIR}:/backup alpine tar xzf /backup/media_${TIMESTAMP}.tar.gz -C /data

# Start services
echo "🚀 Starting services..."
docker-compose up -d

echo "✅ Recovery complete!"
```

### 10.2 Rollback Procedure
```bash
#!/bin/bash
# scripts/rollback.sh
set -e

echo "⚠️  Rolling back to previous version..."

# Get previous git tag
PREVIOUS_TAG=$(git describe --tags --abbrev=0 HEAD^)

# Checkout previous version
git checkout $PREVIOUS_TAG

# Rebuild and deploy
./scripts/deploy.sh

echo "✅ Rollback to ${PREVIOUS_TAG} complete!"
```

## 11. Performance Tuning

### 11.1 PostgreSQL Tuning
```sql
-- postgresql.conf optimizations
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 4MB
min_wal_size = 1GB
max_wal_size = 4GB
```

### 11.2 Redis Configuration
```conf
# redis.conf
maxmemory 512mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

## 12. Maintenance Procedures

### 12.1 Daily Maintenance
- Log rotation
- Temporary file cleanup
- Health checks
- Backup verification

### 12.2 Weekly Maintenance
- Security updates
- Performance analysis
- Database vacuum
- SSL certificate check

### 12.3 Monthly Maintenance
- Full system backup
- Dependency updates
- Security audit
- Capacity planning

## 13. Scaling Strategy

### 13.1 Horizontal Scaling
```yaml
# docker-compose.scale.yml
version: '3.9'

services:
  backend:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '0.5'
          memory: 512M

  celery:
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '0.5'
          memory: 256M
```

### 13.2 Database Replication
- Primary-Secondary PostgreSQL setup
- Read replicas for reporting
- Connection pooling with PgBouncer

## 14. Compliance & Audit

### 14.1 DSGVO Compliance
- Data encryption at rest and in transit
- Access logging and audit trails
- Data retention policies
- Right to deletion implementation

### 14.2 Security Audit Log
```bash
# Audit log shipping to secure storage
*/10 * * * * docker-compose exec postgres pg_dump -t audit.audit_logs | gzip | aws s3 cp - s3://cybersec-audit-logs/$(date +\%Y/\%m/\%d/\%H-\%M).sql.gz
```

Diese umfassende Deployment-Spezifikation bietet eine produktionsreife Infrastruktur ohne Terraform, mit Fokus auf Sicherheit, Skalierbarkeit und einfache Wartung.