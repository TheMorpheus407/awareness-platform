#!/bin/bash
set -e

echo "🚀 Cybersecurity Awareness Platform Deployment Script"
echo "=================================================="

# Configuration
REMOTE_USER=${REMOTE_USER:-ubuntu}
REMOTE_HOST=${REMOTE_HOST:-}
REMOTE_PATH=${REMOTE_PATH:-/opt/awareness-platform}
SSH_KEY_PATH=".ssh/bootstrap-awareness private key.txt"

# Check if remote host is provided
if [ -z "$REMOTE_HOST" ]; then
    echo "❌ Error: REMOTE_HOST environment variable not set"
    echo "Usage: REMOTE_HOST=your-server.com ./deploy.sh"
    exit 1
fi

# Check if SSH key exists
if [ ! -f "$SSH_KEY_PATH" ]; then
    echo "❌ Error: SSH key not found at $SSH_KEY_PATH"
    exit 1
fi

# Fix SSH key permissions
chmod 600 "$SSH_KEY_PATH"

echo "📦 Preparing deployment package..."

# Create deployment archive
tar -czf deployment.tar.gz \
    --exclude=node_modules \
    --exclude=venv \
    --exclude=__pycache__ \
    --exclude=.git \
    --exclude=.env \
    --exclude=*.db \
    --exclude=*.log \
    --exclude=deployment.tar.gz \
    .

echo "🔐 Connecting to $REMOTE_HOST..."

# Copy deployment package
scp -i "$SSH_KEY_PATH" deployment.tar.gz "$REMOTE_USER@$REMOTE_HOST:/tmp/"

# Deploy on remote server
ssh -i "$SSH_KEY_PATH" "$REMOTE_USER@$REMOTE_HOST" << 'ENDSSH'
set -e

echo "🏗️  Setting up application directory..."

# Create application directory
sudo mkdir -p /opt/awareness-platform
sudo chown $USER:$USER /opt/awareness-platform
cd /opt/awareness-platform

# Extract deployment package
tar -xzf /tmp/deployment.tar.gz
rm /tmp/deployment.tar.gz

# Check if .env exists, if not create from example
if [ ! -f .env ]; then
    cp .env.example .env
    echo "⚠️  Created .env from .env.example - Please configure it!"
fi

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "🐳 Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
fi

# Install Docker Compose if not present
if ! command -v docker-compose &> /dev/null; then
    echo "🐳 Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

echo "🚀 Starting services..."

# Stop existing services
docker-compose -f docker-compose.prod.yml down || true

# Build and start services
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# Wait for database to be ready
echo "⏳ Waiting for database..."
sleep 10

# Run migrations
echo "🗄️  Running database migrations..."
docker-compose -f docker-compose.prod.yml exec -T backend alembic upgrade head

# Show service status
echo "✅ Deployment complete!"
echo ""
docker-compose -f docker-compose.prod.yml ps

echo ""
echo "📋 Next steps:"
echo "1. Configure .env file with production settings"
echo "2. Set up SSL certificates with certbot"
echo "3. Update DNS to point to this server"
echo "4. Create admin user: docker-compose exec backend python create_admin_user.py"

ENDSSH

# Cleanup
rm deployment.tar.gz

echo "✅ Deployment script completed!"