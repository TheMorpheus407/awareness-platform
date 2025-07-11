#!/bin/bash
# Backup verification script
# Verifies integrity of all backups and tests restore capability

set -euo pipefail

# Configuration
BACKUP_DIR="/var/backups"
LOG_DIR="/var/log/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="${LOG_DIR}/verify_${TIMESTAMP}.log"
TEST_DB="test_restore_db"

# Create log directory
mkdir -p "${LOG_DIR}"

# Function to log messages
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "${LOG_FILE}"
}

# Function to verify database backup
verify_db_backup() {
    local backup_file=$1
    log "Verifying database backup: ${backup_file}"
    
    # Check if file exists and is readable
    if [ ! -r "${backup_file}" ]; then
        log "ERROR: Cannot read backup file ${backup_file}"
        return 1
    fi
    
    # Check if file is a valid gzip
    if ! gzip -t "${backup_file}" 2>/dev/null; then
        log "ERROR: ${backup_file} is not a valid gzip file"
        return 1
    fi
    
    # Check if it contains SQL
    if ! zcat "${backup_file}" | head -n 100 | grep -q "PostgreSQL"; then
        log "WARNING: ${backup_file} may not be a valid PostgreSQL dump"
        return 1
    fi
    
    log "Database backup ${backup_file} verified successfully"
    return 0
}

# Function to verify file backup
verify_file_backup() {
    local backup_file=$1
    local checksum_file="${backup_file}.sha256"
    
    log "Verifying file backup: ${backup_file}"
    
    # Check if file exists and is readable
    if [ ! -r "${backup_file}" ]; then
        log "ERROR: Cannot read backup file ${backup_file}"
        return 1
    fi
    
    # Check if checksum file exists
    if [ ! -r "${checksum_file}" ]; then
        log "WARNING: No checksum file for ${backup_file}"
        # Still try to verify the tar file
        if ! tar -tzf "${backup_file}" >/dev/null 2>&1; then
            log "ERROR: ${backup_file} is not a valid tar.gz file"
            return 1
        fi
    else
        # Verify checksum
        if ! sha256sum -c "${checksum_file}" >/dev/null 2>&1; then
            log "ERROR: Checksum verification failed for ${backup_file}"
            return 1
        fi
    fi
    
    log "File backup ${backup_file} verified successfully"
    return 0
}

# Start verification
log "=== Starting backup verification ==="

# Initialize counters
TOTAL_DB_BACKUPS=0
VALID_DB_BACKUPS=0
TOTAL_FILE_BACKUPS=0
VALID_FILE_BACKUPS=0

# Verify database backups
log "Verifying database backups..."
for backup in $(find "${BACKUP_DIR}/database" -name "db_backup_*.sql.gz" -type f | sort -r | head -10); do
    TOTAL_DB_BACKUPS=$((TOTAL_DB_BACKUPS + 1))
    if verify_db_backup "${backup}"; then
        VALID_DB_BACKUPS=$((VALID_DB_BACKUPS + 1))
    fi
done

# Verify file backups
log "Verifying file backups..."
for backup in $(find "${BACKUP_DIR}/files" -name "files_backup_*.tar.gz" -type f | sort -r | head -10); do
    TOTAL_FILE_BACKUPS=$((TOTAL_FILE_BACKUPS + 1))
    if verify_file_backup "${backup}"; then
        VALID_FILE_BACKUPS=$((VALID_FILE_BACKUPS + 1))
    fi
done

# Test restore capability (using most recent valid backup)
log "Testing restore capability..."
LATEST_DB_BACKUP=$(find "${BACKUP_DIR}/database" -name "db_backup_*.sql.gz" -type f | sort -r | head -1)

if [ -n "${LATEST_DB_BACKUP}" ] && [ -f "${LATEST_DB_BACKUP}" ]; then
    log "Testing restore with ${LATEST_DB_BACKUP}"
    
    # Create test database
    if createdb "${TEST_DB}" 2>/dev/null; then
        # Try to restore
        if zcat "${LATEST_DB_BACKUP}" | psql "${TEST_DB}" >/dev/null 2>&1; then
            log "Test restore successful"
            RESTORE_TEST="PASSED"
        else
            log "ERROR: Test restore failed"
            RESTORE_TEST="FAILED"
        fi
        
        # Drop test database
        dropdb "${TEST_DB}" 2>/dev/null || true
    else
        log "WARNING: Could not create test database"
        RESTORE_TEST="SKIPPED"
    fi
else
    log "WARNING: No database backup found for restore test"
    RESTORE_TEST="SKIPPED"
fi

# Check backup age
log "Checking backup age..."
LATEST_BACKUP_AGE=999
if [ -n "${LATEST_DB_BACKUP}" ]; then
    LATEST_BACKUP_TIME=$(stat -c %Y "${LATEST_DB_BACKUP}")
    CURRENT_TIME=$(date +%s)
    LATEST_BACKUP_AGE=$(( (CURRENT_TIME - LATEST_BACKUP_TIME) / 3600 ))
    log "Latest backup age: ${LATEST_BACKUP_AGE} hours"
fi

# Generate summary
log "=== Verification Summary ==="
log "Database backups: ${VALID_DB_BACKUPS}/${TOTAL_DB_BACKUPS} valid"
log "File backups: ${VALID_FILE_BACKUPS}/${TOTAL_FILE_BACKUPS} valid"
log "Restore test: ${RESTORE_TEST}"
log "Latest backup age: ${LATEST_BACKUP_AGE} hours"

# Determine overall status
if [ ${VALID_DB_BACKUPS} -eq 0 ] || [ ${VALID_FILE_BACKUPS} -eq 0 ]; then
    STATUS="CRITICAL"
    MESSAGE="No valid backups found!"
elif [ "${RESTORE_TEST}" = "FAILED" ]; then
    STATUS="CRITICAL"
    MESSAGE="Restore test failed!"
elif [ ${LATEST_BACKUP_AGE} -gt 48 ]; then
    STATUS="WARNING"
    MESSAGE="Latest backup is older than 48 hours"
elif [ ${VALID_DB_BACKUPS} -lt ${TOTAL_DB_BACKUPS} ] || [ ${VALID_FILE_BACKUPS} -lt ${TOTAL_FILE_BACKUPS} ]; then
    STATUS="WARNING"
    MESSAGE="Some backups failed verification"
else
    STATUS="OK"
    MESSAGE="All backups verified successfully"
fi

log "Overall status: ${STATUS} - ${MESSAGE}"

# Clean up old verification logs
find "${LOG_DIR}" -name "verify_*.log" -mtime +30 -delete

# Exit with appropriate code
case ${STATUS} in
    "OK")
        exit 0
        ;;
    "WARNING")
        exit 1
        ;;
    "CRITICAL")
        exit 2
        ;;
esac