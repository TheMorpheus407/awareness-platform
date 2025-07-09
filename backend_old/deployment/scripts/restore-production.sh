#!/bin/bash

# Production Restore Script
# Restores from backups with verification and rollback capability

set -euo pipefail

# Configuration
BACKUP_DIR="/opt/backups"
APP_DIR="/opt/awareness"
S3_BUCKET="${BACKUP_S3_BUCKET:-}"
S3_REGION="${BACKUP_S3_REGION:-eu-central-1}"
LOG_FILE="/var/log/awareness/restore.log"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a $LOG_FILE
}

# Usage function
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Options:
    -d, --date DATE         Backup date to restore (format: YYYYMMDD_HHMMSS)
    -s, --from-s3           Download backup from S3
    -t, --type TYPE         Type of restore: full, database, files, redis, config
    -f, --force             Skip confirmation prompts
    -v, --verify-only       Only verify backup integrity without restoring
    -h, --help              Show this help message

Examples:
    $0 --date 20240108_120000 --type full
    $0 --from-s3 --date 20240108_120000 --type database
    $0 --verify-only --date 20240108_120000
EOF
    exit 0
}

# Parse arguments
BACKUP_DATE=""
FROM_S3=false
RESTORE_TYPE="full"
FORCE=false
VERIFY_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--date)
            BACKUP_DATE="$2"
            shift 2
            ;;
        -s|--from-s3)
            FROM_S3=true
            shift
            ;;
        -t|--type)
            RESTORE_TYPE="$2"
            shift 2
            ;;
        -f|--force)
            FORCE=true
            shift
            ;;
        -v|--verify-only)
            VERIFY_ONLY=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            error "Unknown option: $1"
            ;;
    esac
done

# Validate inputs
if [ -z "$BACKUP_DATE" ]; then
    error "Backup date is required. Use -d or --date option."
fi

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   error "This script must be run as root"
fi

log "Starting restore process..."
log "Backup date: $BACKUP_DATE"
log "Restore type: $RESTORE_TYPE"
log "From S3: $FROM_S3"

