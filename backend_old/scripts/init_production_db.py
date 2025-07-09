#!/usr/bin/env python3
"""Initialize production database with migrations and admin user."""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from alembic.config import Config
from alembic import command
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from core.config import settings
from core.security import get_password_hash
from db.session import SessionLocal, engine
from models.user import User
from models.company import Company


def run_migrations():
    """Run Alembic migrations."""
    print("Running database migrations...")
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
    print("✓ Migrations completed successfully")


def create_admin_user():
    """Create initial admin user."""
    print("\nCreating admin user...")
    
    db = SessionLocal()
    try:
        # Check if admin exists
        existing_admin = db.query(User).filter(User.email == "admin@bootstrap-awareness.de").first()
        if existing_admin:
            print("✓ Admin user already exists")
            return
        
        # Create admin company first
        admin_company = Company(
            name="Bootstrap Academy GmbH",
            domain="bootstrap-awareness.de",
            is_active=True
        )
        db.add(admin_company)
        db.flush()
        
        # Create admin user
        admin_user = User(
            email="admin@bootstrap-awareness.de",
            hashed_password=get_password_hash("ChangeMeImmediately!"),
            full_name="System Administrator",
            is_active=True,
            is_superuser=True,
            is_verified=True,
            company_id=admin_company.id,
            role="admin"
        )
        db.add(admin_user)
        db.commit()
        
        print("✓ Admin user created successfully")
        print("  Email: admin@bootstrap-awareness.de")
        print("  Password: ChangeMeImmediately!")
        print("  ⚠️  IMPORTANT: Change this password immediately after first login!")
        
    except Exception as e:
        print(f"✗ Error creating admin user: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def setup_row_level_security():
    """Setup PostgreSQL Row Level Security."""
    print("\nSetting up Row Level Security...")
    
    try:
        with engine.connect() as conn:
            # Enable RLS on tables
            tables = ['users', 'companies', 'courses', 'enrollments', 'analytics']
            for table in tables:
                conn.execute(text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY"))
                conn.commit()
            
            print("✓ Row Level Security enabled")
            
    except Exception as e:
        print(f"✗ Error setting up RLS: {e}")
        # Non-critical error, continue


def main():
    """Main initialization function."""
    print("=== Production Database Initialization ===\n")
    
    try:
        # Run migrations
        run_migrations()
        
        # Create admin user
        create_admin_user()
        
        # Setup RLS
        setup_row_level_security()
        
        print("\n✓ Database initialization completed successfully!")
        
    except Exception as e:
        print(f"\n✗ Initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()