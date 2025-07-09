# 🚨 Emergency Production Fix - SSH Commands

**Server**: 83.228.205.20  
**User**: ubuntu  
**App Directory**: /opt/awareness

## 🔥 Quick Fix Commands (Copy & Paste)

### 1. Connect to Server
```bash
ssh ubuntu@83.228.205.20
```

### 2. Navigate to App Directory
```bash
cd /opt/awareness
```

### 3. Check Current Status
```bash
# See what's running
docker-compose ps

# Check frontend content
docker exec -it awareness_frontend_1 cat /usr/share/nginx/html/index.html | head -20

# Check backend structure
docker exec -it awareness_backend_1 ls -la /app/
```

### 4. Emergency Fix - Rebuild Containers with Correct Paths

```bash
# Create temporary build directory
mkdir -p /tmp/awareness-fix
cd /tmp/awareness-fix

# Create fixed backend Dockerfile
cat > Dockerfile.backend << 'DOCKERFILE'
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y libpq-dev gcc curl && rm -rf /var/lib/apt/lists/*

# Copy requirements first
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy all backend files
COPY backend/ /app/

# Fix the nested structure if it exists
RUN if [ -d "/app/backend" ]; then \
    cp -r /app/backend/* /app/ && \
    rm -rf /app/backend; \
fi

ENV PYTHONPATH=/app
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
DOCKERFILE

# Create fixed frontend Dockerfile  
cat > Dockerfile.frontend << 'DOCKERFILE'
FROM node:20-alpine AS builder
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
ENV VITE_API_URL=https://bootstrap-awareness.de/api
ENV VITE_APP_NAME="Bootstrap Awareness Platform"
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
DOCKERFILE

# Clone the repository to get latest code
git clone https://github.com/TheMorpheus407/awareness-platform.git
cd awareness-platform

# Build fixed images
docker build -f /tmp/awareness-fix/Dockerfile.backend -t awareness-backend:fixed .
docker build -f /tmp/awareness-fix/Dockerfile.frontend -t awareness-frontend:fixed .

# Go back to app directory
cd /opt/awareness

# Update docker-compose to use local images
cp docker-compose.yml docker-compose.yml.backup
sed -i 's|ghcr.io/.*/backend:.*|awareness-backend:fixed|g' docker-compose.yml
sed -i 's|ghcr.io/.*/frontend:.*|awareness-frontend:fixed|g' docker-compose.yml

# Restart with new images
docker-compose down
docker-compose up -d

# Wait for services
sleep 30

# Initialize database
docker-compose exec -T backend alembic upgrade head
```

### 5. Alternative: Manual Container Fixes

If rebuilding doesn't work, try these manual fixes:

```bash
# Fix Frontend (replace Vite template with a temporary page)
docker exec -it awareness_frontend_1 sh -c 'cat > /usr/share/nginx/html/index.html << "HTML"
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bootstrap Awareness Platform</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
        h1 { color: #2563eb; }
        .status { background: #fef3c7; padding: 20px; border-radius: 8px; margin: 20px auto; max-width: 600px; }
    </style>
</head>
<body>
    <h1>Bootstrap Awareness Platform</h1>
    <div class="status">
        <h2>🚧 Wartungsarbeiten</h2>
        <p>Die Plattform wird gerade aktualisiert. Bitte versuchen Sie es in wenigen Minuten erneut.</p>
        <p>Bei Fragen kontaktieren Sie uns unter: hallo@bootstrap-awareness.de</p>
    </div>
</body>
</html>
HTML'

# Fix Backend paths
docker exec -it awareness_backend_1 sh -c '
if [ -d "/app/backend" ]; then
    echo "Fixing backend paths..."
    cp -r /app/backend/* /app/
    export PYTHONPATH=/app
fi
'

# Restart backend with correct path
docker-compose restart backend
```

### 6. Verify Fixes

```bash
# Check if frontend is fixed
curl -s https://bootstrap-awareness.de/ | grep -o "<title>.*</title>"

# Check API health
curl -s https://bootstrap-awareness.de/api/health

# Check logs
docker-compose logs --tail=50 backend
docker-compose logs --tail=50 frontend
```

### 7. If All Else Fails - Rollback

```bash
# Restore original docker-compose
cp docker-compose.yml.backup docker-compose.yml

# Pull original images
docker-compose pull

# Restart
docker-compose down
docker-compose up -d
```

## 📞 Debug Information Commands

```bash
# Full diagnosis
docker ps -a
docker-compose logs --tail=100
df -h
free -m
```

## 🔧 Common Issues & Solutions

### Issue: "No such file or directory"
```bash
# Backend can't find main.py
docker exec -it awareness_backend_1 find /app -name "main.py" -type f
```

### Issue: "Permission denied"
```bash
# Fix permissions
sudo chown -R ubuntu:ubuntu /opt/awareness
sudo chmod -R 755 /opt/awareness
```

### Issue: "Address already in use"
```bash
# Find and kill processes using ports
sudo lsof -i :80
sudo lsof -i :443
# Kill with: sudo kill -9 <PID>
```

## 🎯 Expected Result

After running these fixes, you should see:
- ✅ https://bootstrap-awareness.de shows the actual platform (not Vite template)
- ✅ https://bootstrap-awareness.de/api/health returns `{"status":"healthy"}`
- ✅ https://bootstrap-awareness.de/api/docs shows the API documentation
- ✅ All containers are running and healthy

## 📧 If you need help
Contact: support@bootstrap-awareness.de