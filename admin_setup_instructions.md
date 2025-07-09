# Admin User Setup Instructions

Since we cannot directly access the Docker container from this WSL environment, you'll need to run these commands on your server where the Docker containers are running.

## Step 1: Connect to your server

```bash
ssh your-server
cd /root/awareness-schulungen  # or wherever your docker-compose.yml is located
```

## Step 2: Create the admin user

Save this Python script as `create_admin.py` on your server:

```python
#!/usr/bin/env python3
import os
import sys

# Set the database URL
os.environ['DATABASE_URL'] = 'postgresql://awareness_user:AwarenessDB2024Secure@postgres:5432/awareness_platform'

# Add the backend directory to Python path
sys.path.insert(0, '/app/backend')

from sqlalchemy import create_engine, text
from core.security import get_password_hash

# Create database connection
engine = create_engine(os.environ['DATABASE_URL'].replace('+asyncpg', ''))

try:
    with engine.begin() as conn:
        # Create company
        print("Creating company...")
        conn.execute(text("""
            INSERT INTO companies (name, domain, size, status, subscription_tier, max_users, country, timezone)
            VALUES ('Bootstrap Awareness GmbH', 'bootstrap-awareness.de', 'medium', 'active', 'enterprise', 100, 'DE', 'Europe/Berlin')
            ON CONFLICT (domain) DO UPDATE SET 
                name = 'Bootstrap Awareness GmbH',
                size = 'medium',
                status = 'active',
                subscription_tier = 'enterprise',
                max_users = 100,
                country = 'DE',
                timezone = 'Europe/Berlin'
            RETURNING id
        """))
        
        # Get company ID
        result = conn.execute(text("SELECT id FROM companies WHERE domain = 'bootstrap-awareness.de'")).fetchone()
        if result:
            company_id = result[0]
            print(f"Company created/updated with ID: {company_id}")
        else:
            raise Exception("Failed to create/retrieve company")
        
        # Create admin user
        print("Creating admin user...")
        password_hash = get_password_hash("SecureAdminPassword123!")
        conn.execute(text("""
            INSERT INTO users (email, password_hash, first_name, last_name, role, is_active, is_verified, is_superuser, company_id)
            VALUES ('admin@bootstrap-awareness.de', :password_hash, 'Admin', 'User', 'company_admin', true, true, true, :company_id)
            ON CONFLICT (email) DO UPDATE SET 
                password_hash = :password_hash, 
                is_active = true, 
                is_verified = true,
                is_superuser = true,
                role = 'company_admin',
                company_id = :company_id
        """), {"password_hash": password_hash, "company_id": company_id})
        
        print("✅ Admin user created/updated successfully!")
        print("📧 Email: admin@bootstrap-awareness.de")
        print("🔑 Password: SecureAdminPassword123!")
        
except Exception as e:
    print(f"❌ Error: {str(e)}")
    sys.exit(1)
```

## Step 3: Run the script in the backend container

```bash
# Copy the script to the container
docker cp create_admin.py awareness-backend:/tmp/create_admin.py

# Execute it
docker exec awareness-backend python /tmp/create_admin.py
```

## Step 4: Check backend logs for errors

If the login is still failing, check the logs:

```bash
docker logs awareness-backend --tail 50
```

## Step 5: Test the login

Once the admin is created, test the login from your local machine:

```bash
curl -X POST https://bootstrap-awareness.de/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@bootstrap-awareness.de&password=SecureAdminPassword123!"
```

## Alternative: Direct Database Access

If the Python script fails, you can create the admin directly in the database:

```bash
# Connect to the postgres container
docker exec -it awareness-postgres psql -U awareness_user -d awareness_platform

# Run these SQL commands:
-- Create company
INSERT INTO companies (name, domain, size, status, subscription_tier, max_users, country, timezone)
VALUES ('Bootstrap Awareness GmbH', 'bootstrap-awareness.de', 'medium', 'active', 'enterprise', 100, 'DE', 'Europe/Berlin')
ON CONFLICT (domain) DO UPDATE SET 
    name = 'Bootstrap Awareness GmbH',
    size = 'medium',
    status = 'active',
    subscription_tier = 'enterprise',
    max_users = 100,
    country = 'DE',
    timezone = 'Europe/Berlin';

-- Get company ID
SELECT id FROM companies WHERE domain = 'bootstrap-awareness.de';

-- Create admin (replace COMPANY_ID with the actual ID from above)
-- Password hash for "SecureAdminPassword123!" (bcrypt)
INSERT INTO users (email, password_hash, first_name, last_name, role, is_active, is_verified, is_superuser, company_id)
VALUES (
    'admin@bootstrap-awareness.de', 
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiLXCJpJ/XJm',
    'Admin', 
    'User', 
    'company_admin', 
    true, 
    true, 
    true, 
    COMPANY_ID
)
ON CONFLICT (email) DO UPDATE SET 
    password_hash = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiLXCJpJ/XJm',
    is_active = true,
    is_verified = true,
    is_superuser = true,
    role = 'company_admin';
```

## Troubleshooting

If you're still having issues:

1. Check that all migrations have run:
   ```bash
   docker exec awareness-backend alembic upgrade head
   ```

2. Verify the database schema:
   ```bash
   docker exec -it awareness-postgres psql -U awareness_user -d awareness_platform -c "\dt"
   ```

3. Check for any error details in the backend logs:
   ```bash
   docker logs awareness-backend --tail 100 | grep -i error
   ```

## Admin Credentials

Once successfully created:
- **Email**: admin@bootstrap-awareness.de
- **Password**: SecureAdminPassword123!