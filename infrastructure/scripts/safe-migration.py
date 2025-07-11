#!/usr/bin/env python3
"""
Safe database migration script with transaction support and rollback capability.
"""

import os
import sys
import logging
from datetime import datetime
from contextlib import contextmanager
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    logger.error("DATABASE_URL environment variable not set")
    sys.exit(1)


@contextmanager
def database_transaction(engine):
    """Context manager for database transactions with automatic rollback on error."""
    connection = engine.connect()
    transaction = connection.begin()
    
    try:
        yield connection
        transaction.commit()
        logger.info("Transaction committed successfully")
    except Exception as e:
        logger.error(f"Error during migration: {e}")
        transaction.rollback()
        logger.info("Transaction rolled back")
        raise
    finally:
        connection.close()


def check_database_health(engine):
    """Check if database is healthy and accessible."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        logger.info("Database health check passed")
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


def backup_schema(engine):
    """Create a backup of the current schema."""
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    backup_name = f"schema_backup_{timestamp}"
    
    try:
        with engine.connect() as conn:
            # Create backup schema
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {backup_name}"))
            
            # Get all tables in public schema
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
            """))
            
            tables = [row[0] for row in result]
            
            # Copy structure and data for each table
            for table in tables:
                logger.info(f"Backing up table: {table}")
                conn.execute(text(f"""
                    CREATE TABLE {backup_name}.{table} 
                    AS SELECT * FROM public.{table}
                """))
            
            conn.commit()
            logger.info(f"Schema backup created: {backup_name}")
            return backup_name
            
    except Exception as e:
        logger.error(f"Failed to create schema backup: {e}")
        return None


def validate_migration(connection, alembic_cfg):
    """Validate that migrations can be applied safely."""
    try:
        # Check current revision
        from alembic.runtime.migration import MigrationContext
        context = MigrationContext.configure(connection)
        current_rev = context.get_current_revision()
        logger.info(f"Current database revision: {current_rev}")
        
        # Check pending migrations
        from alembic.script import ScriptDirectory
        script = ScriptDirectory.from_config(alembic_cfg)
        head_rev = script.get_current_head()
        logger.info(f"Target revision: {head_rev}")
        
        if current_rev == head_rev:
            logger.info("Database is already up to date")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Migration validation failed: {e}")
        raise


def run_migrations():
    """Run database migrations with safety checks and transaction support."""
    logger.info("Starting safe migration process...")
    
    # Create engine
    engine = create_engine(DATABASE_URL, echo=False)
    
    # Check database health
    if not check_database_health(engine):
        logger.error("Database health check failed, aborting migration")
        sys.exit(1)
    
    # Create Alembic configuration
    alembic_cfg = Config("alembic.ini")
    
    # Create backup
    backup_name = backup_schema(engine)
    if not backup_name:
        logger.warning("Failed to create backup, proceed with caution")
        response = input("Continue without backup? (yes/no): ")
        if response.lower() != "yes":
            logger.info("Migration aborted by user")
            sys.exit(0)
    
    try:
        # Run migrations in a transaction
        with database_transaction(engine) as connection:
            # Validate migrations
            if not validate_migration(connection, alembic_cfg):
                logger.info("No migrations to apply")
                return
            
            # Set connection for Alembic
            alembic_cfg.attributes['connection'] = connection
            
            # Run migrations
            logger.info("Applying migrations...")
            command.upgrade(alembic_cfg, "head")
            
            # Verify migration success
            from alembic.runtime.migration import MigrationContext
            context = MigrationContext.configure(connection)
            current_rev = context.get_current_revision()
            logger.info(f"Migration completed. New revision: {current_rev}")
            
            # Run post-migration validation
            logger.info("Running post-migration validation...")
            
            # Check critical tables exist
            critical_tables = ['users', 'companies', 'courses', 'user_progress']
            result = connection.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
            """))
            existing_tables = {row[0] for row in result}
            
            missing_tables = set(critical_tables) - existing_tables
            if missing_tables:
                raise Exception(f"Critical tables missing after migration: {missing_tables}")
            
            logger.info("Post-migration validation passed")
            
            # Clean up old backup schemas (keep last 5)
            if backup_name:
                result = connection.execute(text("""
                    SELECT schema_name 
                    FROM information_schema.schemata 
                    WHERE schema_name LIKE 'schema_backup_%'
                    ORDER BY schema_name DESC
                """))
                
                backup_schemas = [row[0] for row in result]
                schemas_to_delete = backup_schemas[5:]  # Keep last 5 backups
                
                for schema in schemas_to_delete:
                    logger.info(f"Removing old backup schema: {schema}")
                    connection.execute(text(f"DROP SCHEMA {schema} CASCADE"))
    
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        
        if backup_name:
            logger.info(f"Migration failed. Backup available at: {backup_name}")
            logger.info(f"To restore, run: psql -c 'DROP SCHEMA public CASCADE; ALTER SCHEMA {backup_name} RENAME TO public;'")
        
        sys.exit(1)
    
    logger.info("Migration completed successfully!")


if __name__ == "__main__":
    run_migrations()