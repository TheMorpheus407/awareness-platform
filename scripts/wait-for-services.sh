#!/bin/bash
set -e

echo "Waiting for services to be ready..."

# Wait for PostgreSQL
echo -n "Waiting for PostgreSQL..."
timeout=60
while ! docker-compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; do
    timeout=$((timeout - 1))
    if [ $timeout -eq 0 ]; then
        echo " FAILED"
        echo "PostgreSQL did not become ready in time"
        exit 1
    fi
    echo -n "."
    sleep 1
done
echo " READY"

# Wait for Redis
echo -n "Waiting for Redis..."
timeout=60
while ! docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; do
    timeout=$((timeout - 1))
    if [ $timeout -eq 0 ]; then
        echo " FAILED"
        echo "Redis did not become ready in time"
        exit 1
    fi
    echo -n "."
    sleep 1
done
echo " READY"

# Wait for Backend API
echo -n "Waiting for Backend API..."
timeout=120
while ! curl -f http://localhost:8000/health > /dev/null 2>&1; do
    timeout=$((timeout - 1))
    if [ $timeout -eq 0 ]; then
        echo " FAILED"
        echo "Backend API did not become ready in time"
        docker-compose logs backend
        exit 1
    fi
    echo -n "."
    sleep 1
done
echo " READY"

# Wait for Frontend
echo -n "Waiting for Frontend..."
timeout=60
while ! curl -f http://localhost:80 > /dev/null 2>&1; do
    timeout=$((timeout - 1))
    if [ $timeout -eq 0 ]; then
        echo " FAILED"
        echo "Frontend did not become ready in time"
        docker-compose logs frontend
        exit 1
    fi
    echo -n "."
    sleep 1
done
echo " READY"

# Run database migrations
echo "Running database migrations..."
docker-compose exec -T backend alembic upgrade head

echo "All services are ready!"

# Display service URLs
echo ""
echo "Service URLs:"
echo "- Frontend: http://localhost:80"
echo "- Backend API: http://localhost:8000"
echo "- API Documentation: http://localhost:8000/docs"
echo ""