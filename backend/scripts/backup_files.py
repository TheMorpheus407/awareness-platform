#!/usr/bin/env python3
"""
File backup script for uploaded content.
Creates compressed archives of uploaded files with timestamp.
"""

import os
import sys
import datetime
import tarfile
import shutil
from pathlib import Path
from typing import Optional, List
import argparse
import logging
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FileBackup:
    """Handle uploaded file backups."""
    
    def __init__(
        self,
        upload_dir: str = "/app/uploads",
        backup_dir: str = "/var/backups/files",
        retention_days: int = 7
    ):
        """
        Initialize file backup handler.
        
        Args:
            upload_dir: Directory containing uploaded files
            backup_dir: Directory to store backups
            retention_days: Number of days to keep backups
        """
        self.upload_dir = Path(upload_dir)
        self.backup_dir = Path(backup_dir)
        self.retention_days = retention_days
        
        # Create backup directory if it doesn't exist
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
    def create_backup(self) -> Optional[Path]:
        """
        Create a compressed backup of uploaded files.
        
        Returns:
            Path to the backup file if successful, None otherwise
        """
        if not self.upload_dir.exists():
            logger.error(f"Upload directory {self.upload_dir} does not exist")
            return None
            
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"files_backup_{timestamp}.tar.gz"
        backup_path = self.backup_dir / backup_name
        
        try:
            logger.info(f"Starting file backup to {backup_path}")
            
            # Count files to backup
            file_count = sum(1 for _ in self.upload_dir.rglob("*") if _.is_file())
            logger.info(f"Found {file_count} files to backup")
            
            # Create compressed tar archive
            with tarfile.open(backup_path, "w:gz") as tar:
                tar.add(self.upload_dir, arcname="uploads")
            
            # Get file size
            size_mb = backup_path.stat().st_size / (1024 * 1024)
            logger.info(f"Backup completed: {backup_path} ({size_mb:.2f} MB)")
            
            # Generate checksum
            checksum = self._generate_checksum(backup_path)
            checksum_path = backup_path.with_suffix(".tar.gz.sha256")
            checksum_path.write_text(f"{checksum}  {backup_name}\n")
            logger.info(f"Checksum saved to {checksum_path}")
            
            return backup_path
            
        except Exception as e:
            logger.error(f"Backup failed: {str(e)}")
            if backup_path.exists():
                backup_path.unlink()
            return None
    
    def _generate_checksum(self, file_path: Path) -> str:
        """Generate SHA256 checksum for a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def verify_backup(self, backup_path: Path) -> bool:
        """
        Verify backup integrity using checksum.
        
        Args:
            backup_path: Path to the backup file
            
        Returns:
            True if backup is valid, False otherwise
        """
        checksum_path = backup_path.with_suffix(".tar.gz.sha256")
        
        if not checksum_path.exists():
            logger.warning(f"Checksum file not found: {checksum_path}")
            return False
        
        try:
            # Read expected checksum
            expected_checksum = checksum_path.read_text().split()[0]
            
            # Calculate actual checksum
            actual_checksum = self._generate_checksum(backup_path)
            
            if expected_checksum == actual_checksum:
                logger.info("Backup verification successful")
                return True
            else:
                logger.error("Checksum mismatch!")
                return False
                
        except Exception as e:
            logger.error(f"Verification failed: {str(e)}")
            return False
    
    def cleanup_old_backups(self) -> List[Path]:
        """
        Remove backups older than retention_days.
        
        Returns:
            List of removed backup files
        """
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=self.retention_days)
        removed_files = []
        
        for backup_file in self.backup_dir.glob("files_backup_*.tar.gz"):
            try:
                # Extract timestamp from filename
                timestamp_str = backup_file.stem.replace("files_backup_", "").replace(".tar", "")
                file_date = datetime.datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                
                if file_date < cutoff_date:
                    logger.info(f"Removing old backup: {backup_file}")
                    
                    # Remove backup and checksum files
                    backup_file.unlink()
                    removed_files.append(backup_file)
                    
                    checksum_file = backup_file.with_suffix(".tar.gz.sha256")
                    if checksum_file.exists():
                        checksum_file.unlink()
                        
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
        
        for backup_file in sorted(self.backup_dir.glob("files_backup_*.tar.gz"), reverse=True):
            try:
                timestamp_str = backup_file.stem.replace("files_backup_", "").replace(".tar", "")
                file_date = datetime.datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                size_mb = backup_file.stat().st_size / (1024 * 1024)
                
                # Check if verified
                checksum_exists = backup_file.with_suffix(".tar.gz.sha256").exists()
                
                backups.append({
                    "filename": backup_file.name,
                    "path": str(backup_file),
                    "date": file_date.isoformat(),
                    "size_mb": round(size_mb, 2),
                    "age_days": (datetime.datetime.now() - file_date).days,
                    "verified": checksum_exists
                })
            except Exception as e:
                logger.warning(f"Could not process file {backup_file}: {str(e)}")
        
        return backups
    
    def restore_backup(self, backup_path: Path, restore_dir: Optional[Path] = None) -> bool:
        """
        Restore files from a backup.
        
        Args:
            backup_path: Path to the backup file
            restore_dir: Directory to restore to (defaults to original location)
            
        Returns:
            True if successful, False otherwise
        """
        if not backup_path.exists():
            logger.error(f"Backup file not found: {backup_path}")
            return False
        
        # Verify backup first
        if not self.verify_backup(backup_path):
            logger.error("Backup verification failed, aborting restore")
            return False
        
        restore_to = restore_dir or self.upload_dir.parent
        
        try:
            logger.info(f"Restoring backup {backup_path} to {restore_to}")
            
            # Create restore directory if needed
            restore_to.mkdir(parents=True, exist_ok=True)
            
            # Extract backup
            with tarfile.open(backup_path, "r:gz") as tar:
                tar.extractall(restore_to)
            
            logger.info("Restore completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Restore failed: {str(e)}")
            return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Uploaded files backup utility")
    parser.add_argument(
        "--upload-dir",
        default="/app/uploads",
        help="Directory containing uploaded files"
    )
    parser.add_argument(
        "--backup-dir",
        default="/var/backups/files",
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
    parser.add_argument(
        "--restore",
        help="Restore from specific backup file"
    )
    parser.add_argument(
        "--restore-dir",
        help="Directory to restore files to"
    )
    
    args = parser.parse_args()
    
    # Initialize backup handler
    backup = FileBackup(
        upload_dir=args.upload_dir,
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
                verified = "✓" if b['verified'] else "✗"
                print(f"{b['filename']} - {b['size_mb']} MB - {b['age_days']} days old - Verified: {verified}")
        else:
            print("No backups found")
        return
    
    # Restore backup if requested
    if args.restore:
        backup_path = Path(args.restore)
        restore_dir = Path(args.restore_dir) if args.restore_dir else None
        
        if backup.restore_backup(backup_path, restore_dir):
            logger.info("Restore completed successfully")
            sys.exit(0)
        else:
            logger.error("Restore failed")
            sys.exit(1)
    
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