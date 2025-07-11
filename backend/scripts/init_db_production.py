#!/usr/bin/env python3
"""Production database initialization with comprehensive error handling."""

import os
import sys
import time
import asyncio
from pathlib import Path
from sqlalchemy import create_engine, text
from alembic.config import Config
from alembic import command
from loguru import logger

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from core.config import settings


def wait_for_database(max_retries=30, retry_interval=2):
    """Wait for database to be available."""
    db_url = str(settings.DATABASE_URL)
    
    # Convert async URL to sync
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    
    # Extract database name and create postgres URL
    parts = db_url.split("/")
    db_name = parts[-1].split("?")[0]
    postgres_url = "/".join(parts[:-1]) + "/postgres"
    
    logger.info(f"Waiting for database server to be available...")
    
    for attempt in range(max_retries):
        try:
            engine = create_engine(postgres_url)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                logger.info("Database server is available")
                return True
        except Exception as e:
            logger.warning(f"Database not ready (attempt {attempt + 1}/{max_retries}): {e}")
            time.sleep(retry_interval)
    
    logger.error("Database server did not become available in time")
    return False


def ensure_database_exists():
    """Ensure database exists, create if not."""
    db_url = str(settings.DATABASE_URL)
    
    # Convert async URL to sync
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    
    # Extract database name and create postgres URL
    parts = db_url.split("/")
    db_name = parts[-1].split("?")[0]
    postgres_url = "/".join(parts[:-1]) + "/postgres"
    
    logger.info(f"Checking if database '{db_name}' exists...")
    
    try:
        engine = create_engine(postgres_url, isolation_level="AUTOCOMMIT")
        with engine.connect() as conn:
            # Check if database exists
            result = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :dbname"),
                {"dbname": db_name}
            ).fetchone()
            
            if not result:
                logger.info(f"Database '{db_name}' does not exist. Creating...")
                conn.execute(text(f"CREATE DATABASE {db_name}"))
                logger.info(f"Database '{db_name}' created successfully")
            else:
                logger.info(f"Database '{db_name}' already exists")
        
        return True
                
    except Exception as e:
        logger.error(f"Error checking/creating database: {e}")
        return False


def clean_existing_enums():
    """Clean up existing enum types to prevent conflicts."""
    db_url = str(settings.DATABASE_URL)
    
    # Convert async URL to sync
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    
    logger.info("Cleaning up existing enum types...")
    
    enum_types = [
        "subscriptionstatus",
        "userrole", 
        "campaignstatus",
        "emailstatus",
        "phishingstatus",
        "enrollmentstatus",
        "quizstatus",
        "notificationtype",
        "notificationstatus"
    ]
    
    try:
        engine = create_engine(db_url)
        with engine.begin() as conn:
            # Get all existing enum types
            result = conn.execute(
                text("""
                    SELECT typname 
                    FROM pg_type 
                    WHERE typtype = 'e' 
                    AND typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
                """)
            )
            existing_enums = [row[0] for row in result]
            
            # Drop existing enums
            for enum_type in existing_enums:
                if enum_type.lower() in enum_types:
                    logger.info(f"Dropping existing enum type: {enum_type}")
                    conn.execute(text(f"DROP TYPE IF EXISTS {enum_type} CASCADE"))
            
        logger.info("Enum cleanup complete")
        return True
        
    except Exception as e:
        logger.error(f"Error during enum cleanup: {e}")
        return False


def run_alembic_migrations():
    """Run Alembic migrations with proper error handling."""
    logger.info("Running database migrations...")
    
    alembic_ini_path = Path(__file__).parent.parent / "alembic.ini"
    
    if not alembic_ini_path.exists():
        logger.error(f"Alembic configuration not found at {alembic_ini_path}")
        return False
    
    try:
        # Change to backend directory
        original_cwd = os.getcwd()
        os.chdir(Path(__file__).parent.parent)
        
        # Create Alembic configuration
        alembic_cfg = Config(str(alembic_ini_path))
        
        # Override database URL
        alembic_cfg.set_main_option("sqlalchemy.url", str(settings.DATABASE_URL))
        
        # Check current revision
        from alembic.runtime.migration import MigrationContext
        from sqlalchemy import create_engine
        
        db_url = str(settings.DATABASE_URL)
        if db_url.startswith("postgresql+asyncpg://"):
            db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
            
        engine = create_engine(db_url)
        with engine.connect() as conn:
            context = MigrationContext.configure(conn)
            current_rev = context.get_current_revision()
            logger.info(f"Current database revision: {current_rev}")
        
        # Run migrations
        command.upgrade(alembic_cfg, "head")
        
        # Verify new revision
        with engine.connect() as conn:
            context = MigrationContext.configure(conn)
            new_rev = context.get_current_revision()
            logger.info(f"Database upgraded to revision: {new_rev}")
        
        os.chdir(original_cwd)
        logger.info("Migrations completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error running migrations: {e}", exc_info=True)
        os.chdir(original_cwd)
        return False


