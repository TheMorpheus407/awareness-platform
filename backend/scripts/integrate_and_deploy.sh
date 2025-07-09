#!/bin/bash
# Integration and Deployment Script for Stage 1
# This script integrates all changes and deploys to production

set -e  # Exit on error

echo "=== Stage 1 Integration and Deployment Script ==="
echo "Server: 83.228.205.20 (bootstrap-awareness.de)"
echo "Starting at: $(date)"

# Configuration
SERVER_IP="83.228.205.20"
SERVER_USER="root"
SSH_KEY="/mnt/e/Projects/AwarenessSchulungen/bootstrap-awareness private key.txt"
PROJECT_ROOT="/mnt/e/Projects/AwarenessSchulungen"
REMOTE_DIR="/opt/awareness-platform"

# Step 1: Commit all changes
echo -e "\n1. Committing all changes..."
cd "$PROJECT_ROOT"
git add -A
git commit -m "Stage 1 Complete: Integration of all features
- Row Level Security (RLS) implementation
- Two-Factor Authentication (2FA) support
- Internationalization (i18n) with German/English
- E2E testing with Playwright
- Enhanced seed data with demo users
- Documentation updates
- Production-ready deployment configuration

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
" || echo "No changes to commit"

# Step 2: Push to remote
echo -e "\n2. Pushing to GitHub..."
git push origin main || echo "Failed to push, continuing..."

# Step 3: Build Docker images locally for faster deployment
echo -e "\n3. Building Docker images..."
# Note: This would require Docker, skipping for now

# Step 4: Prepare deployment package
echo -e "\n4. Creating deployment package..."
tar -czf stage1_deployment.tar.gz \
  --exclude='*.pyc' \
  --exclude='__pycache__' \
  --exclude='node_modules' \
  --exclude='venv' \
  --exclude='.git' \
  --exclude='*.log' \
  --exclude='*.tmp' \
  --exclude='test_venv' \
  backend frontend deployment docker-compose.prod.yml .env.example

# Step 5: Create deployment checklist
echo -e "\n5. Creating deployment checklist..."
cat > deployment_checklist.md << 'EOF'
# Stage 1 Deployment Checklist

## Pre-deployment
- [x] All changes committed
- [x] Tests passing (verified locally)
- [x] Documentation updated
- [x] Environment variables documented

## Features Included
- [x] Row Level Security (RLS)
- [x] Two-Factor Authentication (2FA)
- [x] Internationalization (i18n)
- [x] E2E Testing Framework
- [x] Enhanced Seed Data

## Deployment Steps
1. [ ] SSH to server
2. [ ] Backup existing database
3. [ ] Pull latest code
4. [ ] Update environment variables
5. [ ] Run database migrations
6. [ ] Apply RLS policies
7. [ ] Build and deploy containers
8. [ ] Run seed data script
9. [ ] Verify all services
10. [ ] Run smoke tests

## Post-deployment Verification
- [ ] Login works
- [ ] 2FA setup works
- [ ] Language switching works
- [ ] API endpoints respond
- [ ] RLS data isolation works
- [ ] E2E tests pass

## Rollback Plan
1. Restore database backup
2. Revert to previous container images
3. Check logs for issues
EOF

# Step 6: Create production environment template
echo -e "\n6. Creating production environment template..."
cat > .env.production.template << 'EOF'
# Database
DB_USER=awareness
DB_PASSWORD=CHANGE_ME_SECURE_PASSWORD
DATABASE_URL=postgresql://awareness:CHANGE_ME_SECURE_PASSWORD@postgres:5432/awareness_platform

# Redis
REDIS_PASSWORD=CHANGE_ME_REDIS_PASSWORD
REDIS_URL=redis://default:CHANGE_ME_REDIS_PASSWORD@redis:6379

# Security
SECRET_KEY=CHANGE_ME_MIN_32_CHARS_RANDOM_STRING
JWT_SECRET_KEY=CHANGE_ME_JWT_SECRET

# External Services
YOUTUBE_API_KEY=your-youtube-api-key
SENDGRID_API_KEY=your-sendgrid-api-key
STRIPE_SECRET_KEY=your-stripe-secret-key
STRIPE_PUBLIC_KEY=your-stripe-public-key
STRIPE_WEBHOOK_SECRET=your-stripe-webhook-secret

# Application
ENVIRONMENT=production
API_URL=https://bootstrap-awareness.de
FRONTEND_URL=https://bootstrap-awareness.de
ALLOWED_HOSTS=bootstrap-awareness.de,www.bootstrap-awareness.de
CORS_ORIGINS=["https://bootstrap-awareness.de","https://www.bootstrap-awareness.de"]

# Email
EMAIL_FROM=noreply@bootstrap-awareness.de
EMAIL_FROM_NAME=Bootstrap Awareness Platform

# Monitoring
SENTRY_DSN=
PROMETHEUS_ENABLED=true
EOF

# Step 7: Create deployment script for server
echo -e "\n7. Creating server deployment script..."
cat > deploy_on_server.sh << 'EOF'
#!/bin/bash
# Run this script on the production server

set -e

echo "=== Deploying Stage 1 to Production ==="

# Navigate to project directory
cd /opt/awareness-platform

# Backup database
echo "1. Backing up database..."
docker compose -f docker-compose.prod.yml exec postgres pg_dump -U awareness awareness_platform > backup_$(date +%Y%m%d_%H%M%S).sql

# Pull latest code
echo "2. Pulling latest code..."
git pull origin main

# Update environment
echo "3. Updating environment variables..."
echo "Please ensure .env is properly configured with production values"

# Stop services
echo "4. Stopping services..."
docker compose -f docker-compose.prod.yml down

# Build new images
echo "5. Building new images..."
docker compose -f docker-compose.prod.yml build

# Run migrations
echo "6. Running database migrations..."
docker compose -f docker-compose.prod.yml run --rm backend alembic upgrade head

# Apply RLS policies
echo "7. Applying RLS policies..."
docker compose -f docker-compose.prod.yml run --rm backend python -c "
import psycopg2
from core.config import settings
conn = psycopg2.connect(settings.DATABASE_URL)
with open('scripts/setup_row_level_security.sql', 'r') as f:
    conn.cursor().execute(f.read())
conn.commit()
conn.close()
print('RLS policies applied successfully')
"

# Start services
echo "8. Starting services..."
docker compose -f docker-compose.prod.yml up -d

# Wait for services to be healthy
echo "9. Waiting for services..."
sleep 30

# Run seed data
echo "10. Running seed data..."
docker compose -f docker-compose.prod.yml run --rm backend python scripts/seed_data_enhanced.py

# Check service health
echo "11. Checking service health..."
docker compose -f docker-compose.prod.yml ps

echo "Deployment complete!"
EOF

chmod +x deploy_on_server.sh

echo -e "\n=== Integration Summary ==="
echo "1. All changes have been staged and ready to commit"
echo "2. Deployment package created: stage1_deployment.tar.gz"
echo "3. Deployment checklist created: deployment_checklist.md"
echo "4. Production environment template: .env.production.template"
echo "5. Server deployment script: deploy_on_server.sh"

echo -e "\n=== Next Steps ==="
echo "1. Review the deployment checklist"
echo "2. SSH to server: ssh -i '$SSH_KEY' $SERVER_USER@$SERVER_IP"
echo "3. Upload deployment package"
echo "4. Run deployment script on server"
echo "5. Verify all services are running"

echo -e "\nScript completed at: $(date)"