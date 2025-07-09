#!/usr/bin/env python3
"""Run database migrations synchronously"""
import os
import sys
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://awareness:awareness@postgres:5432/awareness_platform")

# Create Alembic configuration
config = Config("alembic.ini")
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Run migrations
print(f"Running migrations on {DATABASE_URL}")
try:
    command.upgrade(config, "head")
    print("Migrations completed successfully!")
except Exception as e:
    print(f"Migration error: {e}")
    sys.exit(1)