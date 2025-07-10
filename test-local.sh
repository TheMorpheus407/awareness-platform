#!/bin/bash
set -e

echo "🧪 Testing Local Setup"
echo "===================="

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed"
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"

# Check .env file
if [ ! -f .env ]; then
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
fi

echo "🐳 Starting services with Docker Compose..."
docker-compose down || true
docker-compose up -d

echo "⏳ Waiting for services to start..."
sleep 15

# Check if services are running
echo ""
echo "📊 Service Status:"
docker-compose ps

# Check backend health
echo ""
echo "🔍 Checking backend health..."
curl -f http://localhost:8000/api/health || echo "❌ Backend health check failed"

# Check frontend
echo ""
echo "🔍 Checking frontend..."
curl -f http://localhost:5173/ > /dev/null && echo "✅ Frontend is responding" || echo "❌ Frontend check failed"

# Show logs if there are issues
if ! curl -sf http://localhost:8000/api/health > /dev/null; then
    echo ""
    echo "📋 Backend logs:"
    docker-compose logs --tail=50 backend
fi

echo ""
echo "🔗 Access points:"
echo "- Frontend: http://localhost:5173"
echo "- Backend API: http://localhost:8000"
echo "- API Docs: http://localhost:8000/api/docs"
echo ""
echo "💡 To view logs: docker-compose logs -f [service]"
echo "💡 To stop: docker-compose down"