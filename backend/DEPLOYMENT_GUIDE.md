# Deployment Guide

This guide covers deploying the Bootstrap Awareness Platform to production.

## Prerequisites

- Access to the GitHub repository
- SSH access to the production server
- Docker and Docker Compose installed on the server
- Domain names configured (bootstrap-awareness.de)

## Production Deployment

### 1. Initial Server Setup

```bash
# SSH to the production server
ssh root@bootstrap-awareness.de

# Update system packages
apt update && apt upgrade -y

# Install Docker (if not already installed)
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt install docker-compose -y
```

### 2. Configure GitHub Actions

The deployment is automated via GitHub Actions. Configure these secrets in your repository:

**Required Secrets** (Settings → Secrets → Actions):
- `SSH_PRIVATE_KEY` - SSH key for server access
- `DB_PASSWORD` - Strong password for PostgreSQL
- `SECRET_KEY` - Generate with: `openssl rand -hex 32`
- `JWT_SECRET_KEY` - Generate with: `openssl rand -hex 32`
- `REDIS_PASSWORD` - Strong password for Redis

**Required Variables**:
```
DB_USER=awareness
DATABASE_URL=postgresql://awareness:[DB_PASSWORD]@postgres:5432/awareness_platform
REDIS_URL=redis://default:[REDIS_PASSWORD]@redis:6379
API_URL=https://api.bootstrap-awareness.de
FRONTEND_URL=https://bootstrap-awareness.de
ALLOWED_HOSTS=bootstrap-awareness.de,www.bootstrap-awareness.de,api.bootstrap-awareness.de
CORS_ORIGINS=https://bootstrap-awareness.de,https://www.bootstrap-awareness.de
EMAIL_FROM=noreply@bootstrap-awareness.de
EMAIL_FROM_NAME=Bootstrap Awareness Platform
```

### 3. Deploy via GitHub Actions

```bash
# Push your code to trigger deployment
git push origin main

# Or manually trigger deployment:
# Go to Actions → Deploy to Production → Run workflow
```

### 4. Post-Deployment Setup

After the first deployment, initialize the database:

```bash
# SSH to server
ssh root@bootstrap-awareness.de

# Run database migrations
docker exec -it backend-container alembic upgrade head

# Initialize database tables
docker exec -it backend-container python scripts/init_db_tables.py

# Create admin user
docker exec -it backend-container python scripts/create_admin_user.py
```

### 5. Verify Deployment

Check that all services are running:

```bash
# Check container status
docker ps

# Check application health
curl https://bootstrap-awareness.de/api/health

# View logs if needed
docker-compose logs -f
```

## Local Development

### Using Docker Compose

```bash
# Clone the repository
git clone https://github.com/TheMorpheus407/awareness-platform.git
cd awareness-platform

# Copy environment file
cp .env.example .env

# Start services
docker-compose -f docker-compose.dev.yml up -d

# Run migrations
docker-compose exec backend alembic upgrade head

# Access the application
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000/docs
```

### Manual Setup

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Troubleshooting

### Common Issues

**Frontend shows Vite template:**
- Check nginx configuration
- Verify frontend build completed
- Check docker logs: `docker logs frontend-container`

**API routes return 404:**
- Ensure database is initialized
- Check backend logs: `docker logs backend-container`
- Verify environment variables are set

**Cannot connect to database:**
- Check PostgreSQL is running: `docker ps | grep postgres`
- Verify DATABASE_URL is correct
- Check database logs: `docker logs postgres-container`

### Useful Commands

```bash
# View all logs
docker-compose logs

# Restart a specific service
docker-compose restart backend

# Rebuild and restart
docker-compose up -d --build

# Check disk usage
df -h

# Monitor resources
docker stats
```

## Backup and Recovery

### Database Backup

```bash
# Create backup
docker exec postgres-container pg_dump -U awareness awareness_platform > backup_$(date +%Y%m%d).sql

# Restore backup
docker exec -i postgres-container psql -U awareness awareness_platform < backup_20250109.sql
```

### Full System Backup

```bash
# Stop services
docker-compose down

# Backup volumes
tar -czf backup_volumes_$(date +%Y%m%d).tar.gz /var/lib/docker/volumes/

# Backup configuration
tar -czf backup_config_$(date +%Y%m%d).tar.gz docker-compose.yml .env
```

## Security Checklist

- [ ] Change default admin password after first login
- [ ] Enable firewall (allow only 80, 443, 22)
- [ ] Set up SSL certificate auto-renewal
- [ ] Configure backup automation
- [ ] Enable monitoring and alerts
- [ ] Review and update secrets regularly
- [ ] Set up fail2ban for SSH protection

## Support

For deployment assistance:
- Email: support@bootstrap-awareness.de
- GitHub Issues: https://github.com/TheMorpheus407/awareness-platform/issues

---

**Note**: Always test deployments in a staging environment first.