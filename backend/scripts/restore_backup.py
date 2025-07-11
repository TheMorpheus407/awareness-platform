#!/usr/bin/env python3
"""
Restore script for database and file backups.
Provides interactive and automated restore capabilities.
"""

import os
import sys
import subprocess
import datetime
import gzip
import tempfile
from pathlib import Path
from typing import Optional, List, Tuple
import argparse
import logging
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BackupRestore:
    """Handle backup restoration for database and files."""
    
    def __init__(
        self,
        database_url: str,
        db_backup_dir: str = "/var/backups/database",
        file_backup_dir: str = "/var/backups/files"
    ):
        """
        Initialize restore handler.
        
        Args:
            database_url: PostgreSQL connection URL
            db_backup_dir: Directory containing database backups
            file_backup_dir: Directory containing file backups
        """
        self.database_url = database_url
        self.db_backup_dir = Path(db_backup_dir)
        self.file_backup_dir = Path(file_backup_dir)
        
    def list_available_backups(self) -> Tuple[List[dict], List[dict]]:
        """
        List all available database and file backups.
        
        Returns:
            Tuple of (database_backups, file_backups)
        """
        db_backups = []
        file_backups = []
        
        # List database backups
        for backup in sorted(self.db_backup_dir.glob("db_backup_*.sql.gz"), reverse=True):
            try:
                timestamp_str = backup.stem.replace("db_backup_", "").replace(".sql", "")
                backup_date = datetime.datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                size_mb = backup.stat().st_size / (1024 * 1024)
                
                db_backups.append({
                    "filename": backup.name,
                    "path": str(backup),
                    "date": backup_date,
                    "date_str": backup_date.strftime("%Y-%m-%d %H:%M:%S"),
                    "size_mb": round(size_mb, 2)
                })
            except Exception as e:
                logger.warning(f"Could not process database backup {backup}: {e}")
        
        # List file backups
        for backup in sorted(self.file_backup_dir.glob("files_backup_*.tar.gz"), reverse=True):
            try:
                timestamp_str = backup.stem.replace("files_backup_", "").replace(".tar", "")
                backup_date = datetime.datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                size_mb = backup.stat().st_size / (1024 * 1024)
                
                file_backups.append({
                    "filename": backup.name,
                    "path": str(backup),
                    "date": backup_date,
                    "date_str": backup_date.strftime("%Y-%m-%d %H:%M:%S"),
                    "size_mb": round(size_mb, 2)
                })
            except Exception as e:
                logger.warning(f"Could not process file backup {backup}: {e}")
        
        return db_backups, file_backups
    
    def restore_database(self, backup_path: str, confirm: bool = True) -> bool:
        """
        Restore database from backup.
        
        Args:
            backup_path: Path to the database backup file
            confirm: Whether to ask for confirmation
            
        Returns:
            True if successful, False otherwise
        """
        backup_file = Path(backup_path)
        if not backup_file.exists():
            logger.error(f"Backup file not found: {backup_path}")
            return False
        
        if confirm:
            print(f"\nWARNING: This will replace the current database with backup from {backup_file.name}")
            response = input("Are you sure you want to continue? (yes/no): ")
            if response.lower() != 'yes':
                logger.info("Restore cancelled by user")
                return False
        
        try:
            logger.info(f"Starting database restore from {backup_path}")
            
            # Create temporary uncompressed file
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.sql', delete=False) as tmp_file:
                tmp_path = tmp_file.name
                
                # Decompress backup
                logger.info("Decompressing backup file...")
                with gzip.open(backup_file, 'rb') as gz_file:
                    tmp_file.write(gz_file.read())
            
            # Restore using psql
            logger.info("Restoring database...")
            result = subprocess.run(
                ["psql", self.database_url, "-f", tmp_path],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Clean up temporary file
            os.unlink(tmp_path)
            
            logger.info("Database restore completed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Database restore failed: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Restore failed: {str(e)}")
            return False
        finally:
            # Ensure temporary file is cleaned up
            if 'tmp_path' in locals() and os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def restore_files(self, backup_path: str, restore_dir: Optional[str] = None, confirm: bool = True) -> bool:
        """
        Restore files from backup.
        
        Args:
            backup_path: Path to the file backup
            restore_dir: Directory to restore to (defaults to /app)
            confirm: Whether to ask for confirmation
            
        Returns:
            True if successful, False otherwise
        """
        # Import from backup_files module
        sys.path.insert(0, str(Path(__file__).parent))
        from backup_files import FileBackup
        
        backup = FileBackup()
        
        if confirm:
            print(f"\nWARNING: This will restore files from backup {Path(backup_path).name}")
            if restore_dir:
                print(f"Files will be restored to: {restore_dir}")
            response = input("Are you sure you want to continue? (yes/no): ")
            if response.lower() != 'yes':
                logger.info("Restore cancelled by user")
                return False
        
        restore_path = Path(restore_dir) if restore_dir else None
        return backup.restore_backup(Path(backup_path), restore_path)
    
    def create_restore_point(self) -> Optional[dict]:
        """
        Create a restore point before performing restore.
        
        Returns:
            Dictionary with restore point information
        """
        logger.info("Creating restore point...")
        
        # Import backup modules
        sys.path.insert(0, str(Path(__file__).parent))
        from backup_database import DatabaseBackup
        from backup_files import FileBackup
        
        restore_point = {
            "timestamp": datetime.datetime.now().isoformat(),
            "database_backup": None,
            "file_backup": None
        }
        
        # Create database backup
        db_backup = DatabaseBackup(self.database_url, backup_dir=str(self.db_backup_dir))
        db_path = db_backup.create_backup()
        if db_path:
            restore_point["database_backup"] = str(db_path)
            logger.info(f"Database restore point created: {db_path}")
        
        # Create file backup
        file_backup = FileBackup(backup_dir=str(self.file_backup_dir))
        file_path = file_backup.create_backup()
        if file_path:
            restore_point["file_backup"] = str(file_path)
            logger.info(f"File restore point created: {file_path}")
        
        # Save restore point metadata
        restore_point_file = self.db_backup_dir.parent / "restore_points.json"
        restore_points = []
        
        if restore_point_file.exists():
            restore_points = json.loads(restore_point_file.read_text())
        
        restore_points.append(restore_point)
        
        # Keep only last 10 restore points
        restore_points = restore_points[-10:]
        
        restore_point_file.write_text(json.dumps(restore_points, indent=2))
        
        return restore_point


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Backup restore utility")
    parser.add_argument(
        "--database-url",
        default=os.getenv("DATABASE_URL"),
        help="PostgreSQL connection URL"
    )
    parser.add_argument(
        "--db-backup-dir",
        default="/var/backups/database",
        help="Directory containing database backups"
    )
    parser.add_argument(
        "--file-backup-dir",
        default="/var/backups/files",
        help="Directory containing file backups"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available backups"
    )
    parser.add_argument(
        "--restore-db",
        help="Restore database from specific backup"
    )
    parser.add_argument(
        "--restore-files",
        help="Restore files from specific backup"
    )
    parser.add_argument(
        "--restore-dir",
        help="Directory to restore files to"
    )
    parser.add_argument(
        "--no-confirm",
        action="store_true",
        help="Skip confirmation prompts"
    )
    parser.add_argument(
        "--create-restore-point",
        action="store_true",
        help="Create restore point before restoring"
    )
    
    args = parser.parse_args()
    
    if not args.database_url:
        logger.error("DATABASE_URL not provided")
        sys.exit(1)
    
    # Initialize restore handler
    restore = BackupRestore(
        database_url=args.database_url,
        db_backup_dir=args.db_backup_dir,
        file_backup_dir=args.file_backup_dir
    )
    
    # List backups if requested
    if args.list:
        db_backups, file_backups = restore.list_available_backups()
        
        print("\nDatabase Backups:")
        print("-" * 80)
        if db_backups:
            for b in db_backups:
                print(f"{b['filename']} - {b['date_str']} - {b['size_mb']} MB")
        else:
            print("No database backups found")
        
        print("\nFile Backups:")
        print("-" * 80)
        if file_backups:
            for b in file_backups:
                print(f"{b['filename']} - {b['date_str']} - {b['size_mb']} MB")
        else:
            print("No file backups found")
        
        return
    
    # Create restore point if requested
    if args.create_restore_point or (args.restore_db or args.restore_files):
        restore_point = restore.create_restore_point()
        if restore_point:
            logger.info("Restore point created successfully")
        else:
            logger.warning("Failed to create complete restore point")
    
    # Restore database if requested
    if args.restore_db:
        if restore.restore_database(args.restore_db, confirm=not args.no_confirm):
            logger.info("Database restore completed successfully")
        else:
            logger.error("Database restore failed")
            sys.exit(1)
    
    # Restore files if requested
    if args.restore_files:
        if restore.restore_files(args.restore_files, args.restore_dir, confirm=not args.no_confirm):
            logger.info("File restore completed successfully")
        else:
            logger.error("File restore failed")
            sys.exit(1)


if __name__ == "__main__":
    main()