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
                    for schema_name, _ in result:
                        if schema_name != current_schema:
                            # Drop type from other schemas
                            try:
                                conn.execute(text(f"DROP TYPE IF EXISTS {schema_name}.{type_name} CASCADE"))
                                print(f"Dropped {type_name} from schema: {schema_name}")
                            except Exception as e:
                                print(f"Warning: Could not drop {type_name} from {schema_name}: {e}")
                        else:
                            # Drop from current schema to recreate with correct values
                            try:
                                conn.execute(text(f"DROP TYPE IF EXISTS {type_name} CASCADE"))
                                print(f"Dropped {type_name} from current schema")
                            except Exception as e:
                                print(f"Warning dropping {type_name}: {e}")
        
        print("Enum cleanup completed successfully")
        return True
        
    except Exception as e:
        print(f"Error fixing enums: {e}")
        return False

if __name__ == "__main__":
    success = fix_enums_simple()
    sys.exit(0 if success else 1)