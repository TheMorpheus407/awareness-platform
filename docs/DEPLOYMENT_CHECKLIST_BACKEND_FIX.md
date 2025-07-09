# Deployment Checklist - Backend Structure Fix

## 🚨 Critical Issue Fixed

The backend code is located in `/backend/backend/` not just `/backend/`. All deployment workflows have been updated to handle this structure correctly.

## ✅ Pre-Deployment Checklist

### 1. Code Structure Verification
- [ ] Verify backend code is in `backend/backend/` directory
- [ ] Ensure `backend/backend/Dockerfile.prod` exists
- [ ] Check that `backend/backend/requirements.txt` is present
- [ ] Confirm `backend/backend/main.py` is the entry point

### 2. GitHub Workflows Updated
- [x] `deploy.yml` - Updated all backend paths
- [x] `deploy-production.yml` - Updated all backend paths
- [x] `ci-cd.yml` - Already has correct paths
- [x] Created `verify-production.yml` for post-deployment verification
- [x] Created `deployment-health-monitor.yml` for continuous monitoring

### 3. Docker Configuration
- [ ] Docker build context: `./backend/backend`
- [ ] Dockerfile path: `./backend/backend/Dockerfile.prod`
- [ ] Working directory in container: `/app`
- [ ] Python path includes `/app`

## 🚀 Deployment Process

### Step 1: Verify Local Build
```bash
# Test building the backend image locally
cd backend/backend
docker build -f Dockerfile.prod -t test-backend .

# Verify the image structure
docker run --rm test-backend ls -la /app/
docker run --rm test-backend python -c "import main"
```

### Step 2: Push to GitHub
```bash
git add .
git commit -m "fix: Update deployment workflows for correct backend structure"
git push origin main
```

### Step 3: Monitor Deployment
1. Watch GitHub Actions: https://github.com/TheMorpheus407/AwarenessSchulungen/actions
2. Check the deployment workflow progress
3. Verify all tests pass
4. Confirm Docker images are built and pushed

### Step 4: Production Verification
After deployment completes:
1. Check API health: https://bootstrap-awareness.de/api/health
2. Check frontend: https://bootstrap-awareness.de
3. Test login functionality
4. Verify database connectivity via extended health check

## 🔧 Troubleshooting

### If Backend Fails to Start

1. **SSH to server and check logs:**
```bash
ssh ubuntu@83.228.205.20
cd /opt/awareness
sudo docker-compose logs --tail=100 backend
```

2. **Run the fix script:**
```bash
sudo chmod +x scripts/fix-backend-structure.sh
sudo ./scripts/fix-backend-structure.sh
```

3. **Manual fix if needed:**
```bash
# Stop backend
sudo docker-compose stop backend
sudo docker-compose rm -f backend

# Pull latest image
sudo docker-compose pull backend

# Start with proper environment
sudo docker-compose up -d backend

# Check logs
sudo docker-compose logs -f backend
```

### Common Issues and Solutions

1. **"Module not found" errors**
   - Issue: Python can't find the application modules
   - Solution: Ensure PYTHONPATH=/app in Dockerfile

2. **"No such file or directory" for scripts**
   - Issue: Scripts path is incorrect
   - Solution: Use absolute path /app/scripts/

3. **Database connection fails**
   - Issue: Wrong database URL format
   - Solution: Use postgresql+asyncpg:// for async connections

4. **Import errors in production**
   - Issue: Relative imports failing
   - Solution: Use absolute imports from app root

## 📊 Monitoring

### Automated Monitoring
- GitHub Actions runs health checks every 30 minutes
- Deployment verification runs after each deployment
- Alerts created as GitHub issues on failure

### Manual Checks
```bash
# API Health
curl https://bootstrap-awareness.de/api/health | jq '.'

# Extended Health (includes DB and Redis)
curl https://bootstrap-awareness.de/api/health/extended | jq '.'

# Test an API endpoint
curl https://bootstrap-awareness.de/api/v1/companies?skip=0&limit=1 | jq '.'
```

## 🎯 Success Criteria

A successful deployment meets these criteria:
1. ✅ All GitHub Actions workflows pass
2. ✅ Backend container is running without restarts
3. ✅ API health endpoint returns 200 OK
4. ✅ Database migrations applied successfully
5. ✅ Frontend loads without errors
6. ✅ Users can log in successfully
7. ✅ No 500 errors in logs

## 📝 Post-Deployment Tasks

1. [ ] Verify all features work as expected
2. [ ] Check application logs for any warnings
3. [ ] Monitor performance metrics
4. [ ] Update status page if applicable
5. [ ] Notify team of successful deployment

## 🆘 Emergency Rollback

If critical issues occur:

```bash
# SSH to server
ssh ubuntu@83.228.205.20

# Navigate to deployment directory
cd /opt/awareness

# Run rollback workflow from GitHub Actions
# OR manually restore from backup:
sudo cp /opt/awareness-backup-*/docker-compose.yml .
sudo cp /opt/awareness-backup-*/.env .
sudo docker-compose pull
sudo docker-compose up -d
```

---

**Note:** This checklist specifically addresses the backend structure issue where the actual backend code is in a nested directory. All workflows have been updated to use the correct paths.