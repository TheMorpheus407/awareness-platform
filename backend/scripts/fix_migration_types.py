#!/usr/bin/env python3
"""Fix migration issues with existing types in PostgreSQL."""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import settings

def fix_migration_types():
    """Drop and recreate custom types to avoid conflicts."""
    # Convert MultiHostUrl to string and handle postgresql+asyncpg
    database_url = str(settings.DATABASE_URL)
    if database_url.startswith("postgresql+asyncpg://"):
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
    engine = create_engine(database_url)
    
    types_to_recreate = [
        ('companysize', ['small', 'medium', 'large', 'enterprise']),
        ('subscriptiontier', ['free', 'starter', 'professional', 'enterprise']),
        ('userrole', ['system_admin', 'company_admin', 'manager', 'employee']),
        ('companystatus', ['trial', 'active', 'suspended', 'cancelled']),
    ]
    
    with engine.begin() as conn:
        for type_name, values in types_to_recreate:
            try:
                # Try to drop the type
                conn.execute(text(f"DROP TYPE IF EXISTS {type_name} CASCADE"))
                print(f"Dropped type {type_name}")
            except Exception as e:
                print(f"Warning dropping type {type_name}: {e}")
            
            try:
                # Create the type
                values_str = ', '.join([f"'{v}'" for v in values])
                conn.execute(text(f"CREATE TYPE {type_name} AS ENUM ({values_str})"))
                print(f"Created type {type_name}")
            except ProgrammingError as e:
                if "already exists" in str(e):
                    print(f"Type {type_name} already exists, skipping")
                else:
                    raise

if __name__ == "__main__":
    fix_migration_types()
    print("Migration types fixed successfully!")