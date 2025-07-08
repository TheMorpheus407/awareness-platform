# Deployment with GitHub Actions

## Overview

The Awareness Platform uses GitHub Actions for continuous integration and deployment. The pipeline automatically tests, builds, and deploys code changes to production.

## Pipeline Architecture

```
[Code Push] → [Tests] → [Build] → [Deploy to Production]
     ↓           ↓         ↓              ↓
   GitHub    CI/CD      Docker       Production
   Actions   Tests      Images        Server
```

## Workflows

### 1. Main CI/CD Pipeline
- **Trigger**: Push to `main` branch
- **Steps**:
  1. Run backend tests (pytest + coverage)
  2. Run frontend tests (vitest + TypeScript)
  3. Run E2E tests (Playwright)
  4. Build Docker images
  5. Push to GitHub Container Registry
  6. Deploy to production server

### 2. Pull Request Checks
- **Trigger**: Pull request events
- **Checks**:
  - Code formatting (Black, ESLint)
  - Type checking (mypy, TypeScript)
  - Security scanning (Trivy)
  - Migration testing

### 3. Security Scans
- **Trigger**: Weekly schedule (Mondays 2 AM UTC)
- **Scans**:
  - Vulnerability scanning
  - Secret detection
  - CodeQL analysis

## Setup Instructions

### 1. Configure GitHub Secrets

Add these secrets in repository settings:

```bash
# Production server details
PRODUCTION_HOST=83.228.205.20
PRODUCTION_USER=root
PRODUCTION_SSH_KEY=<contents of bootstrap-awareness private key.txt>

# Database configuration
PRODUCTION_DATABASE_URL=postgresql://awareness_user:PASSWORD@postgres:5432/awareness_db

# Security
PRODUCTION_SECRET_KEY=<generate with: openssl rand -hex 32>
```

### 2. Prepare Production Server

SSH into the production server and run:

```bash
# Install Docker and Docker Compose
curl -fsSL https://get.docker.com | sh
apt-get install docker-compose-plugin

# Create deployment directory
mkdir -p /opt/awareness-platform
cd /opt/awareness-platform

# Clone repository
git clone https://github.com/TheMorpheus407/awareness-platform.git .

# Create necessary directories
mkdir -p /var/log/awareness-platform
mkdir -p /var/backups/awareness-platform

# Set up environment file
cp deployment/.env.production.template .env
# Edit .env with production values
```

### 3. Initial Manual Deployment

Test the deployment manually first:

```bash
cd /opt/awareness-platform
./deployment/scripts/deploy-production.sh
```

### 4. Enable GitHub Actions

1. Go to repository Settings → Actions → General
2. Ensure "Actions permissions" is set to "Allow all actions"
3. Push to main branch to trigger deployment

## Deployment Process

### Automatic Deployment

Every push to `main` branch triggers:

1. **Test Phase**
   - Unit tests with coverage
   - Integration tests
   - E2E tests
   - Type checking

2. **Build Phase**
   - Build optimized frontend
   - Build backend Docker image
   - Push to registry

3. **Deploy Phase**
   - SSH to production server
   - Pull latest images
   - Run database migrations
   - Apply RLS policies
   - Health check
   - Cleanup old images

### Manual Deployment

If needed, deploy manually:

```bash
# On production server
cd /opt/awareness-platform
git pull origin main
./deployment/scripts/deploy-production.sh
```

## Rollback Procedure

If deployment fails:

1. **Automatic Rollback**
   - Health check failure triggers automatic rollback
   - Previous containers are restored

2. **Manual Rollback**
   ```bash
   # List backups
   ls -la /var/backups/awareness-platform/
   
   # Restore database
   docker-compose -f docker-compose.prod.yml exec postgres psql -U postgres awareness_db < /var/backups/awareness-platform/db_backup_TIMESTAMP.sql
   
   # Restore code
   cd /opt/awareness-platform
   git checkout <previous-commit>
   docker-compose -f docker-compose.prod.yml up -d
   ```

## Monitoring

### GitHub Actions Dashboard
- View runs: https://github.com/TheMorpheus407/awareness-platform/actions
- Check logs for failures
- Monitor deployment time

### Production Health
- Health endpoint: https://bootstrap-awareness.de/api/health
- Container status: `docker-compose -f docker-compose.prod.yml ps`
- Logs: `docker-compose -f docker-compose.prod.yml logs -f`

### Alerts
- GitHub Actions sends email on failure
- Optional: Configure Slack/Discord webhooks

## Troubleshooting

### Common Issues

1. **SSH Authentication Failed**
   - Check PRODUCTION_SSH_KEY secret
   - Verify SSH key permissions on server

2. **Docker Build Failed**
   - Check Dockerfile syntax
   - Verify base image availability

3. **Migration Failed**
   - Check database connectivity
   - Review migration files
   - Check for conflicts

4. **Health Check Failed**
   - Check container logs
   - Verify environment variables
   - Check database connection

### Debug Commands

```bash
# Check GitHub Actions logs
gh run list
gh run view <run-id>

# On production server
docker-compose -f docker-compose.prod.yml logs backend
docker-compose -f docker-compose.prod.yml exec backend python -c "from core.config import settings; print(settings)"
```

## Security Considerations

1. **Secrets Management**
   - Never commit secrets to repository
   - Rotate secrets regularly
   - Use GitHub's secret scanning

2. **Access Control**
   - Limit who can push to main
   - Review pull requests before merge
   - Enable branch protection

3. **Container Security**
   - Regular image updates
   - Vulnerability scanning
   - Minimal base images

## Performance Optimization

1. **Build Caching**
   - Docker layer caching
   - Dependency caching
   - Parallel job execution

2. **Deployment Speed**
   - Pre-built images
   - Rolling updates
   - Health check optimization

## Future Improvements

- [ ] Blue-green deployments
- [ ] Kubernetes migration
- [ ] Automated performance testing
- [ ] Canary releases
- [ ] Multi-region deployment