def verify_essential_tables():
    """Verify that essential tables exist after migration."""
    db_url = str(settings.DATABASE_URL)
    
    # Convert async URL to sync
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    
    logger.info("Verifying essential database tables...")
    
    essential_tables = [
        "alembic_version",
        "users",
        "organizations", 
        "roles",
        "permissions",
        "role_permissions",
        "user_roles",
        "courses",
        "enrollments",
        "analytics_events"
    ]
    
    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            missing_tables = []
            
            for table in essential_tables:
                result = conn.execute(
                    text("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' 
                            AND table_name = :table_name
                        )
                    """),
                    {"table_name": table}
                ).scalar()
                
                if result:
                    logger.info(f"✓ Table '{table}' exists")
                else:
                    logger.error(f"✗ Table '{table}' is missing")
                    missing_tables.append(table)
            
            if missing_tables:
                logger.error(f"Missing tables: {', '.join(missing_tables)}")
                return False
                
        logger.info("All essential tables verified successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error verifying tables: {e}")
        return False


def create_initial_data():
    """Create initial data if needed."""
    db_url = str(settings.DATABASE_URL)
    
    # Convert async URL to sync
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    
    logger.info("Creating initial data...")
    
    try:
        engine = create_engine(db_url)
        with engine.begin() as conn:
            # Check if we have any roles
            result = conn.execute(text("SELECT COUNT(*) FROM roles")).scalar()
            
            if result == 0:
                logger.info("Creating default roles...")
                
                # Create default roles
                conn.execute(text("""
                    INSERT INTO roles (name, description) VALUES
                    ('admin', 'System Administrator'),
                    ('manager', 'Company Manager'),
                    ('instructor', 'Course Instructor'),
                    ('user', 'Regular User')
                    ON CONFLICT (name) DO NOTHING
                """))
                
                logger.info("Default roles created")
            
            # Check if we have any permissions
            result = conn.execute(text("SELECT COUNT(*) FROM permissions")).scalar()
            
            if result == 0:
                logger.info("Creating default permissions...")
                
                # Create default permissions
                permissions = [
                    ('users:read', 'View users'),
                    ('users:write', 'Create/update users'),
                    ('users:delete', 'Delete users'),
                    ('companies:read', 'View companies'),
                    ('companies:write', 'Create/update companies'),
                    ('companies:delete', 'Delete companies'),
                    ('courses:read', 'View courses'),
                    ('courses:write', 'Create/update courses'),
                    ('courses:delete', 'Delete courses'),
                    ('analytics:read', 'View analytics'),
                    ('phishing:read', 'View phishing campaigns'),
                    ('phishing:write', 'Create/update phishing campaigns')
                ]
                
                for resource_action, description in permissions:
                    resource, action = resource_action.split(':')
                    conn.execute(
                        text("""
                            INSERT INTO permissions (resource, action, description)
                            VALUES (:resource, :action, :description)
                            ON CONFLICT (resource, action) DO NOTHING
                        """),
                        {"resource": resource, "action": action, "description": description}
                    )
                
                logger.info("Default permissions created")
                
                # Assign permissions to admin role
                conn.execute(text("""
                    INSERT INTO role_permissions (role_id, permission_id)
                    SELECT r.id, p.id
                    FROM roles r
                    CROSS JOIN permissions p
                    WHERE r.name = 'admin'
                    ON CONFLICT DO NOTHING
                """))
                
                logger.info("Admin role permissions assigned")
        
        return True
        
    except Exception as e:
        logger.error(f"Error creating initial data: {e}")
        return False


def main():
    """Main initialization function."""
    logger.info("=== Starting Production Database Initialization ===")
    
    # Step 1: Wait for database server
    if not wait_for_database():
        logger.error("Database server is not available")
        return 1
    
    # Step 2: Ensure database exists
    if not ensure_database_exists():
        logger.error("Failed to ensure database exists")
        return 1
    
    # Step 3: Clean existing enums
    if not clean_existing_enums():
        logger.warning("Failed to clean existing enums, continuing anyway...")
    
    # Step 4: Run migrations
    if not run_alembic_migrations():
        logger.error("Failed to run migrations")
        return 1
    
    # Step 5: Verify tables
    if not verify_essential_tables():
        logger.error("Essential tables are missing")
        return 1
    
    # Step 6: Create initial data
    if not create_initial_data():
        logger.warning("Failed to create initial data, but database is initialized")
    
    logger.info("=== Production Database Initialization Complete ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())