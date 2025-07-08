# Deployment Guide for Awareness Platform

## Current Status
- **Git Status**: 6 commits ready to push to origin/main
- **GitHub Repository**: https://github.com/TheMorpheus407/awareness-platform
- **Production URL**: https://bootstrap-awareness.de
- **Server IP**: Will be deployed via SSH using stored keys

## Step 1: Push Code to GitHub

Since GitHub authentication is required, you need to:

1. **Option A: Use GitHub Personal Access Token**
   ```bash
   # Create a token at: https://github.com/settings/tokens
   # Select scopes: repo, workflow
   
   # Push using token
   git push https://YOUR_GITHUB_USERNAME:YOUR_TOKEN@github.com/TheMorpheus407/awareness-platform.git main
   ```

2. **Option B: Use GitHub CLI**
   ```bash
   # Login to GitHub
   gh auth login
   
   # Push changes
   git push origin main
   ```

3. **Option C: Use Git Credential Manager**
   ```bash
   # This will prompt for username and password/token
   git push origin main
   ```

## Step 2: Configure GitHub Secrets

### Required Secrets (Add at https://github.com/TheMorpheus407/awareness-platform/settings/secrets/actions)

1. **SSH_PRIVATE_KEY** (Secret)
   - Copy entire content from `bootstrap-awareness private key.txt`
   - Include BEGIN and END lines

### Required Variables (Add at https://github.com/TheMorpheus407/awareness-platform/settings/variables/actions)

2. **Database Configuration**
   ```
   DB_USER=awareness
   DB_PASSWORD=[Generate secure password]
   DATABASE_URL=postgresql://awareness:[PASSWORD]@postgres:5432/awareness_platform
   ```

3. **Security Keys**
   ```bash
   # Generate SECRET_KEY
   openssl rand -hex 32
   
   # Generate JWT_SECRET_KEY
   openssl rand -hex 32
   ```

4. **Redis Configuration**
   ```
   REDIS_PASSWORD=[Generate secure password]
   REDIS_URL=redis://default:[PASSWORD]@redis:6379
   ```

5. **Application URLs**
   ```
   API_URL=https://api.bootstrap-awareness.de
   FRONTEND_URL=https://bootstrap-awareness.de
   ALLOWED_HOSTS=bootstrap-awareness.de,www.bootstrap-awareness.de,api.bootstrap-awareness.de
   CORS_ORIGINS=https://bootstrap-awareness.de,https://www.bootstrap-awareness.de
   ```

6. **Email Configuration**
   ```
   EMAIL_FROM=noreply@bootstrap-awareness.de
   EMAIL_FROM_NAME=Bootstrap Awareness Platform
   ```

### Optional Secrets (Can be added later)
- YOUTUBE_API_KEY
- SENDGRID_API_KEY
- STRIPE_SECRET_KEY
- STRIPE_PUBLIC_KEY
- STRIPE_WEBHOOK_SECRET
- SENTRY_DSN
- GRAFANA_ADMIN_PASSWORD

## Step 3: Trigger Deployment

1. Go to: https://github.com/TheMorpheus407/awareness-platform/actions
2. Select "Deploy to Production" workflow
3. Click "Run workflow" -> Select branch "main" -> "Run workflow"

## Step 4: Monitor Deployment

### GitHub Actions
- Watch progress at: https://github.com/TheMorpheus407/awareness-platform/actions
- Check logs for any errors
- Deployment includes:
  - Running tests
  - Building Docker images
  - Pushing to GitHub Container Registry
  - Deploying to server via SSH
  - Health check verification

### Expected Workflow Stages
1. **Test** - Runs Python and Frontend tests
2. **Build** - Creates Docker images for backend and frontend
3. **Deploy** - Deploys to production server and runs health checks

### Troubleshooting

**Push Failed**
- Ensure you have write access to the repository
- Use a personal access token with 'repo' and 'workflow' scopes

**Deployment Failed at SSH**
- Verify SSH_PRIVATE_KEY secret is correctly set
- Check server is accessible at bootstrap-awareness.de

**Docker Build Failed**
- Check Dockerfile syntax in backend/ and frontend/
- Ensure all dependencies are specified

**Health Check Failed**
- SSH into server: `ssh root@bootstrap-awareness.de`
- Check logs: `docker-compose logs`
- Verify services are running: `docker-compose ps`

## Step 5: Post-Deployment Verification

1. **Check Application**
   ```bash
   curl https://bootstrap-awareness.de/health
   curl https://api.bootstrap-awareness.de/health
   ```

2. **Check SSL Certificates**
   - Frontend: https://bootstrap-awareness.de
   - API: https://api.bootstrap-awareness.de

3. **Database Connection**
   - Ensure migrations ran successfully
   - Check database connectivity from backend

## Quick Reference Commands

```bash
# Generate secure passwords
openssl rand -base64 32 | tr -d '=' | tr '+/' '-_' | cut -c1-24

# Generate secret keys
openssl rand -hex 32

# Check GitHub Actions status
gh run list --workflow=deploy.yml

# View deployment logs
gh run view [RUN_ID] --log

# SSH to production server (after setup)
ssh root@bootstrap-awareness.de
```

## Support Scripts

- `scripts/setup-github-secrets.sh` - Interactive guide for secrets
- `scripts/github-secrets-template.json` - JSON template with all secrets
- `deployment/scripts/deploy.sh` - Server-side deployment script

## Next Steps

1. Push code to GitHub (requires authentication)
2. Configure all required secrets in GitHub
3. Trigger manual deployment
4. Verify application is running
5. Configure monitoring and alerts