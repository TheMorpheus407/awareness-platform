#!/usr/bin/env python3
"""Check database status and migration state."""

import sys
from pathlib import Path
from sqlalchemy import create_engine, text
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from core.config import settings
from loguru import logger


def check_database_status():
    """Check database connection and status."""
    db_url = str(settings.DATABASE_URL)
    
    # Convert async URL to sync
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    
    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            # Test connection
            result = conn.execute(text("SELECT version()")).fetchone()
            logger.info(f"✓ Database connected: {result[0]}")
            
            # Check if alembic_version table exists
            alembic_exists = conn.execute(
                text("""
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'alembic_version'
                """)
            ).fetchone()
            
            if alembic_exists:
                # Get current revision
                current_rev = conn.execute(
                    text("SELECT version_num FROM alembic_version")
                ).fetchone()
                
                if current_rev:
                    logger.info(f"✓ Current migration: {current_rev[0]}")
                else:
                    logger.warning("⚠ Alembic version table exists but no revision recorded")
            else:
                logger.warning("⚠ No alembic_version table found - migrations not run")
            
            # Count tables
            table_count = conn.execute(
                text("""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    AND table_type = 'BASE TABLE'
                """)
            ).fetchone()[0]
            
            logger.info(f"✓ Tables in database: {table_count}")
            
            # List some key tables
            key_tables = ["users", "organizations", "roles", "permissions"]
            for table in key_tables:
                exists = conn.execute(
                    text("""
                        SELECT 1 FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = :table_name
                    """),
                    {"table_name": table}
                ).fetchone()
                
                if exists:
                    # Get row count
                    count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).fetchone()[0]
                    logger.info(f"  • {table}: {count} rows")
                else:
                    logger.warning(f"  ✗ {table}: NOT FOUND")
                    
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False
    
    return True


def check_pending_migrations():
    """Check for pending migrations."""
    alembic_cfg = Config(Path(__file__).parent.parent / "alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", str(settings.DATABASE_URL))
    
    script_dir = ScriptDirectory.from_config(alembic_cfg)
    
    db_url = str(settings.DATABASE_URL)
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    
    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            context = MigrationContext.configure(conn)
            current_heads = context.get_current_heads()
            
            logger.info("\n=== Migration Status ===")
            if current_heads:
                logger.info(f"Current revision(s): {', '.join(current_heads)}")
            else:
                logger.info("No migrations applied yet")
            
            # Get all revisions
            all_revisions = list(script_dir.walk_revisions())
            logger.info(f"Total migrations available: {len(all_revisions)}")
            
            # Check for pending migrations
            if current_heads:
                pending = []
                for rev in all_revisions:
                    if rev.revision not in current_heads:
                        # Check if this revision is an ancestor of current head
                        if not any(script_dir.is_base(rev.revision, head) for head in current_heads):
                            pending.append(rev)
                
                if pending:
                    logger.warning(f"\n⚠ Pending migrations: {len(pending)}")
                    for rev in pending[:5]:  # Show first 5
                        logger.warning(f"  - {rev.revision[:12]}: {rev.doc}")
                    if len(pending) > 5:
                        logger.warning(f"  ... and {len(pending) - 5} more")
                else:
                    logger.info("✓ All migrations applied")
            else:
                logger.warning(f"⚠ No migrations applied - {len(all_revisions)} pending")
                
    except Exception as e:
        logger.error(f"Error checking migrations: {e}")
        return False
    
    return True


def main():
    """Main function."""
    logger.info("=== Database Status Check ===\n")
    
    # Check database connection and tables
    db_ok = check_database_status()
    
    if db_ok:
        # Check migration status
        check_pending_migrations()
    
    logger.info("\n=== Check Complete ===")
    return 0 if db_ok else 1


if __name__ == "__main__":
    sys.exit(main())