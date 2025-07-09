# 🚨 Production Fix SSH Commands

**Server**: 83.228.205.20  
**User**: ubuntu  
**Last Updated**: 2025-07-09

## 🔧 Quick Fix Commands

### 1. Connect to Server
```bash
ssh ubuntu@83.228.205.20
```

### 2. Navigate to Application Directory
```bash
cd /opt/awareness
```

### 3. Fix Backend Path Issue (CRITICAL)

The backend code is in `backend/backend/` but Docker expects it in `backend/`. Fix:

```bash
# Option A: Create symbolic link (Quick fix)
sudo ln -sf backend/backend/* backend/

# Option B: Update Docker Compose (Proper fix)
sudo nano docker-compose.prod.yml
# Change backend volumes from:
#   - ./backend:/app
# To:
#   - ./backend/backend:/app
```

### 4. Restart Services
```bash
sudo docker-compose -f docker-compose.prod.yml down
sudo docker-compose -f docker-compose.prod.yml up -d
```

### 5. Initialize Database
```bash
# Run migrations
sudo docker exec backend-container alembic upgrade head

# If migrations fail due to enum issues:
sudo docker exec backend-container python scripts/fix_enum_conflicts.py
sudo docker exec backend-container alembic upgrade head

# Initialize tables
sudo docker exec backend-container python scripts/init_db_tables.py

# Create admin user
sudo docker exec backend-container python scripts/create_admin_user.py
```

### 6. Verify Services
```bash
# Check all containers are running
sudo docker ps

# Check backend health
curl http://localhost:8000/api/health

# Check frontend
curl http://localhost

# Check logs if needed
sudo docker logs backend-container
sudo docker logs frontend-container
sudo docker logs nginx-container
```

## 🔴 If Automated Fix Fails

### Manual Backend Fix
```bash
# Create corrected backend Dockerfile
cat > /opt/awareness/backend/Dockerfile.prod.fixed << 'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

# Rebuild backend locally
cd /opt/awareness
sudo docker build -f backend/Dockerfile.prod.fixed -t backend-fixed .
sudo docker tag backend-fixed ghcr.io/themorpheus407/awareness-platform/backend:latest
```

### Manual Frontend Fix
```bash
# Verify frontend build
sudo docker exec frontend-container ls -la /usr/share/nginx/html/

# If showing Vite template, rebuild:
cd /opt/awareness/frontend
sudo docker build -t frontend-fixed .
sudo docker tag frontend-fixed ghcr.io/themorpheus407/awareness-platform/frontend:latest
```

## 🚀 Emergency Rollback

If everything fails:

```bash
# Stop all containers
sudo docker-compose -f docker-compose.prod.yml down

# Restore from backup
sudo cp -r /opt/awareness/backup-*/* /opt/awareness/

# Use working images (if available)
sudo docker-compose -f docker-compose.prod.yml up -d
```

## 📋 Verification Checklist

- [ ] All containers running: `sudo docker ps`
- [ ] Backend responds: `curl http://localhost:8000/api/health`
- [ ] Frontend loads: `curl http://localhost | grep -v "Vite"`
- [ ] Database connected: `sudo docker exec backend-container python -c "from db.session import get_db; print('DB OK')"`
- [ ] SSL working: `curl https://bootstrap-awareness.de`

## 🔍 Debug Commands

```bash
# Check backend structure
sudo docker exec backend-container ls -la /app/

# Check frontend files
sudo docker exec frontend-container ls -la /usr/share/nginx/html/

# Database connection test
sudo docker exec postgres-container psql -U postgres -c "\l"

# Check nginx config
sudo docker exec nginx-container nginx -t
```

## ⚡ One-Line Fix Attempt

```bash
cd /opt/awareness && sudo docker-compose -f docker-compose.prod.yml down && sudo ln -sf backend/backend/* backend/ && sudo docker-compose -f docker-compose.prod.yml up -d && sleep 20 && sudo docker exec backend-container alembic upgrade head && echo "✅ Fix complete!"
```