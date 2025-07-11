#!/usr/bin/env python3
"""Fix duplicate enum type issue in database."""

import os
import sys
import asyncio
from sqlalchemy import create_engine, text

# Get database URL from environment
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost/awareness_platform")

# Convert async URL to sync for this script
if DATABASE_URL.startswith("postgresql+asyncpg://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

def fix_enums():
    """Drop existing enum types that are causing conflicts."""
    engine = create_engine(DATABASE_URL)
    
    enum_types = [
        "subscriptionstatus",
        "userrole",
        "campaignstatus",
        "emailstatus",
        "phishingstatus",
        "enrollmentstatus"
    ]
    
    with engine.connect() as conn:
        for enum_type in enum_types:
            try:
                # Check if enum exists
                result = conn.execute(
                    text("SELECT 1 FROM pg_type WHERE typname = :name"),
                    {"name": enum_type}
                ).fetchone()
                
                if result:
                    print(f"Dropping existing enum type: {enum_type}")
                    conn.execute(text(f"DROP TYPE IF EXISTS {enum_type} CASCADE"))
                    conn.commit()
            except Exception as e:
                print(f"Error handling enum {enum_type}: {e}")
    
    print("Enum cleanup complete")

if __name__ == "__main__":
    fix_enums()