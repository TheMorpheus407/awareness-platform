# Deployment Guide

## Overview
This guide covers deployment options for the Cybersecurity Awareness Platform backend, from development to production environments.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Development Deployment](#development-deployment)
3. [Production Deployment](#production-deployment)
4. [Docker Deployment](#docker-deployment)
5. [Kubernetes Deployment](#kubernetes-deployment)
6. [Database Migrations](#database-migrations)
7. [SSL/TLS Configuration](#ssltls-configuration)
8. [Monitoring Setup](#monitoring-setup)
9. [Backup and Recovery](#backup-and-recovery)
10. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements
- **OS**: Ubuntu 20.04+ or similar Linux distribution
- **CPU**: Minimum 2 cores, recommended 4+ cores
- **RAM**: Minimum 4GB, recommended 8GB+
- **Storage**: Minimum 20GB, recommended 50GB+ with SSD
- **Python**: 3.11+
- **PostgreSQL**: 14+
- **Redis**: 6+
- **Nginx**: Latest stable

### Required Tools
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y \
    python3.11 python3.11-venv python3.11-dev \
    postgresql postgresql-contrib \
    redis-server \
    nginx \
    git curl wget \
    build-essential \
    certbot python3-certbot-nginx
```

## Development Deployment

### 1. Local Setup
```bash
# Clone repository
git clone <repository-url>
cd backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Setup environment
cp .env.example .env
# Edit .env with your configuration

# Setup database
createdb cybersec_platform
alembic upgrade head

# Create admin user
python scripts/create_admin.py

# Run development server
python main.py
```

### 2. Docker Compose Development
```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f

# Run migrations
docker-compose exec backend alembic upgrade head

# Create admin user
docker-compose exec backend python scripts/create_admin.py
```

## Production Deployment

### 1. Server Preparation
```bash
# Create application user
sudo useradd -m -s /bin/bash cybersec
sudo usermod -aG sudo cybersec

# Create directories
sudo mkdir -p /opt/cybersec/{app,logs,uploads,certificates}
sudo chown -R cybersec:cybersec /opt/cybersec
```

### 2. PostgreSQL Setup
```bash
# Install PostgreSQL
sudo apt install postgresql-14

# Create database and user
sudo -u postgres psql <<EOF
CREATE USER cybersec WITH PASSWORD 'secure_password';
CREATE DATABASE cybersec_platform OWNER cybersec;
GRANT ALL PRIVILEGES ON DATABASE cybersec_platform TO cybersec;
EOF

# Configure PostgreSQL for production
sudo nano /etc/postgresql/14/main/postgresql.conf
# Add/modify:
# max_connections = 200
# shared_buffers = 256MB
# effective_cache_size = 1GB
# work_mem = 4MB

# Restart PostgreSQL
sudo systemctl restart postgresql
```

### 3. Redis Setup
```bash
# Configure Redis
sudo nano /etc/redis/redis.conf
# Add/modify:
# maxmemory 256mb
# maxmemory-policy allkeys-lru
# requirepass your_redis_password

# Enable and start Redis
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

### 4. Application Deployment
```bash
# Switch to app user
sudo su - cybersec
cd /opt/cybersec/app

# Clone repository
git clone <repository-url> .

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup production environment
cp .env.example .env
# Edit .env with production settings

# Run migrations
alembic upgrade head

# Collect static files (if applicable)
python manage.py collectstatic --noinput
```

### 5. Systemd Service Setup
```bash
# Create service file
sudo nano /etc/systemd/system/cybersec-backend.service
```

Add the following content:
```ini
[Unit]
Description=Cybersecurity Platform Backend
After=network.target postgresql.service redis.service

[Service]
Type=exec
User=cybersec
Group=cybersec
WorkingDirectory=/opt/cybersec/app
Environment="PATH=/opt/cybersec/app/venv/bin"
ExecStart=/opt/cybersec/app/venv/bin/uvicorn main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --loop uvloop \
    --access-log \
    --log-level info
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable cybersec-backend
sudo systemctl start cybersec-backend
sudo systemctl status cybersec-backend
```

### 6. Nginx Configuration
```bash
# Create Nginx configuration
sudo nano /etc/nginx/sites-available/cybersec-platform
```

Add configuration from `nginx/sites-enabled/default.conf`.

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/cybersec-platform /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Docker Deployment

### Production Docker Build
```bash
# Build production image
docker build -f Dockerfile.prod -t cybersec-backend:latest .

# Run with environment file
docker run -d \
    --name cybersec-backend \
    --env-file .env.production \
    -p 8000:8000 \
    -v /opt/cybersec/logs:/app/logs \
    -v /opt/cybersec/uploads:/app/uploads \
    --restart unless-stopped \
    cybersec-backend:latest
```

### Docker Compose Production
```bash
# Use production compose file
docker-compose -f docker-compose.prod.yml up -d

# Scale workers
docker-compose -f docker-compose.prod.yml up -d --scale backend=3
```

## Kubernetes Deployment

### 1. Create Namespace
```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: cybersec-platform
```

### 2. ConfigMap and Secrets
```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: cybersec-config
  namespace: cybersec-platform
data:
  ENVIRONMENT: "production"
  APP_NAME: "Cybersecurity Platform"
  LOG_LEVEL: "INFO"
```

```yaml
# secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: cybersec-secrets
  namespace: cybersec-platform
type: Opaque
stringData:
  DATABASE_URL: "postgresql+asyncpg://user:pass@postgres:5432/db"
  SECRET_KEY: "your-secret-key"
  REDIS_URL: "redis://:password@redis:6379/0"
```

### 3. Deployment
```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cybersec-backend
  namespace: cybersec-platform
spec:
  replicas: 3
  selector:
    matchLabels:
      app: cybersec-backend
  template:
    metadata:
      labels:
        app: cybersec-backend
    spec:
      containers:
      - name: backend
        image: cybersec-backend:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: cybersec-config
        - secretRef:
            name: cybersec-secrets
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### 4. Service and Ingress
```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: cybersec-backend
  namespace: cybersec-platform
spec:
  selector:
    app: cybersec-backend
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
---
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: cybersec-ingress
  namespace: cybersec-platform
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - api.cybersec-platform.de
    secretName: cybersec-tls
  rules:
  - host: api.cybersec-platform.de
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: cybersec-backend
            port:
              number: 80
```

Apply configurations:
```bash
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f secret.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f ingress.yaml
```

## Database Migrations

### Running Migrations
```bash
# Development
alembic upgrade head

# Production with backup
pg_dump cybersec_platform > backup_$(date +%Y%m%d_%H%M%S).sql
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

### Creating New Migrations
```bash
# Auto-generate migration
alembic revision --autogenerate -m "Add new feature"

# Review and edit migration
nano alembic/versions/xxx_add_new_feature.py

# Test migration
alembic upgrade head
alembic downgrade -1
alembic upgrade head
```

## SSL/TLS Configuration

### Let's Encrypt with Certbot
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d api.cybersec-platform.de

# Auto-renewal
sudo certbot renew --dry-run
```

### Manual SSL Configuration
```nginx
server {
    listen 443 ssl http2;
    server_name api.cybersec-platform.de;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # ... rest of configuration
}
```

## Monitoring Setup

### 1. Prometheus Configuration
```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'cybersec-backend'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

### 2. Grafana Dashboard
Import the dashboard from `monitoring/grafana/dashboards/`.

### 3. Alerting Rules
```yaml
# alerts.yml
groups:
  - name: cybersec_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: High error rate detected
```

## Backup and Recovery

### Database Backup
```bash
# Automated backup script
#!/bin/bash
BACKUP_DIR="/opt/cybersec/backups"
DB_NAME="cybersec_platform"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup
pg_dump $DB_NAME | gzip > $BACKUP_DIR/db_backup_$DATE.sql.gz

# Keep only last 7 days
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +7 -delete
```

### Recovery Procedure
```bash
# Restore from backup
gunzip < backup.sql.gz | psql cybersec_platform

# Restore uploads
tar -xzf uploads_backup.tar.gz -C /opt/cybersec/
```

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   ```bash
   # Check PostgreSQL status
   sudo systemctl status postgresql
   
   # Check connection
   psql -U cybersec -d cybersec_platform -h localhost
   ```

2. **Redis Connection Issues**
   ```bash
   # Check Redis status
   sudo systemctl status redis-server
   
   # Test connection
   redis-cli ping
   ```

3. **Application Errors**
   ```bash
   # Check logs
   journalctl -u cybersec-backend -f
   
   # Check application logs
   tail -f /opt/cybersec/logs/app.log
   ```

4. **Performance Issues**
   ```bash
   # Monitor resources
   htop
   
   # Check database queries
   psql -c "SELECT * FROM pg_stat_activity WHERE state = 'active';"
   ```

### Health Checks
```bash
# Basic health
curl http://localhost:8000/health

# Detailed health
curl http://localhost:8000/api/v1/health/detailed

# Metrics
curl http://localhost:8000/metrics
```

## Security Checklist

- [ ] Change all default passwords
- [ ] Enable firewall (ufw or iptables)
- [ ] Configure fail2ban for SSH
- [ ] Set up SSL/TLS certificates
- [ ] Enable security headers in Nginx
- [ ] Configure rate limiting
- [ ] Set up monitoring and alerting
- [ ] Regular security updates
- [ ] Backup encryption
- [ ] Log rotation configured
- [ ] Secrets management system
- [ ] Regular penetration testing