# Backup and Restore Guide

## Overview

This guide covers the automated backup strategy for the Cybersecurity Awareness Platform, including database backups, file backups, and restore procedures.

## Backup Components

### 1. Database Backups
- **What**: PostgreSQL database including all tables, indexes, and data
- **When**: Daily at 2:00 AM (configurable)
- **Where**: `/var/backups/database/`
- **Format**: Compressed SQL dump (`.sql.gz`)
- **Retention**: 7 days by default

### 2. File Backups
- **What**: All uploaded files in `/app/uploads/`
- **When**: Daily at 2:00 AM (configurable)
- **Where**: `/var/backups/files/`
- **Format**: Compressed tar archive (`.tar.gz`) with SHA256 checksum
- **Retention**: 7 days by default

### 3. Redis Backups (Optional)
- **What**: Redis cache data
- **When**: Daily at 2:00 AM
- **Where**: `/var/backups/redis/`
- **Format**: RDB snapshot (`.rdb.gz`)
- **Retention**: 7 days by default

## Automated Backup Setup

### 1. Install Backup Scripts

```bash
# Copy scripts to production server
scp backend/scripts/backup_*.py user@server:/app/scripts/
scp backend/scripts/automated_backup.sh user@server:/app/scripts/
scp backend/scripts/restore_backup.py user@server:/app/scripts/
scp backend/scripts/verify_backups.sh user@server:/app/scripts/

# Make scripts executable
ssh user@server 'chmod +x /app/scripts/*.py /app/scripts/*.sh'
```

### 2. Configure Cron Jobs

```bash
# Install cron configuration
ssh user@server 'sudo crontab -u www-data /app/infrastructure/cron/backup-cron'

# Or manually add to crontab
ssh user@server 'sudo crontab -e -u www-data'

# Add these lines:
# Daily backups at 2:00 AM
0 2 * * * /app/scripts/automated_backup.sh >> /var/log/backups/cron.log 2>&1

# Weekly verification on Sunday at 4:00 AM
0 4 * * 0 /app/scripts/verify_backups.sh >> /var/log/backups/cron-verify.log 2>&1
```

### 3. Create Backup Directories

```bash
ssh user@server 'sudo mkdir -p /var/backups/{database,files,redis}'
ssh user@server 'sudo mkdir -p /var/log/backups'
ssh user@server 'sudo chown -R www-data:www-data /var/backups /var/log/backups'
```

## Manual Backup Operations

### Create Manual Backup

```bash
# Database backup
python3 /app/scripts/backup_database.py

# File backup
python3 /app/scripts/backup_files.py

# Full backup (database + files)
/app/scripts/automated_backup.sh
```

### List Available Backups

```bash
# List database backups
python3 /app/scripts/backup_database.py --list

# List file backups
python3 /app/scripts/backup_files.py --list

# List all backups with restore script
python3 /app/scripts/restore_backup.py --list
```

### Verify Backups

```bash
# Run verification script
/app/scripts/verify_backups.sh

# Check latest backup age
ls -la /var/backups/database/ | head -5
```

## Restore Procedures

### 1. Interactive Restore

```bash
# List available backups
python3 /app/scripts/restore_backup.py --list

# Restore database (with confirmation)
python3 /app/scripts/restore_backup.py \
    --restore-db /var/backups/database/db_backup_20250111_020000.sql.gz

# Restore files (with confirmation)
python3 /app/scripts/restore_backup.py \
    --restore-files /var/backups/files/files_backup_20250111_020000.tar.gz
```

### 2. Automated Restore (No Confirmation)

```bash
# Restore without confirmation prompts
python3 /app/scripts/restore_backup.py \
    --restore-db /var/backups/database/db_backup_20250111_020000.sql.gz \
    --no-confirm

# Restore to specific directory
python3 /app/scripts/restore_backup.py \
    --restore-files /var/backups/files/files_backup_20250111_020000.tar.gz \
    --restore-dir /tmp/restored_files \
    --no-confirm
```

### 3. Emergency Restore

```bash
# 1. Stop application
sudo systemctl stop awareness-platform

# 2. Create restore point (backup current state)
python3 /app/scripts/restore_backup.py --create-restore-point

# 3. Restore database
zcat /var/backups/database/db_backup_YYYYMMDD_HHMMSS.sql.gz | \
    psql postgresql://user:pass@localhost/dbname

# 4. Restore files
cd /
tar -xzf /var/backups/files/files_backup_YYYYMMDD_HHMMSS.tar.gz

# 5. Start application
sudo systemctl start awareness-platform

# 6. Verify application
curl https://your-domain.com/api/v1/health
```

