#!/bin/bash

# Production Backup Script with S3 Support
# Performs comprehensive backups of database, files, and configuration

set -euo pipefail

# Configuration
BACKUP_DIR="/opt/backups"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30
S3_BUCKET="${BACKUP_S3_BUCKET:-}"
S3_REGION="${BACKUP_S3_REGION:-eu-central-1}"
APP_DIR="/opt/awareness"
LOG_FILE="/var/log/awareness/backup.log"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a $LOG_FILE
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a $LOG_FILE >&2
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a $LOG_FILE
}

# Create backup directories
mkdir -p $BACKUP_DIR/{postgres,redis,files,configs}

# Start backup process
log "Starting production backup..."

# 1. Backup PostgreSQL
log "Backing up PostgreSQL database..."
PGBACKUP_FILE="$BACKUP_DIR/postgres/db_backup_$DATE.sql.gz"

if docker exec awareness-postgres-1 pg_dumpall -U awareness_user | gzip > $PGBACKUP_FILE; then
    log "✅ PostgreSQL backup completed: $(du -h $PGBACKUP_FILE | cut -f1)"
    
    # Create structure-only backup for faster restoration testing
    docker exec awareness-postgres-1 pg_dumpall -U awareness_user --schema-only | \
        gzip > "$BACKUP_DIR/postgres/db_schema_$DATE.sql.gz"
else
    error "PostgreSQL backup failed"
fi

# 2. Backup Redis
log "Backing up Redis data..."
REDIS_BACKUP_FILE="$BACKUP_DIR/redis/redis_backup_$DATE.rdb"

if docker exec awareness-redis-1 redis-cli BGSAVE; then
    sleep 5  # Wait for background save to complete
    docker cp awareness-redis-1:/data/dump.rdb $REDIS_BACKUP_FILE
    log "✅ Redis backup completed: $(du -h $REDIS_BACKUP_FILE | cut -f1)"
else
    warning "Redis backup failed (non-critical)"
fi

# 3. Backup uploaded files
log "Backing up uploaded files..."
FILES_BACKUP="$BACKUP_DIR/files/files_backup_$DATE.tar.gz"

if docker run --rm \
    -v awareness_uploaded_files:/source:ro \
    -v $BACKUP_DIR/files:/backup \
    alpine tar czf /backup/files_backup_$DATE.tar.gz -C /source .; then
    log "✅ Files backup completed: $(du -h $FILES_BACKUP | cut -f1)"
else
    warning "Files backup failed"
fi

# 4. Backup configuration files
log "Backing up configuration files..."
CONFIG_BACKUP="$BACKUP_DIR/configs/config_backup_$DATE.tar.gz"

tar czf $CONFIG_BACKUP \
    $APP_DIR/.env* \
    $APP_DIR/docker-compose.yml \
    $APP_DIR/nginx \
    $APP_DIR/scripts \
    /etc/nginx/ssl-params.conf \
    /etc/letsencrypt/live \
    2>/dev/null || true

log "✅ Configuration backup completed: $(du -h $CONFIG_BACKUP | cut -f1)"

# 5. Create backup manifest
MANIFEST_FILE="$BACKUP_DIR/backup_manifest_$DATE.json"
cat > $MANIFEST_FILE << EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "date": "$DATE",
  "hostname": "$(hostname)",
  "files": {
    "database": "$(basename $PGBACKUP_FILE)",
    "database_size": "$(du -b $PGBACKUP_FILE | cut -f1)",
    "redis": "$(basename $REDIS_BACKUP_FILE)",
    "redis_size": "$(du -b $REDIS_BACKUP_FILE | cut -f1)",
    "files": "$(basename $FILES_BACKUP)",
    "files_size": "$(du -b $FILES_BACKUP | cut -f1)",
    "config": "$(basename $CONFIG_BACKUP)",
    "config_size": "$(du -b $CONFIG_BACKUP | cut -f1)"
  },
  "checksums": {
    "database": "$(sha256sum $PGBACKUP_FILE | cut -d' ' -f1)",
    "redis": "$(sha256sum $REDIS_BACKUP_FILE | cut -d' ' -f1)",
    "files": "$(sha256sum $FILES_BACKUP | cut -d' ' -f1)",
    "config": "$(sha256sum $CONFIG_BACKUP | cut -d' ' -f1)"
  }
}
EOF

# 6. Clean old backups
log "Cleaning old backups..."
find $BACKUP_DIR -type f -name "*.gz" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR -type f -name "*.rdb" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR -type f -name "*.json" -mtime +$RETENTION_DAYS -delete

