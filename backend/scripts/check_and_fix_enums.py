#!/usr/bin/env python3
"""Check and fix PostgreSQL enum types in the database."""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import settings

def get_existing_enum_values(engine, enum_name):
    """Get the existing values for an enum type."""
    query = text("""
        SELECT e.enumlabel 
        FROM pg_enum e 
        JOIN pg_type t ON e.enumtypid = t.oid 
        WHERE t.typname = :enum_name
        ORDER BY e.enumsortorder;
    """)
    
    with engine.connect() as conn:
        result = conn.execute(query, {"enum_name": enum_name})
        return [row[0] for row in result]

def check_enum_exists(engine, enum_name):
    """Check if an enum type exists in the database."""
    query = text("""
        SELECT EXISTS (
            SELECT 1 
            FROM pg_type 
            WHERE typname = :enum_name
        );
    """)
    
    with engine.connect() as conn:
        result = conn.execute(query, {"enum_name": enum_name})
        return result.scalar()

def create_or_update_enum(engine, enum_name, values):
    """Create or update an enum type with the given values."""
    if check_enum_exists(engine, enum_name):
        existing_values = get_existing_enum_values(engine, enum_name)
        print(f"Enum '{enum_name}' exists with values: {existing_values}")
        
        # Check if values match
        if set(existing_values) == set(values):
            print(f"Enum '{enum_name}' already has correct values.")
            return
        else:
            print(f"Enum '{enum_name}' has different values. Expected: {values}")
            # In production, you might want to handle this differently
            # For now, we'll drop and recreate
            with engine.begin() as conn:
                try:
                    conn.execute(text(f"DROP TYPE {enum_name} CASCADE"))
                    print(f"Dropped enum '{enum_name}'")
                except Exception as e:
                    print(f"Error dropping enum '{enum_name}': {e}")
                    return
    
    # Create the enum
    values_str = ', '.join([f"'{v}'" for v in values])
    with engine.begin() as conn:
        try:
            conn.execute(text(f"CREATE TYPE {enum_name} AS ENUM ({values_str})"))
            print(f"Created enum '{enum_name}' with values: {values}")
        except ProgrammingError as e:
            if "already exists" in str(e):
                print(f"Enum '{enum_name}' already exists (race condition)")
            else:
                raise

def main():
    """Main function to check and fix all enum types."""
    # Convert MultiHostUrl to string and handle postgresql+asyncpg
    database_url = str(settings.DATABASE_URL)
    if database_url.startswith("postgresql+asyncpg://"):
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
    
    engine = create_engine(database_url)
    
    # Define all enum types and their expected values
    enums = {
        'companysize': ['small', 'medium', 'large', 'enterprise'],
        'subscriptiontier': ['free', 'starter', 'professional', 'enterprise'],
        'userrole': ['system_admin', 'company_admin', 'manager', 'employee'],
        'companystatus': ['trial', 'active', 'suspended', 'cancelled'],
    }
    
    print("Checking and fixing enum types...")
    for enum_name, values in enums.items():
        create_or_update_enum(engine, enum_name, values)
    
    print("\nAll enum types have been checked and fixed!")

if __name__ == "__main__":
    main()