## Backup Monitoring

### 1. Check Backup Status

```bash
# Check last backup time
ls -la /var/backups/database/ | head -2

# Check backup logs
tail -n 50 /var/log/backups/backup_*.log

# Check cron execution
grep CRON /var/log/syslog | grep backup
```

### 2. Set Up Alerts

Add monitoring to `automated_backup.sh`:

```bash
# Send email on failure
if [ "${OVERALL_STATUS}" = "FAILED" ]; then
    echo "Backup failed at $(date)" | mail -s "Backup Failed" admin@example.com
fi

# Send to monitoring system
curl -X POST https://monitoring.example.com/api/v1/events \
    -H "Content-Type: application/json" \
    -d "{
        \"service\": \"backup\",
        \"status\": \"${OVERALL_STATUS}\",
        \"message\": \"${MESSAGE}\"
    }"
```

## Disaster Recovery Plan

### 1. Regular Testing
- Test restore procedures monthly
- Document restore times
- Verify data integrity after restore

### 2. Off-site Backups
```bash
# Sync backups to S3 (add to cron)
aws s3 sync /var/backups/ s3://your-backup-bucket/backups/ \
    --exclude "*.log" \
    --delete

# Or use rsync to remote server
rsync -avz /var/backups/ backup-server:/remote/backups/
```

### 3. Recovery Time Objectives
- **RTO (Recovery Time Objective)**: 2 hours
- **RPO (Recovery Point Objective)**: 24 hours

### 4. Recovery Checklist
1. [ ] Identify backup to restore
2. [ ] Notify stakeholders
3. [ ] Create restore point
4. [ ] Stop application services
5. [ ] Restore database
6. [ ] Restore files
7. [ ] Verify data integrity
8. [ ] Start application services
9. [ ] Run smoke tests
10. [ ] Monitor for issues

## Troubleshooting

### Common Issues

1. **Backup fails with "permission denied"**
   ```bash
   # Fix permissions
   sudo chown -R www-data:www-data /var/backups
   sudo chmod 755 /var/backups
   ```

2. **Database backup fails with "pg_dump: command not found"**
   ```bash
   # Install PostgreSQL client
   sudo apt-get install postgresql-client
   ```

3. **Disk space issues**
   ```bash
   # Check disk usage
   df -h /var/backups
   
   # Clean old backups manually
   find /var/backups -name "*.gz" -mtime +30 -delete
   ```

4. **Restore fails with "database exists"**
   ```bash
   # Drop existing database first
   dropdb dbname
   createdb dbname
   ```

## Best Practices

1. **Test Restores Regularly**
   - Perform test restores monthly
   - Document the process and timing
   - Verify application functionality after restore

2. **Monitor Backup Health**
   - Check backup completion daily
   - Monitor backup sizes for anomalies
   - Set up alerts for failures

3. **Secure Backups**
   - Encrypt sensitive backups
   - Restrict access to backup directories
   - Use secure transfer for off-site backups

4. **Document Everything**
   - Keep restore procedures up-to-date
   - Document any custom configurations
   - Maintain contact list for emergencies

5. **Retention Policy**
   - Daily backups: 7 days
   - Weekly backups: 4 weeks
   - Monthly backups: 12 months
   - Adjust based on compliance requirements

## Compliance Considerations

### GDPR Compliance
- Implement backup encryption for personal data
- Honor data deletion requests in backups
- Document backup access logs

### Audit Trail
- Log all backup and restore operations
- Maintain chain of custody for backups
- Regular compliance audits

## Scripts Reference

### backup_database.py
- Creates PostgreSQL database backups
- Manages retention automatically
- Supports compression and verification

### backup_files.py
- Creates file system backups
- Generates SHA256 checksums
- Supports incremental backups

### automated_backup.sh
- Orchestrates all backup operations
- Sends notifications on failure
- Manages log rotation

### restore_backup.py
- Interactive and automated restore
- Creates restore points
- Supports partial restores

### verify_backups.sh
- Verifies backup integrity
- Tests restore capability
- Monitors backup age

## Support

For backup-related issues:
1. Check logs in `/var/log/backups/`
2. Run verification script
3. Contact system administrator
4. Escalate to database team if needed