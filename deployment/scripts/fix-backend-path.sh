#!/bin/bash
# Fix Backend Path Issue
# This script fixes the backend/backend path issue in production

set -e

echo "🔧 Backend Path Fix Script"
echo "========================="
echo ""

# Check current directory structure in the repository
echo "1. 📁 Checking repository structure..."
echo "------------------------------------"

if [ -d "backend/backend" ]; then
    echo "❌ Found backend/backend structure (new structure)"
    echo "   The backend code is in a nested directory"
    
    echo ""
    echo "2. 🐳 Creating fixed Dockerfile.prod for backend..."
    echo "-------------------------------------------------"
    
    cat > backend/Dockerfile.prod.fixed << 'EOF'
# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the entire backend directory (includes the nested backend/)
COPY . /app/

# If the structure is backend/backend/, we need to work with that
RUN if [ -d "/app/backend" ]; then \
        echo "Found nested backend structure, adjusting..." && \
        cp -r /app/backend/* /app/ && \
        rm -rf /app/backend; \
    fi

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy from builder
COPY --from=builder /app /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

    echo "✅ Created fixed Dockerfile"
    
elif [ -d "backend" ]; then
    echo "✅ Found standard backend structure"
    echo "   The backend code is in the expected location"
else
    echo "❌ Cannot find backend directory!"
    exit 1
fi

echo ""
echo "3. 🐳 Creating fixed Frontend Dockerfile..."
echo "-----------------------------------------"

cat > frontend/Dockerfile.prod.fixed << 'EOF'
# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies (including dev dependencies for build)
RUN npm ci

# Copy source files
COPY . .

# Build the app with production configuration
ENV NODE_ENV=production
ENV VITE_API_URL=https://bootstrap-awareness.de/api
ENV VITE_APP_NAME="Bootstrap Awareness Platform"

# Build the application
RUN npm run build

# Verify build output
RUN ls -la dist/ && \
    if [ ! -f dist/index.html ]; then \
        echo "❌ Build failed: index.html not found!" && exit 1; \
    fi && \
    if grep -q "Vite + React" dist/index.html; then \
        echo "❌ Build failed: Still contains Vite template!" && exit 1; \
    fi

# Production stage
FROM nginx:alpine

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Verify files were copied
RUN ls -la /usr/share/nginx/html/

# Add health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/ || exit 1

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
EOF

echo "✅ Created fixed Frontend Dockerfile"

echo ""
echo "4. 📝 Creating deployment instructions..."
echo "----------------------------------------"

cat > PRODUCTION_FIX_INSTRUCTIONS.md << 'EOF'
# Production Fix Instructions

## Problem Summary
1. Backend code is in `backend/backend/` instead of `backend/`
2. Frontend is showing Vite template instead of the actual app
3. Database is not initialized
4. API routes return 404 (except /api/health)

## Solution Steps

### 1. Build Fixed Images Locally
```bash
# Build backend with path fix
cd backend
docker build -t ghcr.io/themorpheus407/awareness-platform/backend:fixed -f Dockerfile.prod.fixed .

# Build frontend with proper production build
cd ../frontend
docker build -t ghcr.io/themorpheus407/awareness-platform/frontend:fixed -f Dockerfile.prod.fixed .

# Push to registry (requires authentication)
docker push ghcr.io/themorpheus407/awareness-platform/backend:fixed
docker push ghcr.io/themorpheus407/awareness-platform/frontend:fixed
```

### 2. Deploy Fixed Images on Server
```bash
# SSH to server
ssh ubuntu@83.228.205.20

# Navigate to app directory
cd /opt/awareness

# Update docker-compose.yml to use :fixed tags
sed -i 's/:latest/:fixed/g' docker-compose.yml

# Pull and restart
docker-compose pull
docker-compose down
docker-compose up -d

# Initialize database
docker-compose exec backend alembic upgrade head
docker-compose exec backend python scripts/create_production_admin.py
```

### 3. Verify Deployment
```bash
# Check if frontend is correct
curl https://bootstrap-awareness.de/ | grep -o "<title>.*</title>"
# Should show: <title>Bootstrap Awareness Platform</title>

# Check API endpoints
curl https://bootstrap-awareness.de/api/health
curl https://bootstrap-awareness.de/api/v1/companies
```

## Alternative: Emergency Fix Script
Run on the production server:
```bash
wget https://raw.githubusercontent.com/TheMorpheus407/awareness-platform/main/deployment/scripts/fix-production-deployment.sh
chmod +x fix-production-deployment.sh
sudo ./fix-production-deployment.sh
```
EOF

echo "✅ Created fix instructions"

echo ""
echo "5. 🚀 Next Steps:"
echo "-----------------"
echo "1. Review the fixed Dockerfiles"
echo "2. Build new images with the fixes:"
echo "   docker build -t ghcr.io/themorpheus407/awareness-platform/backend:fixed -f backend/Dockerfile.prod.fixed backend/"
echo "   docker build -t ghcr.io/themorpheus407/awareness-platform/frontend:fixed -f frontend/Dockerfile.prod.fixed frontend/"
echo "3. Push to registry or deploy directly to server"
echo "4. Run the fix-production-deployment.sh script on the server"
echo ""
echo "📋 Fix preparation complete!"