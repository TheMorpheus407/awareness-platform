#!/usr/bin/env python3
"""Fix migration issues specifically for CI/CD environment."""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError

def fix_enums_simple():
    """Fix enum types using environment variables directly."""
    # Get database URL from environment
    database_url = os.environ.get('DATABASE_URL', '')
    
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        return False
    
    # Convert asyncpg URL to regular postgresql URL for SQLAlchemy
    if database_url.startswith("postgresql+asyncpg://"):
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
    
    try:
        engine = create_engine(database_url)
        
        # Define enum types to handle
        enums_to_drop = [
            'userrole',
            'companysize', 
            'subscriptiontier',
            'companystatus'
        ]
        
        with engine.begin() as conn:
            # Drop existing enums if they exist
            for enum_name in enums_to_drop:
                try:
                    conn.execute(text(f"DROP TYPE IF EXISTS {enum_name} CASCADE"))
                    print(f"Dropped enum: {enum_name}")
                except Exception as e:
                    print(f"Warning dropping {enum_name}: {e}")
        
        print("Enum cleanup completed successfully")
        return True
        
    except Exception as e:
        print(f"Error fixing enums: {e}")
        return False

if __name__ == "__main__":
    success = fix_enums_simple()
    sys.exit(0 if success else 1)