#!/bin/bash
# Fix production deployment issues for Awareness Platform

set -e

echo "=== Awareness Platform Production Fix Script ==="
echo "This script will fix the production deployment issues"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    print_error "This script must be run as root"
    exit 1
fi

# 1. Fix Nginx Configuration
print_status "Fixing Nginx configuration..."

# Create the corrected nginx config with upstream definitions
cat > /tmp/awareness-platform-prod-fixed.conf << 'EOF'
# Upstream definitions
upstream backend {
    server localhost:8000;
    keepalive 32;
}

upstream frontend {
    server localhost:5173;
    keepalive 32;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name bootstrap-awareness.de www.bootstrap-awareness.de;
    
    # ACME challenge for Let's Encrypt
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    # Redirect all other traffic to HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# Redirect www to non-www
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name www.bootstrap-awareness.de;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/bootstrap-awareness.de/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/bootstrap-awareness.de/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    return 301 https://bootstrap-awareness.de$request_uri;
}

# Main HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name bootstrap-awareness.de;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/bootstrap-awareness.de/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/bootstrap-awareness.de/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Logging
    access_log /var/log/nginx/awareness-access.log;
    error_log /var/log/nginx/awareness-error.log warn;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Frontend root path
    location / {
        # First try to serve from the static build directory
        root /home/awareness/awareness-platform/frontend/dist;
        try_files $uri $uri/ @frontend_proxy;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # Fallback to frontend dev server if needed
    location @frontend_proxy {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
    
    # API endpoints
    location /api {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Disable buffering for SSE/WebSocket
        proxy_buffering off;
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://backend/health;
        access_log off;
    }
    
    location /api/health {
        proxy_pass http://backend/api/health;
        access_log off;
    }
    
    # WebSocket support
    location /ws {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket timeouts
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
    }
    
    # Block access to sensitive files
    location ~ /\. {
        deny all;
    }
}
EOF

# 2. Check and fix backend service
print_status "Checking backend service..."

# Create systemd service for backend if it doesn't exist
if [ ! -f /etc/systemd/system/awareness-backend.service ]; then
    print_status "Creating backend systemd service..."
    cat > /etc/systemd/system/awareness-backend.service << 'EOF'
[Unit]
Description=Awareness Platform Backend
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=awareness
WorkingDirectory=/home/awareness/awareness-platform/backend
Environment="PATH=/home/awareness/.local/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONUNBUFFERED=1"
ExecStart=/home/awareness/awareness-platform/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    systemctl daemon-reload
fi

# 3. Check and fix frontend service
print_status "Checking frontend build..."

# Create systemd service for frontend dev server (temporary until proper build is fixed)
if [ ! -f /etc/systemd/system/awareness-frontend.service ]; then
    print_status "Creating frontend systemd service..."
    cat > /etc/systemd/system/awareness-frontend.service << 'EOF'
[Unit]
Description=Awareness Platform Frontend
After=network.target

[Service]
Type=simple
User=awareness
WorkingDirectory=/home/awareness/awareness-platform/frontend
Environment="PATH=/home/awareness/.nvm/versions/node/v20.11.0/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/awareness/.nvm/versions/node/v20.11.0/bin/npm run dev -- --host 0.0.0.0 --port 5173
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    systemctl daemon-reload
fi

# 4. Check Docker containers
print_status "Checking Docker containers..."
if command -v docker &> /dev/null; then
    docker ps -a | grep -E "(postgres|redis)" || print_warning "Database containers not found"
fi

# 5. Apply fixes
print_status "Applying fixes..."

# Backup existing nginx config
if [ -f /etc/nginx/sites-enabled/default ]; then
    cp /etc/nginx/sites-enabled/default /etc/nginx/sites-enabled/default.bak
fi

# Copy new nginx config
cp /tmp/awareness-platform-prod-fixed.conf /etc/nginx/sites-enabled/default

# Test nginx config
print_status "Testing nginx configuration..."
nginx -t || {
    print_error "Nginx configuration test failed"
    exit 1
}

# 6. Restart services
print_status "Restarting services..."

# Reload nginx
systemctl reload nginx
print_success "Nginx reloaded"

# Start backend if not running
systemctl is-active --quiet awareness-backend || {
    print_status "Starting backend service..."
    systemctl start awareness-backend
    systemctl enable awareness-backend
}

# Start frontend if not running
systemctl is-active --quiet awareness-frontend || {
    print_status "Starting frontend service..."
    systemctl start awareness-frontend
    systemctl enable awareness-frontend
}

# 7. Check service status
print_status "Checking service status..."
echo ""
echo "=== Service Status ==="
systemctl status awareness-backend --no-pager | head -n 5
echo ""
systemctl status awareness-frontend --no-pager | head -n 5
echo ""
systemctl status nginx --no-pager | head -n 5

# 8. Test endpoints
print_status "Testing endpoints..."
echo ""
echo "=== Endpoint Tests ==="

# Test health endpoint
curl -s http://localhost:8000/api/health | jq . || print_error "Backend health check failed"

# Test frontend
curl -s -o /dev/null -w "%{http_code}" http://localhost:5173 || print_error "Frontend not responding"

# Test nginx
curl -s -o /dev/null -w "%{http_code}" https://bootstrap-awareness.de/api/health || print_error "Nginx API proxy failed"

print_success "Production fix script completed!"
echo ""
echo "Next steps:"
echo "1. Check https://bootstrap-awareness.de - should show the app"
echo "2. Check https://bootstrap-awareness.de/api/health - should return JSON"
echo "3. Monitor logs: tail -f /var/log/nginx/awareness-error.log"
echo "4. Check backend logs: journalctl -u awareness-backend -f"
echo "5. Check frontend logs: journalctl -u awareness-frontend -f"