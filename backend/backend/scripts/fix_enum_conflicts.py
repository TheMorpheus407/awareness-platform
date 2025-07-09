#!/usr/bin/env python3
"""Fix enum type conflicts before running migrations."""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import settings

def fix_enum_conflicts():
    """Fix enum type conflicts by ensuring they exist in the correct schema."""
    # Convert MultiHostUrl to string and handle postgresql+asyncpg
    database_url = str(settings.DATABASE_URL)
    if database_url.startswith("postgresql+asyncpg://"):
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
    
    engine = create_engine(database_url)
    
    enum_definitions = {
        'companysize': ['small', 'medium', 'large', 'enterprise'],
        'subscriptiontier': ['free', 'starter', 'professional', 'enterprise'],
        'userrole': ['system_admin', 'company_admin', 'manager', 'employee'],
        'companystatus': ['trial', 'active', 'suspended', 'cancelled']
    }
    
    with engine.begin() as conn:
        # Get current schema
        current_schema = conn.execute(text("SELECT current_schema()")).scalar()
        print(f"Current schema: {current_schema}")
        
        for type_name, values in enum_definitions.items():
            print(f"\nProcessing enum type: {type_name}")
            
            # Check if type exists in any schema
            result = conn.execute(
                text(f"""
                    SELECT n.nspname, t.typname 
                    FROM pg_type t 
                    JOIN pg_namespace n ON t.typnamespace = n.oid 
                    WHERE t.typname = '{type_name}'
                """)
            ).fetchall()
            
            if result:
                print(f"  Found {len(result)} instance(s) of {type_name}")
                for schema_name, _ in result:
                    print(f"  - In schema: {schema_name}")
                    if schema_name != current_schema:
                        # Drop type from other schemas
                        try:
                            conn.execute(text(f"DROP TYPE IF EXISTS {schema_name}.{type_name} CASCADE"))
                            print(f"  - Dropped from schema: {schema_name}")
                        except Exception as e:
                            print(f"  - Warning: Could not drop from {schema_name}: {e}")
            
            # Always try to ensure the type exists in current schema
            try:
                # First try to create
                values_str = ', '.join([f"'{v}'" for v in values])
                conn.execute(text(f"CREATE TYPE {type_name} AS ENUM ({values_str})"))
                print(f"  ✓ Created {type_name} in current schema")
            except ProgrammingError as e:
                if "already exists" in str(e):
                    print(f"  ✓ {type_name} already exists in current schema")
                    # Optionally verify the values match
                    try:
                        enum_values = conn.execute(
                            text(f"""
                                SELECT e.enumlabel 
                                FROM pg_enum e 
                                JOIN pg_type t ON e.enumtypid = t.oid 
                                WHERE t.typname = '{type_name}'
                                ORDER BY e.enumsortorder
                            """)
                        ).fetchall()
                        existing_values = [row[0] for row in enum_values]
                        if existing_values != values:
                            print(f"  ! Warning: Existing values {existing_values} != expected {values}")
                    except Exception:
                        pass
                else:
                    raise

def check_tables():
    """Check if tables already exist."""
    database_url = str(settings.DATABASE_URL)
    if database_url.startswith("postgresql+asyncpg://"):
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
    
    engine = create_engine(database_url)
    
    with engine.begin() as conn:
        # Check for existing tables
        tables = conn.execute(
            text("""
                SELECT tablename 
                FROM pg_tables 
                WHERE schemaname = current_schema() 
                AND tablename IN ('companies', 'users')
            """)
        ).fetchall()
        
        if tables:
            print("\nExisting tables found:")
            for table in tables:
                print(f"  - {table[0]}")
            return True
        else:
            print("\nNo existing tables found.")
            return False

if __name__ == "__main__":
    print("Fixing enum type conflicts...")
    fix_enum_conflicts()
    
    print("\n" + "="*50)
    tables_exist = check_tables()
    
    if tables_exist:
        print("\n⚠️  WARNING: Tables already exist. You may need to:")
        print("  1. Drop existing tables: alembic downgrade base")
        print("  2. Or stamp the current revision: alembic stamp head")
    
    print("\n✅ Enum conflicts fixed. You can now run migrations.")