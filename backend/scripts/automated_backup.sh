#!/bin/bash
# Automated backup script for database and files
# Run this via cron for daily backups

set -euo pipefail

# Load environment variables
if [ -f /app/.env ]; then
    source /app/.env
fi

# Configuration
BACKUP_DIR="/var/backups"
LOG_DIR="/var/log/backups"
RETENTION_DAYS=7
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="${LOG_DIR}/backup_${TIMESTAMP}.log"

# Create directories if they don't exist
mkdir -p "${BACKUP_DIR}/database"
mkdir -p "${BACKUP_DIR}/files"
mkdir -p "${LOG_DIR}"

# Function to log messages
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "${LOG_FILE}"
}

# Function to send notification (customize based on your notification system)
send_notification() {
    local status=$1
    local message=$2
    
    # Example: Send to monitoring system or email
    # curl -X POST https://monitoring.example.com/webhook \
    #     -H "Content-Type: application/json" \
    #     -d "{\"status\": \"${status}\", \"message\": \"${message}\"}"
    
    log "Notification: ${status} - ${message}"
}

# Start backup process
log "=== Starting backup process ==="

# Database backup
log "Starting database backup..."
if python3 /app/scripts/backup_database.py \
    --backup-dir "${BACKUP_DIR}/database" \
    --retention-days ${RETENTION_DAYS} >> "${LOG_FILE}" 2>&1; then
    log "Database backup completed successfully"
    DB_BACKUP_STATUS="SUCCESS"
else
    log "ERROR: Database backup failed"
    DB_BACKUP_STATUS="FAILED"
fi

# File backup
log "Starting file backup..."
if python3 /app/scripts/backup_files.py \
    --upload-dir "/app/uploads" \
    --backup-dir "${BACKUP_DIR}/files" \
    --retention-days ${RETENTION_DAYS} >> "${LOG_FILE}" 2>&1; then
    log "File backup completed successfully"
    FILE_BACKUP_STATUS="SUCCESS"
else
    log "ERROR: File backup failed"
    FILE_BACKUP_STATUS="FAILED"
fi

# Redis backup (if configured)
if [ ! -z "${REDIS_URL:-}" ]; then
    log "Starting Redis backup..."
    REDIS_BACKUP_FILE="${BACKUP_DIR}/redis/redis_backup_${TIMESTAMP}.rdb"
    mkdir -p "${BACKUP_DIR}/redis"
    
    # Extract Redis connection details
    REDIS_HOST=$(echo $REDIS_URL | sed -E 's|redis://([^:]+):.*|\1|')
    REDIS_PORT=$(echo $REDIS_URL | sed -E 's|redis://[^:]+:([0-9]+).*|\1|')
    
    if redis-cli -h ${REDIS_HOST} -p ${REDIS_PORT} BGSAVE && \
       sleep 5 && \
       redis-cli -h ${REDIS_HOST} -p ${REDIS_PORT} --rdb "${REDIS_BACKUP_FILE}"; then
        log "Redis backup completed successfully"
        REDIS_BACKUP_STATUS="SUCCESS"
        
        # Compress Redis backup
        gzip "${REDIS_BACKUP_FILE}"
        
        # Clean up old Redis backups
        find "${BACKUP_DIR}/redis" -name "redis_backup_*.rdb.gz" -mtime +${RETENTION_DAYS} -delete
    else
        log "ERROR: Redis backup failed"
        REDIS_BACKUP_STATUS="FAILED"
    fi
else
    REDIS_BACKUP_STATUS="SKIPPED"
fi

# Generate backup summary
log "=== Backup Summary ==="
log "Database backup: ${DB_BACKUP_STATUS}"
log "File backup: ${FILE_BACKUP_STATUS}"
log "Redis backup: ${REDIS_BACKUP_STATUS}"

# Check disk usage
DISK_USAGE=$(df -h ${BACKUP_DIR} | awk 'NR==2 {print $5}' | sed 's/%//')
log "Backup disk usage: ${DISK_USAGE}%"

if [ ${DISK_USAGE} -gt 80 ]; then
    log "WARNING: Backup disk usage is above 80%"
    send_notification "WARNING" "Backup disk usage is ${DISK_USAGE}%"
fi

# Determine overall status
if [ "${DB_BACKUP_STATUS}" = "FAILED" ] || [ "${FILE_BACKUP_STATUS}" = "FAILED" ]; then
    OVERALL_STATUS="FAILED"
    send_notification "ERROR" "Backup process failed. Check logs at ${LOG_FILE}"
    exit 1
else
    OVERALL_STATUS="SUCCESS"
    send_notification "SUCCESS" "Backup process completed successfully"
fi

# Clean up old log files
find "${LOG_DIR}" -name "backup_*.log" -mtime +30 -delete

log "=== Backup process completed with status: ${OVERALL_STATUS} ===