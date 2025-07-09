#!/bin/bash
set -e

# Configuration
BACKUP_DIR="/opt/awareness/backups"
RETENTION_DAYS=30
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

echo "Starting backup at $(date)"

# Backup database
echo "Backing up database..."
docker compose exec -T postgres pg_dump -U awareness awareness_platform | gzip > "$BACKUP_DIR/db_backup_$TIMESTAMP.sql.gz"

# Backup uploaded files
echo "Backing up uploaded files..."
docker run --rm -v awareness_uploaded_files:/data -v $BACKUP_DIR:/backup alpine tar czf /backup/files_backup_$TIMESTAMP.tar.gz -C /data .

# Backup configuration
echo "Backing up configuration..."
tar czf "$BACKUP_DIR/config_backup_$TIMESTAMP.tar.gz" -C /opt/awareness .env docker-compose.yml nginx

# Clean old backups
echo "Cleaning old backups..."
find $BACKUP_DIR -name "*.gz" -mtime +$RETENTION_DAYS -delete

# Upload to S3 (optional)
if [ ! -z "$AWS_S3_BACKUP_BUCKET" ]; then
    echo "Uploading to S3..."
    aws s3 sync $BACKUP_DIR s3://$AWS_S3_BACKUP_BUCKET/awareness-platform/ --exclude "*" --include "*_$TIMESTAMP.*"
fi

echo "Backup completed at $(date)"