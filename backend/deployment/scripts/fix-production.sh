#!/bin/bash
# Emergency production fix script

set -e

echo "Emergency Production Fix Script"
echo "==============================="

# SSH into server and fix issues
ssh ubuntu@83.228.205.20 << 'EOF'
set -e

echo "1. Checking Docker containers..."
sudo docker ps -a

echo "2. Checking logs..."
sudo docker logs awareness_backend_1 --tail 50 2>&1 | grep -i error || true

echo "3. Creating superuser..."
sudo docker exec -it awareness_backend_1 python scripts/create_superuser.py || true

echo "4. Checking environment..."
sudo docker exec awareness_backend_1 env | grep -E "DATABASE_URL|CORS" || true

echo "5. Restarting containers..."
cd /opt/awareness
sudo docker-compose -f docker-compose.prod.ghcr.yml restart

echo "6. Waiting for services..."
sleep 30

echo "7. Final health check..."
curl -s http://localhost:8000/api/health || echo "Health check failed"

EOF