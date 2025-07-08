#!/bin/bash

# SSL Certificate Setup Script for Production
# Handles Let's Encrypt certificate generation and renewal

set -euo pipefail

# Configuration
DOMAIN="bootstrap-awareness.de"
EMAIL="admin@bootstrap-awareness.de"
NGINX_CONTAINER="awareness-nginx-1"
CERT_PATH="/etc/letsencrypt/live/$DOMAIN"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   error "This script must be run as root"
fi

# Function to check if certificates already exist
check_existing_certs() {
    if [ -d "$CERT_PATH" ] && [ -f "$CERT_PATH/fullchain.pem" ] && [ -f "$CERT_PATH/privkey.pem" ]; then
        log "SSL certificates already exist for $DOMAIN"
        
        # Check expiration
        EXPIRY=$(openssl x509 -enddate -noout -in "$CERT_PATH/fullchain.pem" | cut -d= -f2)
        EXPIRY_EPOCH=$(date -d "$EXPIRY" +%s)
        CURRENT_EPOCH=$(date +%s)
        DAYS_LEFT=$(( ($EXPIRY_EPOCH - $CURRENT_EPOCH) / 86400 ))
        
        if [ $DAYS_LEFT -lt 30 ]; then
            warning "Certificate expires in $DAYS_LEFT days. Renewal recommended."
            return 1
        else
            log "Certificate valid for $DAYS_LEFT more days."
            return 0
        fi
    else
        return 1
    fi
}

# Function to test nginx configuration
test_nginx_config() {
    log "Testing nginx configuration..."
    docker exec $NGINX_CONTAINER nginx -t || error "Nginx configuration test failed"
}

# Function to reload nginx
reload_nginx() {
    log "Reloading nginx..."
    docker exec $NGINX_CONTAINER nginx -s reload || error "Failed to reload nginx"
}

# Main script
log "Starting SSL certificate setup for $DOMAIN"

# Check if certbot is installed
if ! command -v certbot &> /dev/null; then
    log "Installing certbot..."
    apt-get update
    apt-get install -y certbot python3-certbot-nginx
fi

# Check for existing certificates
if check_existing_certs; then
    read -p "Certificates already exist and are valid. Force renewal? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log "Skipping certificate generation."
        exit 0
    fi
fi

# Stop nginx temporarily to get certificates in standalone mode
log "Stopping nginx container..."
docker stop $NGINX_CONTAINER || true

# Get certificates
log "Obtaining SSL certificates from Let's Encrypt..."
certbot certonly \
    --standalone \
    --non-interactive \
    --agree-tos \
    --email $EMAIL \
    --domains $DOMAIN,www.$DOMAIN \
    --expand \
    --pre-hook "docker stop $NGINX_CONTAINER 2>/dev/null || true" \
    --post-hook "docker start $NGINX_CONTAINER 2>/dev/null || true"

# Start nginx again
log "Starting nginx container..."
docker start $NGINX_CONTAINER

# Wait for nginx to be ready
sleep 5

# Test nginx configuration
test_nginx_config

# Create renewal configuration
log "Setting up automatic renewal..."
cat > /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh << EOF
#!/bin/bash
docker exec $NGINX_CONTAINER nginx -s reload
EOF

chmod +x /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh

# Set up cron job for renewal
if ! crontab -l | grep -q "certbot renew"; then
    log "Adding certbot renewal to crontab..."
    (crontab -l 2>/dev/null; echo "0 3 * * * /usr/bin/certbot renew --quiet") | crontab -
fi

# Create certificate monitoring script
cat > /opt/awareness/scripts/check-ssl-expiry.sh << 'EOF'
#!/bin/bash

DOMAIN="bootstrap-awareness.de"
CERT_PATH="/etc/letsencrypt/live/$DOMAIN/fullchain.pem"
WARNING_DAYS=14

if [ -f "$CERT_PATH" ]; then
    EXPIRY=$(openssl x509 -enddate -noout -in "$CERT_PATH" | cut -d= -f2)
    EXPIRY_EPOCH=$(date -d "$EXPIRY" +%s)
    CURRENT_EPOCH=$(date +%s)
    DAYS_LEFT=$(( ($EXPIRY_EPOCH - $CURRENT_EPOCH) / 86400 ))
    
    echo "SSL certificate for $DOMAIN expires in $DAYS_LEFT days ($EXPIRY)"
    
    if [ $DAYS_LEFT -lt $WARNING_DAYS ]; then
        echo "WARNING: Certificate expiring soon! Please renew."
        # Send alert (configure your alerting mechanism here)
        # Example: curl -X POST https://your-webhook-url -d "SSL cert expiring in $DAYS_LEFT days"
        exit 1
    fi
else
    echo "ERROR: Certificate not found at $CERT_PATH"
    exit 2
fi
EOF

chmod +x /opt/awareness/scripts/check-ssl-expiry.sh

# Add to monitoring cron
if ! crontab -l | grep -q "check-ssl-expiry"; then
    (crontab -l 2>/dev/null; echo "0 9 * * * /opt/awareness/scripts/check-ssl-expiry.sh") | crontab -
fi

# Verify SSL configuration
log "Verifying SSL configuration..."
sleep 5

# Test HTTPS endpoint
if curl -sf https://$DOMAIN > /dev/null; then
    log "✅ HTTPS is working correctly!"
else
    error "HTTPS test failed. Please check nginx logs."
fi

# Check SSL grade (optional)
log "You can check your SSL configuration grade at:"
log "https://www.ssllabs.com/ssltest/analyze.html?d=$DOMAIN"

log "SSL setup completed successfully!"
log ""
log "Certificate details:"
openssl x509 -in "$CERT_PATH/fullchain.pem" -noout -subject -dates