"""Script to create initial Alembic migration."""

import os
os.environ["DATABASE_URL"] = "postgresql://cybersec:changeme@localhost:5432/cybersecurity_platform"
os.environ["SECRET_KEY"] = "test_key_for_migration"
os.environ["FRONTEND_URL"] = "http://localhost:5173"
os.environ["CORS_ORIGINS"] = '["http://localhost:5173"]'

# Now we can import and create the migration
from alembic import command
from alembic.config import Config

# Create Alembic configuration
alembic_cfg = Config("alembic.ini")

# Generate migration
revision_message = "Initial migration with users and companies"
command.revision(alembic_cfg, message=revision_message, autogenerate=True)

print(f"Migration created: {revision_message}")