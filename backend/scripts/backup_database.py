#!/usr/bin/env python3
"""
Database backup script for PostgreSQL.
Creates compressed backups with timestamp and manages retention.
"""

import os
import sys
import subprocess
import datetime
import gzip
import shutil
from pathlib import Path
from typing import Optional, List
import argparse
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseBackup:
    """Handle PostgreSQL database backups."""
    
    def __init__(
        self,
        database_url: str,
        backup_dir: str = "/var/backups/database",
        retention_days: int = 7
    ):
        """
        Initialize backup handler.
        
        Args:
            database_url: PostgreSQL connection URL
            backup_dir: Directory to store backups
            retention_days: Number of days to keep backups
        """
        self.database_url = database_url
        self.backup_dir = Path(backup_dir)
        self.retention_days = retention_days
        
        # Create backup directory if it doesn't exist
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
    def create_backup(self) -> Optional[Path]:
        """
        Create a database backup.
        
        Returns:
            Path to the backup file if successful, None otherwise
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"db_backup_{timestamp}.sql"
        backup_path = self.backup_dir / backup_name
        compressed_path = self.backup_dir / f"{backup_name}.gz"
        
        try:
            logger.info(f"Starting database backup to {backup_path}")
            
            # Run pg_dump
            result = subprocess.run(
                [
                    "pg_dump",
                    "--clean",
                    "--if-exists",
                    "--no-owner",
                    "--no-privileges",
                    "--verbose",
                    self.database_url
                ],
                stdout=open(backup_path, 'w'),
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            
            logger.info("Database dump completed successfully")
            
            # Compress the backup
            logger.info(f"Compressing backup to {compressed_path}")
            with open(backup_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Remove uncompressed file
            backup_path.unlink()
            
            # Get file size
            size_mb = compressed_path.stat().st_size / (1024 * 1024)
            logger.info(f"Backup completed: {compressed_path} ({size_mb:.2f} MB)")
            
            return compressed_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"pg_dump failed: {e.stderr}")
            if backup_path.exists():
                backup_path.unlink()
            return None
        except Exception as e:
            logger.error(f"Backup failed: {str(e)}")
            if backup_path.exists():
                backup_path.unlink()
            return None
    
    def cleanup_old_backups(self) -> List[Path]:
        """
        Remove backups older than retention_days.
        
        Returns:
            List of removed backup files
        """
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=self.retention_days)
        removed_files = []
        
        for backup_file in self.backup_dir.glob("db_backup_*.sql.gz"):
            # Extract timestamp from filename
            try:
                timestamp_str = backup_file.stem.replace("db_backup_", "").replace(".sql", "")
                file_date = datetime.datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                
                if file_date < cutoff_date:
                    logger.info(f"Removing old backup: {backup_file}")
                    backup_file.unlink()
                    removed_files.append(backup_file)
            except Exception as e:
                logger.warning(f"Could not process file {backup_file}: {str(e)}")
        
        return removed_files
    
    def list_backups(self) -> List[dict]:
        """
        List all available backups.
        
        Returns:
            List of backup information dictionaries
        """
        backups = []
        
        for backup_file in sorted(self.backup_dir.glob("db_backup_*.sql.gz"), reverse=True):
            try:
                timestamp_str = backup_file.stem.replace("db_backup_", "").replace(".sql", "")
                file_date = datetime.datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                size_mb = backup_file.stat().st_size / (1024 * 1024)
                
                backups.append({
                    "filename": backup_file.name,
                    "path": str(backup_file),
                    "date": file_date.isoformat(),
                    "size_mb": round(size_mb, 2),
                    "age_days": (datetime.datetime.now() - file_date).days
                })
            except Exception as e:
                logger.warning(f"Could not process file {backup_file}: {str(e)}")
        
        return backups
    
    def verify_backup(self, backup_path: Path) -> bool:
        """
        Verify that a backup file is valid.
        
        Args:
            backup_path: Path to the backup file
            
        Returns:
            True if backup is valid, False otherwise
        """
        try:
            # Test if file can be decompressed
            with gzip.open(backup_path, 'rb') as f:
                # Read first few bytes to ensure it's valid
                f.read(1024)
            return True
        except Exception as e:
            logger.error(f"Backup verification failed for {backup_path}: {str(e)}")
            return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="PostgreSQL database backup utility")
    parser.add_argument(
        "--database-url",
        default=os.getenv("DATABASE_URL"),
        help="PostgreSQL connection URL"
    )
    parser.add_argument(
        "--backup-dir",
        default="/var/backups/database",
        help="Directory to store backups"
    )
    parser.add_argument(
        "--retention-days",
        type=int,
        default=7,
        help="Number of days to keep backups"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List existing backups"
    )
    parser.add_argument(
        "--cleanup-only",
        action="store_true",
        help="Only cleanup old backups without creating new one"
    )
    
    args = parser.parse_args()
    
    if not args.database_url:
        logger.error("DATABASE_URL not provided")
        sys.exit(1)
    
    # Initialize backup handler
    backup = DatabaseBackup(
        database_url=args.database_url,
        backup_dir=args.backup_dir,
        retention_days=args.retention_days
    )
    
    # List backups if requested
    if args.list:
        backups = backup.list_backups()
        if backups:
            print("\nAvailable backups:")
            print("-" * 80)
            for b in backups:
                print(f"{b['filename']} - {b['size_mb']} MB - {b['age_days']} days old")
        else:
            print("No backups found")
        return
    
    # Cleanup old backups
    removed = backup.cleanup_old_backups()
    if removed:
        logger.info(f"Removed {len(removed)} old backup(s)")
    
    # Create new backup unless cleanup-only
    if not args.cleanup_only:
        backup_file = backup.create_backup()
        if backup_file:
            # Verify the backup
            if backup.verify_backup(backup_file):
                logger.info("Backup verification successful")
                sys.exit(0)
            else:
                logger.error("Backup verification failed")
                sys.exit(1)
        else:
            logger.error("Backup creation failed")
            sys.exit(1)


if __name__ == "__main__":
    main()