#!/usr/bin/env python3
"""Prepare database for migrations by ensuring enum types are correct."""

import os
import sys
from sqlalchemy import create_engine, text

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import settings

def safe_drop_enum(engine, enum_name):
    """Safely drop an enum type if it exists."""
    with engine.begin() as conn:
        try:
            # Check if enum exists
            result = conn.execute(
                text("SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname = :name)"),
                {"name": enum_name}
            )
            if result.scalar():
                # Drop the enum cascade (will drop dependent columns too)
                conn.execute(text(f"DROP TYPE IF EXISTS {enum_name} CASCADE"))
                print(f"Dropped enum type: {enum_name}")
        except Exception as e:
            print(f"Warning while dropping {enum_name}: {e}")

def main():
    """Main function to prepare database for migrations."""
    # Convert MultiHostUrl to string and handle postgresql+asyncpg
    database_url = str(settings.DATABASE_URL)
    if database_url.startswith("postgresql+asyncpg://"):
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
    
    engine = create_engine(database_url)
    
    print("Preparing database for migrations...")
    print("This will drop and recreate enum types to ensure consistency.")
    
    # List of enum types to drop
    enum_types = ['userrole', 'companysize', 'subscriptiontier', 'companystatus']
    
    for enum_type in enum_types:
        safe_drop_enum(engine, enum_type)
    
    print("\nDatabase is now ready for migrations!")
    print("Run 'alembic upgrade head' to apply migrations.")

if __name__ == "__main__":
    main()