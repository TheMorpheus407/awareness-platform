#!/bin/bash
# Fix migration files on production server

# Create fixed migration content
cat > /tmp/fix_migrations.sh << 'EOF'
#!/bin/bash

# Fix 001_initial_migration.py
docker exec awareness-backend-1 bash -c "cat > /app/alembic/versions/001_initial_migration.py << 'MIGRATION'
\"\"\"Initial migration with users and companies

Revision ID: 1a2b3c4d5e6f
Revises: 
Create Date: 2025-01-07 16:00:00.000000

\"\"\"
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '1a2b3c4d5e6f'
down_revision = None
branch_labels = None
depends_on = None

$(cat /mnt/e/Projects/AwarenessSchulungen/backend/alembic/versions/001_initial_migration.py | tail -n +18)
MIGRATION"

# Fix 002_add_core_tables.py  
docker exec awareness-backend-1 bash -c "cat > /app/alembic/versions/002_add_core_tables.py << 'MIGRATION'
\"\"\"Add core tables for courses, phishing, and analytics

Revision ID: 2b3c4d5e6f7a
Revises: 1a2b3c4d5e6f
Create Date: 2025-07-07

\"\"\"
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2b3c4d5e6f7a'
down_revision = '1a2b3c4d5e6f'
branch_labels = None
depends_on = None

$(cat /mnt/e/Projects/AwarenessSchulungen/backend/alembic/versions/002_add_core_tables.py | tail -n +18)
MIGRATION"

# Fix 003_add_2fa_support.py
docker exec awareness-backend-1 bash -c "cat > /app/alembic/versions/003_add_2fa_support.py << 'MIGRATION'
\"\"\"Add 2FA support

Revision ID: 3c4d5e6f7a8b
Revises: 2b3c4d5e6f7a
Create Date: 2025-01-07

\"\"\"
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '3c4d5e6f7a8b'
down_revision = '2b3c4d5e6f7a'
branch_labels = None
depends_on = None

$(cat /mnt/e/Projects/AwarenessSchulungen/backend/alembic/versions/003_add_2fa_support.py | tail -n +18)
MIGRATION"

echo "Migration files fixed!"
EOF

# Make it executable
chmod +x /tmp/fix_migrations.sh

# Copy to server and execute
scp -i /tmp/bootstrap-awareness.pem -o StrictHostKeyChecking=no /tmp/fix_migrations.sh ubuntu@bootstrap-awareness.de:/tmp/
ssh -i /tmp/bootstrap-awareness.pem -o StrictHostKeyChecking=no ubuntu@bootstrap-awareness.de "cd /opt/awareness && sudo bash /tmp/fix_migrations.sh"