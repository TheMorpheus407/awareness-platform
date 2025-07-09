#!/bin/bash
# Production Diagnosis Script
# This script diagnoses common production issues

echo "🔍 Bootstrap Awareness Production Diagnosis Script"
echo "================================================="
echo ""

# Check if we're running on the production server
if [[ $(hostname) != *"awareness"* ]]; then
    echo "⚠️  This script should be run on the production server"
    echo "   Current hostname: $(hostname)"
fi

echo "1. 🐳 Docker Container Status:"
echo "------------------------------"
docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""

echo "2. 📁 Frontend Container Check:"
echo "------------------------------"
FRONTEND_CONTAINER=$(docker ps -q --filter "name=frontend")
if [ -n "$FRONTEND_CONTAINER" ]; then
    echo "✅ Frontend container found: $FRONTEND_CONTAINER"
    echo "📄 Checking index.html content:"
    docker exec $FRONTEND_CONTAINER head -20 /usr/share/nginx/html/index.html
    echo ""
    echo "📂 Frontend files:"
    docker exec $FRONTEND_CONTAINER ls -la /usr/share/nginx/html/
else
    echo "❌ Frontend container not found!"
fi
echo ""

echo "3. 🔧 Backend Container Check:"
echo "------------------------------"
BACKEND_CONTAINER=$(docker ps -q --filter "name=backend")
if [ -n "$BACKEND_CONTAINER" ]; then
    echo "✅ Backend container found: $BACKEND_CONTAINER"
    echo "📊 Backend health check:"
    docker exec $BACKEND_CONTAINER curl -s http://localhost:8000/api/health || echo "❌ Health check failed"
    echo ""
    echo "🔍 Backend logs (last 20 lines):"
    docker logs --tail 20 $BACKEND_CONTAINER
    echo ""
    echo "📁 Backend file structure:"
    docker exec $BACKEND_CONTAINER ls -la /app/
else
    echo "❌ Backend container not found!"
fi
echo ""

echo "4. 🌐 Nginx Configuration Check:"
echo "---------------------------------"
NGINX_CONTAINER=$(docker ps -q --filter "name=nginx")
if [ -n "$NGINX_CONTAINER" ]; then
    echo "✅ Nginx container found: $NGINX_CONTAINER"
    echo "📝 Nginx configuration test:"
    docker exec $NGINX_CONTAINER nginx -t
    echo ""
    echo "📋 Nginx upstream configuration:"
    docker exec $NGINX_CONTAINER cat /etc/nginx/nginx.conf | grep -A5 "upstream"
else
    echo "❌ Nginx container not found!"
fi
echo ""

echo "5. 🗄️ Database Check:"
echo "--------------------"
POSTGRES_CONTAINER=$(docker ps -q --filter "name=postgres")
if [ -n "$POSTGRES_CONTAINER" ]; then
    echo "✅ Postgres container found: $POSTGRES_CONTAINER"
    echo "📊 Database connection test:"
    docker exec $POSTGRES_CONTAINER pg_isready -U awareness_user
    echo ""
    echo "📋 List of databases:"
    docker exec $POSTGRES_CONTAINER psql -U awareness_user -c "\l" 2>/dev/null || echo "❌ Cannot list databases"
else
    echo "❌ Postgres container not found!"
fi
echo ""

echo "6. 🔍 Docker Compose Configuration:"
echo "-----------------------------------"
if [ -f docker-compose.yml ]; then
    echo "✅ docker-compose.yml found"
    echo "📋 Services defined:"
    grep -E "^\s+[a-z-]+:" docker-compose.yml | sed 's/://' | xargs
    echo ""
    echo "🖼️ Images being used:"
    grep -E "image:" docker-compose.yml | awk '{print $2}'
else
    echo "❌ docker-compose.yml not found!"
fi
echo ""

echo "7. 🌐 External Access Check:"
echo "----------------------------"
echo "🔗 Testing https://bootstrap-awareness.de/api/health"
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" https://bootstrap-awareness.de/api/health
echo ""
echo "🔗 Testing https://bootstrap-awareness.de/"
curl -s https://bootstrap-awareness.de/ | grep -o "<title>.*</title>" | head -1
echo ""

echo "8. 📝 Common Issues Found:"
echo "--------------------------"
ISSUES_FOUND=0

# Check if frontend shows Vite template
if docker exec $FRONTEND_CONTAINER cat /usr/share/nginx/html/index.html 2>/dev/null | grep -q "Vite + React"; then
    echo "❌ Frontend is showing Vite template instead of the app"
    echo "   → Solution: Frontend build may have failed or wrong files were copied"
    ISSUES_FOUND=$((ISSUES_FOUND+1))
fi

# Check if backend has proper file structure
if ! docker exec $BACKEND_CONTAINER ls /app/main.py &>/dev/null; then
    echo "❌ Backend main.py not found in /app/"
    echo "   → Solution: Check if backend files are in correct location"
    ISSUES_FOUND=$((ISSUES_FOUND+1))
fi

# Check database initialization
if ! docker exec $POSTGRES_CONTAINER psql -U awareness_user -d awareness_platform -c "\dt" 2>/dev/null | grep -q "users"; then
    echo "❌ Database tables not initialized"
    echo "   → Solution: Run database migrations"
    ISSUES_FOUND=$((ISSUES_FOUND+1))
fi

if [ $ISSUES_FOUND -eq 0 ]; then
    echo "✅ No common issues detected"
else
    echo ""
    echo "🔧 Found $ISSUES_FOUND issue(s) that need fixing"
fi

echo ""
echo "📋 Diagnosis complete!"
echo "====================="