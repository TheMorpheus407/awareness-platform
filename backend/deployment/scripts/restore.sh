#!/bin/bash
set -e

# Check if backup file is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <backup_timestamp>"
    echo "Available backups:"
    ls -la /opt/awareness/backups/
    exit 1
fi

TIMESTAMP=$1
BACKUP_DIR="/opt/awareness/backups"

echo "Starting restore from backup $TIMESTAMP..."

# Stop services
echo "Stopping services..."
docker compose stop

# Restore database
if [ -f "$BACKUP_DIR/db_backup_$TIMESTAMP.sql.gz" ]; then
    echo "Restoring database..."
    docker compose up -d postgres
    sleep 10
    gunzip -c "$BACKUP_DIR/db_backup_$TIMESTAMP.sql.gz" | docker compose exec -T postgres psql -U awareness awareness_platform
fi

# Restore uploaded files
if [ -f "$BACKUP_DIR/files_backup_$TIMESTAMP.tar.gz" ]; then
    echo "Restoring uploaded files..."
    docker run --rm -v awareness_uploaded_files:/data -v $BACKUP_DIR:/backup alpine sh -c "rm -rf /data/* && tar xzf /backup/files_backup_$TIMESTAMP.tar.gz -C /data"
fi

# Restore configuration
if [ -f "$BACKUP_DIR/config_backup_$TIMESTAMP.tar.gz" ]; then
    echo "Restoring configuration..."
    read -p "Do you want to restore configuration files? This will overwrite current config. (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        tar xzf "$BACKUP_DIR/config_backup_$TIMESTAMP.tar.gz" -C /opt/awareness
    fi
fi

# Start services
echo "Starting services..."
docker compose up -d

echo "Restore completed. Please verify the application is working correctly."