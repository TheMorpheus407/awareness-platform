#!/bin/bash

# Production Environment Setup Script
# This script sets up a fresh Ubuntu server for hosting the awareness platform

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
DOMAIN="bootstrap-awareness.de"
EMAIL="admin@bootstrap-awareness.de"
APP_DIR="/opt/awareness"
BACKUP_DIR="/opt/backups"
LOG_DIR="/var/log/awareness"

# Function to print colored output
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

log "Starting production environment setup..."

# Update system
log "Updating system packages..."
apt-get update
apt-get upgrade -y

# Install required packages
log "Installing required packages..."
apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    software-properties-common \
    ufw \
    fail2ban \
    htop \
    vim \
    git \
    jq \
    postgresql-client \
    redis-tools \
    certbot \
    python3-certbot-nginx

# Install Docker
if ! command -v docker &> /dev/null; then
    log "Installing Docker..."
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
else
    log "Docker already installed"
fi

# Install Docker Compose
if ! command -v docker-compose &> /dev/null; then
    log "Installing Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
else
    log "Docker Compose already installed"
fi

# Create application directories
log "Creating application directories..."
mkdir -p $APP_DIR/{backend,frontend,nginx,scripts,deployment,logs}
mkdir -p $BACKUP_DIR/{postgres,redis,files}
mkdir -p $LOG_DIR/{nginx,backend,postgres}
mkdir -p /etc/nginx/ssl

# Set up firewall
log "Configuring firewall..."
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow http
ufw allow https
ufw allow 9090/tcp  # Prometheus
ufw allow 3000/tcp  # Grafana (restrict in production)
ufw --force enable

# Configure fail2ban
log "Configuring fail2ban..."
cat > /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/*error.log

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
port = http,https
logpath = /var/log/nginx/*error.log

[nginx-botsearch]
enabled = true
filter = nginx-botsearch
port = http,https
logpath = /var/log/nginx/*access.log
maxretry = 2
EOF

systemctl restart fail2ban

# Set up system limits
log "Configuring system limits..."
cat >> /etc/sysctl.conf << EOF

# Network optimizations
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.tcp_fin_timeout = 30
net.ipv4.tcp_keepalive_time = 60
net.ipv4.tcp_keepalive_intvl = 10
net.ipv4.tcp_keepalive_probes = 6
net.ipv4.ip_local_port_range = 1024 65535

# File system
fs.file-max = 65535

# Memory
vm.swappiness = 10
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5
EOF

sysctl -p

# Set up file limits
cat >> /etc/security/limits.conf << EOF

# Awareness Platform Limits
* soft nofile 65535
* hard nofile 65535
* soft nproc 32768
* hard nproc 32768
EOF

# Generate DH parameters for SSL
if [ ! -f /etc/nginx/dhparam.pem ]; then
    log "Generating DH parameters (this may take a while)..."
    openssl dhparam -out /etc/nginx/dhparam.pem 2048
fi

# Create swap file if not exists
if [ ! -f /swapfile ]; then
    log "Creating swap file..."
    fallocate -l 2G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' | tee -a /etc/fstab
fi

# Set up log rotation
log "Configuring log rotation..."
cat > /etc/logrotate.d/awareness << EOF
$LOG_DIR/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data adm
    sharedscripts
    postrotate
        docker exec awareness-nginx-1 nginx -s reload > /dev/null 2>&1 || true
    endscript
}
EOF

# Install monitoring tools
log "Installing monitoring tools..."
# Node Exporter
wget -q https://github.com/prometheus/node_exporter/releases/latest/download/node_exporter-1.6.1.linux-amd64.tar.gz
tar xvf node_exporter-*.tar.gz
cp node_exporter-*/node_exporter /usr/local/bin/
rm -rf node_exporter-*

# Create node_exporter service
cat > /etc/systemd/system/node_exporter.service << EOF
[Unit]
Description=Node Exporter
After=network.target

[Service]
User=nobody
Group=nogroup
Type=simple
ExecStart=/usr/local/bin/node_exporter

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable node_exporter
systemctl start node_exporter