# Function to download from S3
download_from_s3() {
    local backup_date=$1
    
    if [ -z "$S3_BUCKET" ]; then
        error "S3_BUCKET environment variable not set"
    fi
    
    # Configure AWS credentials if provided
    if [ ! -z "${BACKUP_S3_ACCESS_KEY:-}" ] && [ ! -z "${BACKUP_S3_SECRET_KEY:-}" ]; then
        export AWS_ACCESS_KEY_ID="$BACKUP_S3_ACCESS_KEY"
        export AWS_SECRET_ACCESS_KEY="$BACKUP_S3_SECRET_KEY"
        export AWS_DEFAULT_REGION="$S3_REGION"
    fi
    
    S3_PATH="s3://$S3_BUCKET/$(hostname)/$backup_date"
    
    log "Downloading backups from S3: $S3_PATH"
    
    # Create temporary directory
    TEMP_DIR="/tmp/restore_$backup_date"
    mkdir -p $TEMP_DIR
    
    # Download files
    aws s3 sync $S3_PATH $TEMP_DIR/
    
    # Move to backup directory
    mkdir -p $BACKUP_DIR/{postgres,redis,files,configs}
    [ -f "$TEMP_DIR/postgres/"* ] && mv $TEMP_DIR/postgres/* $BACKUP_DIR/postgres/
    [ -f "$TEMP_DIR/redis/"* ] && mv $TEMP_DIR/redis/* $BACKUP_DIR/redis/
    [ -f "$TEMP_DIR/files/"* ] && mv $TEMP_DIR/files/* $BACKUP_DIR/files/
    [ -f "$TEMP_DIR/configs/"* ] && mv $TEMP_DIR/configs/* $BACKUP_DIR/configs/
    [ -f "$TEMP_DIR/manifest.json" ] && mv $TEMP_DIR/manifest.json $BACKUP_DIR/
    
    rm -rf $TEMP_DIR
    log "✅ Downloaded backups from S3"
}

# Function to verify backup files
verify_backups() {
    local date=$1
    local missing_files=()
    
    info "Verifying backup files..."
    
    # Check required files based on restore type
    case $RESTORE_TYPE in
        full|database)
            [ ! -f "$BACKUP_DIR/postgres/db_backup_$date.sql.gz" ] && missing_files+=("PostgreSQL backup")
            ;;
    esac
    
    case $RESTORE_TYPE in
        full|redis)
            [ ! -f "$BACKUP_DIR/redis/redis_backup_$date.rdb" ] && missing_files+=("Redis backup")
            ;;
    esac
    
    case $RESTORE_TYPE in
        full|files)
            [ ! -f "$BACKUP_DIR/files/files_backup_$date.tar.gz" ] && missing_files+=("Files backup")
            ;;
    esac
    
    case $RESTORE_TYPE in
        full|config)
            [ ! -f "$BACKUP_DIR/configs/config_backup_$date.tar.gz" ] && missing_files+=("Config backup")
            ;;
    esac
    
    if [ ${#missing_files[@]} -gt 0 ]; then
        error "Missing backup files: ${missing_files[*]}"
    fi
    
    # Verify manifest if exists
    if [ -f "$BACKUP_DIR/backup_manifest_$date.json" ]; then
        info "Verifying checksums from manifest..."
        
        # Extract checksums from manifest
        DB_CHECKSUM=$(jq -r '.checksums.database' "$BACKUP_DIR/backup_manifest_$date.json")
        
        # Verify database checksum
        if [ -f "$BACKUP_DIR/postgres/db_backup_$date.sql.gz" ]; then
            ACTUAL_CHECKSUM=$(sha256sum "$BACKUP_DIR/postgres/db_backup_$date.sql.gz" | cut -d' ' -f1)
            if [ "$DB_CHECKSUM" != "$ACTUAL_CHECKSUM" ]; then
                error "Database backup checksum mismatch!"
            else
                log "✅ Database backup checksum verified"
            fi
        fi
    fi
    
    log "✅ All backup files verified"
}

# Function to create pre-restore backup
create_restore_point() {
    info "Creating restore point..."
    
    # Use the backup script to create a point-in-time backup
    if [ -f "$APP_DIR/scripts/backup-production.sh" ]; then
        RESTORE_POINT_DATE=$(date +%Y%m%d_%H%M%S)
        export BACKUP_DIR="/opt/backups/restore_points"
        mkdir -p $BACKUP_DIR
        
        $APP_DIR/scripts/backup-production.sh
        
        log "✅ Restore point created: $RESTORE_POINT_DATE"
        echo $RESTORE_POINT_DATE > /tmp/last_restore_point
    else
        warning "Backup script not found. Skipping restore point creation."
    fi
}

# Function to restore database
restore_database() {
    local date=$1
    local backup_file="$BACKUP_DIR/postgres/db_backup_$date.sql.gz"
    
    log "Restoring PostgreSQL database..."
    
    # Stop application
    info "Stopping application containers..."
    cd $APP_DIR
    docker-compose stop backend
    
    # Create new database
    info "Recreating database..."
    docker exec awareness-postgres-1 psql -U awareness_user -c "DROP DATABASE IF EXISTS awareness_platform_restore;"
    docker exec awareness-postgres-1 psql -U awareness_user -c "CREATE DATABASE awareness_platform_restore;"
    
    # Restore backup
    info "Restoring from backup..."
    zcat $backup_file | docker exec -i awareness-postgres-1 psql -U awareness_user -d awareness_platform_restore
    
    if [ $? -eq 0 ]; then
        # Swap databases
        docker exec awareness-postgres-1 psql -U awareness_user << EOF
ALTER DATABASE awareness_platform RENAME TO awareness_platform_old;
ALTER DATABASE awareness_platform_restore RENAME TO awareness_platform;
EOF
        
        log "✅ Database restored successfully"
        
        # Start application
        docker-compose start backend
    else
        error "Database restoration failed"
    fi
}

# Function to restore Redis
restore_redis() {
    local date=$1
    local backup_file="$BACKUP_DIR/redis/redis_backup_$date.rdb"
    
    log "Restoring Redis data..."
    
    # Stop Redis
    docker-compose stop redis
    
    # Copy backup file
    docker cp $backup_file awareness-redis-1:/data/dump.rdb
    
    # Start Redis
    docker-compose start redis
    
    log "✅ Redis restored successfully"
}

# Function to restore files
restore_files() {
    local date=$1
    local backup_file="$BACKUP_DIR/files/files_backup_$date.tar.gz"
    
    log "Restoring uploaded files..."
    
    # Create temporary container to extract files
    docker run --rm \
        -v awareness_uploaded_files:/target \
        -v $BACKUP_DIR/files:/backup:ro \
        alpine sh -c "
            cd /target && 
            rm -rf * && 
            tar xzf /backup/files_backup_$date.tar.gz
        "
    
    log "✅ Files restored successfully"
}

# Function to restore configuration
restore_config() {
    local date=$1
    local backup_file="$BACKUP_DIR/configs/config_backup_$date.tar.gz"
    
    log "Restoring configuration files..."
    
    # Extract to temporary directory
    TEMP_CONFIG="/tmp/config_restore_$date"
    mkdir -p $TEMP_CONFIG
    tar xzf $backup_file -C $TEMP_CONFIG
    
    # Selectively restore configuration files
    if [ -f "$TEMP_CONFIG$APP_DIR/docker-compose.yml" ]; then
        cp "$TEMP_CONFIG$APP_DIR/docker-compose.yml" "$APP_DIR/docker-compose.yml.restored"
        info "docker-compose.yml restored as docker-compose.yml.restored"
    fi
    
    # Clean up
    rm -rf $TEMP_CONFIG
    
    log "✅ Configuration restored (review manually)"
}

# Main restore process
main() {
    # Download from S3 if requested
    if [ "$FROM_S3" = true ]; then
        download_from_s3 $BACKUP_DATE
    fi
    
    # Verify backups
    verify_backups $BACKUP_DATE
    
    if [ "$VERIFY_ONLY" = true ]; then
        log "✅ Verification completed. No restore performed."
        exit 0
    fi
    
    # Confirmation prompt
    if [ "$FORCE" != true ]; then
        warning "This will restore $RESTORE_TYPE from backup dated $BACKUP_DATE"
        warning "Current data will be overwritten!"
        read -p "Are you sure you want to continue? (yes/no) " -r
        if [[ ! $REPLY =~ ^yes$ ]]; then
            log "Restore cancelled by user"
            exit 0
        fi
    fi
    
    # Create restore point
    create_restore_point
    
    # Perform restore based on type
    case $RESTORE_TYPE in
        full)
            restore_database $BACKUP_DATE
            restore_redis $BACKUP_DATE
            restore_files $BACKUP_DATE
            restore_config $BACKUP_DATE
            ;;
        database)
            restore_database $BACKUP_DATE
            ;;
        redis)
            restore_redis $BACKUP_DATE
            ;;
        files)
            restore_files $BACKUP_DATE
            ;;
        config)
            restore_config $BACKUP_DATE
            ;;
        *)
            error "Invalid restore type: $RESTORE_TYPE"
            ;;
    esac
    
    # Verify application health
    sleep 10
    if curl -sf http://localhost/api/health > /dev/null; then
        log "✅ Application health check passed"
    else
        warning "Application health check failed. Please verify manually."
    fi
    
    log "✅ Restore completed successfully!"
    
    # Show restore point info
    if [ -f /tmp/last_restore_point ]; then
        RESTORE_POINT=$(cat /tmp/last_restore_point)
        info "Restore point created: $RESTORE_POINT"
        info "To rollback: $0 --date $RESTORE_POINT --type $RESTORE_TYPE"
    fi
}

# Execute main function
main