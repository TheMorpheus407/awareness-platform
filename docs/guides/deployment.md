# Deployment Guide

## Overview

This guide covers deploying the Awareness Platform to production on Ubuntu 24.04 LTS.

## Prerequisites

- Ubuntu 24.04 LTS server
- Domain name pointed to server IP (bootstrap-awareness.de)
- SSH access to the server
- Docker and Docker Compose installed

## Directory Structure

The application should be deployed to `/home/awareness/awareness-platform/` with this structure:

```
/home/awareness/awareness-platform/
├── backend/                 # FastAPI backend
├── frontend/               # React frontend
├── deployment/             # Deployment configs
├── docker-compose.yml      # Production compose file
├── .env                    # Environment variables
└── scripts/                # Utility scripts
```

## Deployment Methods

### Method 1: Docker Compose (Recommended)

1. **Clone the repository**:
```bash
cd /home/awareness
git clone https://github.com/TheMorpheus407/awareness-platform.git
cd awareness-platform
```

2. **Create environment file**:
```bash
cp .env.example .env
# Edit .env with production values
```

3. **Start services**:
```bash
docker-compose up -d
```

4. **Run migrations**:
```bash
docker-compose exec backend alembic upgrade head
```

5. **Check status**:
```bash
docker-compose ps
docker-compose logs -f
```

### Method 2: Systemd Services

If not using Docker, you can run services directly:

1. **Backend Setup**:
```bash
cd /home/awareness/awareness-platform/backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. **Frontend Setup**:
```bash
cd /home/awareness/awareness-platform/frontend
npm install
npm run build
```

3. **Create systemd services** (see scripts/fix-production.sh for examples)

## Nginx Configuration

1. **Install Nginx**:
```bash
sudo apt update
sudo apt install nginx
```

2. **Configure Nginx**:
```bash
# Copy the config from deployment/nginx/sites-enabled/awareness-platform.conf
sudo cp deployment/nginx/sites-enabled/awareness-platform.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/awareness-platform.conf /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default  # Remove default site
```

3. **Test and reload**:
```bash
sudo nginx -t
sudo systemctl reload nginx
```

## SSL Certificate

1. **Install Certbot**:
```bash
sudo apt install certbot python3-certbot-nginx
```

2. **Obtain certificate**:
```bash
sudo certbot --nginx -d bootstrap-awareness.de -d www.bootstrap-awareness.de
```

## Database Setup

1. **PostgreSQL** (if not using Docker):
```bash
sudo apt install postgresql-15
sudo -u postgres createdb awareness_platform
sudo -u postgres psql -c "CREATE USER awareness WITH PASSWORD 'your-password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE awareness_platform TO awareness;"
```

2. **Run migrations**:
```bash
cd backend
alembic upgrade head
```

## Environment Variables

Required environment variables in `.env`:

```bash
# Database
DATABASE_URL=postgresql://awareness:password@localhost/awareness_platform
DB_PASSWORD=AwarenessDB2024Secure

# Redis
REDIS_URL=redis://default:password@localhost:6379
REDIS_PASSWORD=redis_595e9ffc5e32e7fc6d8cbae32a9e610c

# Security
SECRET_KEY=8eb9afc6e39da58b95628f1505bf1107c7f9f0243990d7acd4ba23f82694b1e5

# Email
SENDGRID_API_KEY=your-sendgrid-key
EMAIL_FROM=noreply@bootstrap-awareness.de

# Frontend
REACT_APP_API_URL=https://bootstrap-awareness.de
```

## Troubleshooting

### Check Services

```bash
# Docker services
docker-compose ps
docker-compose logs backend
docker-compose logs frontend

# Systemd services
systemctl status awareness-backend
systemctl status awareness-frontend
systemctl status nginx

# Ports
ss -tlnp | grep -E "(80|443|8000|5173)"
```

### Common Issues

1. **Frontend shows Vite template**:
   - Frontend needs to be built: `npm run build`
   - Nginx needs to serve from `frontend/dist`

2. **API returns 404**:
   - Check nginx upstream definitions
   - Verify backend is running on port 8000
   - Check API routes include `/api` prefix

3. **Database connection failed**:
   - Verify PostgreSQL is running
   - Check DATABASE_URL in .env
   - Run migrations

### Logs

- Nginx: `/var/log/nginx/error.log`
- Backend: `docker-compose logs backend` or `journalctl -u awareness-backend`
- Frontend: `docker-compose logs frontend` or `journalctl -u awareness-frontend`

## Quick Diagnosis

Run the diagnosis script:
```bash
bash scripts/diagnose-production.sh
```

## Quick Fix

Run the fix script (as root):
```bash
sudo bash scripts/fix-production.sh
```

## Monitoring

- Health check: https://bootstrap-awareness.de/api/health
- Logs: `tail -f /var/log/nginx/awareness-error.log`
- System: `htop`, `df -h`, `free -h`

## Backup

Regular backups should include:
- PostgreSQL database: `pg_dump awareness_platform > backup.sql`
- Uploaded files: `/home/awareness/awareness-platform/backend/uploads/`
- Environment files: `.env`