# Create deployment user
if ! id -u awareness >/dev/null 2>&1; then
    log "Creating deployment user..."
    useradd -m -s /bin/bash awareness
    usermod -aG docker awareness
fi

# Set up cron jobs
log "Setting up cron jobs..."
cat > /etc/cron.d/awareness-backup << EOF
# Database backup every 6 hours
0 */6 * * * root /opt/awareness/scripts/backup.sh >> $LOG_DIR/backup.log 2>&1

# Clean old logs weekly
0 2 * * 0 root find $LOG_DIR -name "*.log" -mtime +30 -delete

# Certificate renewal check daily
0 3 * * * root certbot renew --quiet --post-hook "docker exec awareness-nginx-1 nginx -s reload"
EOF

# Create health check script
cat > $APP_DIR/scripts/health-check.sh << 'EOF'
#!/bin/bash
# Health check script

SERVICES=("nginx" "backend" "postgres" "redis")
FAILED=0

for service in "${SERVICES[@]}"; do
    if ! docker ps | grep -q "awareness-${service}-1"; then
        echo "Service $service is not running!"
        FAILED=$((FAILED + 1))
    fi
done

# Check API endpoint
if ! curl -sf http://localhost/api/health > /dev/null; then
    echo "API health check failed!"
    FAILED=$((FAILED + 1))
fi

# Check disk space
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "Disk usage critical: ${DISK_USAGE}%"
    FAILED=$((FAILED + 1))
fi

exit $FAILED
EOF

chmod +x $APP_DIR/scripts/health-check.sh

# Create backup script
cat > $APP_DIR/scripts/backup.sh << 'EOF'
#!/bin/bash
# Backup script for production

set -euo pipefail

BACKUP_DIR="/opt/backups"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Backup PostgreSQL
echo "Backing up PostgreSQL..."
docker exec awareness-postgres-1 pg_dumpall -U awareness_user > $BACKUP_DIR/postgres/backup_$DATE.sql
gzip $BACKUP_DIR/postgres/backup_$DATE.sql

# Backup Redis
echo "Backing up Redis..."
docker exec awareness-redis-1 redis-cli --rdb $BACKUP_DIR/redis/backup_$DATE.rdb

# Backup uploaded files
echo "Backing up uploaded files..."
docker run --rm -v awareness_uploaded_files:/data -v $BACKUP_DIR/files:/backup alpine tar czf /backup/files_$DATE.tar.gz -C /data .

# Clean old backups
echo "Cleaning old backups..."
find $BACKUP_DIR -type f -mtime +$RETENTION_DAYS -delete

# Upload to S3 if configured
if [ ! -z "${BACKUP_S3_BUCKET:-}" ]; then
    echo "Uploading to S3..."
    aws s3 sync $BACKUP_DIR s3://$BACKUP_S3_BUCKET/$(hostname)/ --delete
fi

echo "Backup completed at $(date)"
EOF

chmod +x $APP_DIR/scripts/backup.sh

# Create monitoring dashboard access
log "Setting up monitoring access..."
htpasswd -bc /etc/nginx/.htpasswd admin $(openssl rand -base64 12)

log "Production setup completed!"
log ""
log "Next steps:"
log "1. Copy your .env.production file to $APP_DIR/.env"
log "2. Copy docker-compose.prod.optimized.yml to $APP_DIR/docker-compose.yml"
log "3. Copy nginx configuration files to $APP_DIR/nginx/"
log "4. Run: cd $APP_DIR && docker-compose up -d"
log "5. Set up SSL: certbot --nginx -d $DOMAIN -d www.$DOMAIN --email $EMAIL --agree-tos --no-eff-email"
log ""
log "Monitoring credentials:"
log "Username: admin"
log "Password: Check /etc/nginx/.htpasswd"
log ""
log "Important files:"
log "- Application: $APP_DIR"
log "- Backups: $BACKUP_DIR"
log "- Logs: $LOG_DIR"