# 7. Upload to S3 if configured
if [ ! -z "$S3_BUCKET" ]; then
    log "Uploading backups to S3..."
    
    # Install AWS CLI if not present
    if ! command -v aws &> /dev/null; then
        log "Installing AWS CLI..."
        apt-get update && apt-get install -y awscli
    fi
    
    # Configure AWS credentials if provided
    if [ ! -z "${BACKUP_S3_ACCESS_KEY:-}" ] && [ ! -z "${BACKUP_S3_SECRET_KEY:-}" ]; then
        export AWS_ACCESS_KEY_ID="$BACKUP_S3_ACCESS_KEY"
        export AWS_SECRET_ACCESS_KEY="$BACKUP_S3_SECRET_KEY"
        export AWS_DEFAULT_REGION="$S3_REGION"
    fi
    
    # Create S3 path
    S3_PATH="s3://$S3_BUCKET/$(hostname)/$DATE"
    
    # Upload files
    if aws s3 cp $PGBACKUP_FILE $S3_PATH/postgres/ --storage-class STANDARD_IA; then
        log "✅ Database uploaded to S3"
    else
        warning "Failed to upload database to S3"
    fi
    
    if aws s3 cp $REDIS_BACKUP_FILE $S3_PATH/redis/ --storage-class STANDARD_IA; then
        log "✅ Redis uploaded to S3"
    else
        warning "Failed to upload Redis to S3"
    fi
    
    if aws s3 cp $FILES_BACKUP $S3_PATH/files/ --storage-class STANDARD_IA; then
        log "✅ Files uploaded to S3"
    else
        warning "Failed to upload files to S3"
    fi
    
    if aws s3 cp $CONFIG_BACKUP $S3_PATH/configs/ --storage-class STANDARD_IA; then
        log "✅ Configuration uploaded to S3"
    else
        warning "Failed to upload configuration to S3"
    fi
    
    # Upload manifest
    aws s3 cp $MANIFEST_FILE $S3_PATH/manifest.json
    
    # Clean old S3 backups
    log "Cleaning old S3 backups..."
    OLD_DATE=$(date -d "$RETENTION_DAYS days ago" +%Y%m%d)
    aws s3 ls s3://$S3_BUCKET/$(hostname)/ | \
        awk '{print $2}' | \
        grep -E '^[0-9]{8}_' | \
        while read dir; do
            dir_date=$(echo $dir | cut -d'_' -f1)
            if [ "$dir_date" -lt "$OLD_DATE" ]; then
                log "Removing old backup: $dir"
                aws s3 rm s3://$S3_BUCKET/$(hostname)/$dir --recursive
            fi
        done
fi

# 8. Verify backups
log "Verifying backups..."
VERIFICATION_PASSED=true

# Test database backup
if zcat $PGBACKUP_FILE | head -n 10 | grep -q "PostgreSQL database dump"; then
    log "✅ Database backup verified"
else
    warning "Database backup verification failed"
    VERIFICATION_PASSED=false
fi

# Test files backup
if tar tzf $FILES_BACKUP &> /dev/null; then
    log "✅ Files backup verified"
else
    warning "Files backup verification failed"
    VERIFICATION_PASSED=false
fi

# 9. Send notification (if webhook configured)
if [ ! -z "${BACKUP_WEBHOOK_URL:-}" ]; then
    BACKUP_SIZE=$(du -sh $BACKUP_DIR | cut -f1)
    
    if [ "$VERIFICATION_PASSED" = true ]; then
        STATUS="success"
        COLOR="good"
    else
        STATUS="failed"
        COLOR="danger"
    fi
    
    curl -X POST $BACKUP_WEBHOOK_URL \
        -H "Content-Type: application/json" \
        -d "{
            \"text\": \"Backup $STATUS for $(hostname)\",
            \"attachments\": [{
                \"color\": \"$COLOR\",
                \"fields\": [
                    {\"title\": \"Date\", \"value\": \"$DATE\", \"short\": true},
                    {\"title\": \"Total Size\", \"value\": \"$BACKUP_SIZE\", \"short\": true},
                    {\"title\": \"S3 Upload\", \"value\": \"$([ ! -z "$S3_BUCKET" ] && echo "Enabled" || echo "Disabled")\", \"short\": true},
                    {\"title\": \"Retention\", \"value\": \"$RETENTION_DAYS days\", \"short\": true}
                ]
            }]
        }"
fi

# 10. Generate backup report
REPORT_FILE="$BACKUP_DIR/backup_report_$DATE.txt"
cat > $REPORT_FILE << EOF
Production Backup Report
========================
Date: $(date)
Hostname: $(hostname)

Backup Summary:
--------------
Database: $(du -h $PGBACKUP_FILE 2>/dev/null | cut -f1 || echo "N/A")
Redis: $(du -h $REDIS_BACKUP_FILE 2>/dev/null | cut -f1 || echo "N/A")
Files: $(du -h $FILES_BACKUP 2>/dev/null | cut -f1 || echo "N/A")
Config: $(du -h $CONFIG_BACKUP 2>/dev/null | cut -f1 || echo "N/A")

Total Backup Size: $(du -sh $BACKUP_DIR | cut -f1)
S3 Upload: $([ ! -z "$S3_BUCKET" ] && echo "Enabled - Bucket: $S3_BUCKET" || echo "Disabled")
Verification: $([ "$VERIFICATION_PASSED" = true ] && echo "PASSED" || echo "FAILED")

Backup Files:
------------
$(ls -lh $BACKUP_DIR/{postgres,redis,files,configs}/*$DATE* 2>/dev/null || echo "No files found")

Disk Usage:
----------
$(df -h $BACKUP_DIR)

Next Steps:
----------
1. Verify backup integrity manually if needed
2. Test restoration procedure monthly
3. Monitor S3 costs if enabled
4. Review retention policy quarterly
EOF

log "Backup completed successfully!"
log "Report saved to: $REPORT_FILE"
log "Total backup size: $(du -sh $BACKUP_DIR | cut -f1)"

# Exit with appropriate code
if [ "$VERIFICATION_PASSED" = true ]; then
    exit 0
else
    exit 1
fi