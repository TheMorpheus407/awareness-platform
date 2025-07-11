#!/usr/bin/env python3
"""Initialize database with proper error handling and migration support."""

import os
import sys
import asyncio
import subprocess
from pathlib import Path
from sqlalchemy import create_engine, text
from alembic.config import Config
from alembic import command

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from core.config import settings
from core.logging import setup_logging
from loguru import logger

# Setup logging
setup_logging()


def check_database_exists():
    """Check if database exists, create if not."""
    # Parse DATABASE_URL to get connection parts
    db_url = str(settings.DATABASE_URL)
    
    # Convert async URL to sync
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    
    # Split off database name to connect to postgres database
    parts = db_url.split("/")
    db_name = parts[-1].split("?")[0]
    postgres_url = "/".join(parts[:-1]) + "/postgres"
    
    logger.info(f"Checking if database '{db_name}' exists...")
    
    try:
        # Connect to postgres database
        engine = create_engine(postgres_url)
        with engine.connect() as conn:
            # Check if database exists
            result = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :dbname"),
                {"dbname": db_name}
            ).fetchone()
            
            if not result:
                logger.info(f"Database '{db_name}' does not exist. Creating...")
                # Need to be outside transaction to create database
                conn.execute(text("COMMIT"))
                conn.execute(text(f"CREATE DATABASE {db_name}"))
                logger.info(f"Database '{db_name}' created successfully")
            else:
                logger.info(f"Database '{db_name}' already exists")
                
    except Exception as e:
        logger.error(f"Error checking/creating database: {e}")
        raise


def clean_enum_types():
    """Clean up any existing enum types that might cause conflicts."""
    db_url = str(settings.DATABASE_URL)
    
    # Convert async URL to sync
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    
    logger.info("Cleaning up enum types...")
    
    enum_types = [
        "subscriptionstatus",
        "userrole", 
        "campaignstatus",
        "emailstatus",
        "phishingstatus",
        "enrollmentstatus"
    ]
    
    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            for enum_type in enum_types:
                try:
                    # Check if enum exists
                    result = conn.execute(
                        text("SELECT 1 FROM pg_type WHERE typname = :name"),
                        {"name": enum_type}
                    ).fetchone()
                    
                    if result:
                        logger.info(f"Dropping existing enum type: {enum_type}")
                        conn.execute(text(f"DROP TYPE IF EXISTS {enum_type} CASCADE"))
                        conn.commit()
                except Exception as e:
                    logger.warning(f"Could not drop enum {enum_type}: {e}")
                    
        logger.info("Enum cleanup complete")
    except Exception as e:
        logger.error(f"Error during enum cleanup: {e}")
        # Don't fail initialization if enum cleanup fails
        logger.warning("Continuing despite enum cleanup errors...")


def run_migrations():
    """Run Alembic migrations."""
    logger.info("Running database migrations...")
    
    # Get alembic config
    alembic_ini_path = Path(__file__).parent.parent / "alembic.ini"
    
    if not alembic_ini_path.exists():
        logger.error(f"Alembic configuration not found at {alembic_ini_path}")
        raise FileNotFoundError(f"Alembic configuration not found at {alembic_ini_path}")
    
    try:
        # Change to backend directory for alembic to work properly
        os.chdir(Path(__file__).parent.parent)
        
        # Create Alembic configuration
        alembic_cfg = Config(str(alembic_ini_path))
        
        # Override database URL
        alembic_cfg.set_main_option("sqlalchemy.url", str(settings.DATABASE_URL))
        
        # Run migrations
        command.upgrade(alembic_cfg, "head")
        
        logger.info("Migrations completed successfully")
    except Exception as e:
        logger.error(f"Error running migrations: {e}")
        raise


def verify_tables():
    """Verify that essential tables exist."""
    db_url = str(settings.DATABASE_URL)
    
    # Convert async URL to sync
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    
    logger.info("Verifying database tables...")
    
    essential_tables = [
        "users",
        "organizations", 
        "roles",
        "permissions",
        "role_permissions",
        "user_roles"
    ]
    
    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            for table in essential_tables:
                result = conn.execute(
                    text("""
                        SELECT 1 FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = :table_name
                    """),
                    {"table_name": table}
                ).fetchone()
                
                if result:
                    logger.info(f"✓ Table '{table}' exists")
                else:
                    logger.error(f"✗ Table '{table}' does not exist")
                    raise Exception(f"Essential table '{table}' not found")
                    
        logger.info("All essential tables verified")
    except Exception as e:
        logger.error(f"Error verifying tables: {e}")
        raise


def main():
    """Main initialization function."""
    logger.info("=== Starting Database Initialization ===")
    
    try:
        # Step 1: Check/create database
        check_database_exists()
        
        # Step 2: Clean up enum types
        clean_enum_types()
        
        # Step 3: Run migrations
        run_migrations()
        
        # Step 4: Verify tables
        verify_tables()
        
        logger.info("=== Database Initialization Complete ===")
        return 0
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())