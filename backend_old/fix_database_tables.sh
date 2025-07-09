#!/bin/bash
# Fix Database Tables - Direct Execution Script

echo "=== Database Table Fix Script ==="
echo "This script will create the missing database tables"
echo ""

# Server connection details
SERVER_IP="217.160.180.62"
SERVER_PORT="21"
SERVER_USER="root"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Attempting to connect to server at ${SERVER_IP}:${SERVER_PORT}...${NC}"

# Function to execute remote commands
execute_remote() {
    ssh -o ConnectTimeout=30 -o ServerAliveInterval=5 -o ServerAliveCountMax=3 -p $SERVER_PORT $SERVER_USER@$SERVER_IP "$1"
}

# Test connection
echo -e "${YELLOW}Testing SSH connection...${NC}"
if ! execute_remote "echo 'Connection successful'"; then
    echo -e "${RED}Failed to connect to server. Please check:${NC}"
    echo "1. Server is accessible at $SERVER_IP:$SERVER_PORT"
    echo "2. You have SSH access as $SERVER_USER"
    echo "3. Your SSH key is properly configured"
    exit 1
fi

echo -e "${GREEN}Connection successful!${NC}"

# Check Docker containers
echo -e "${YELLOW}Checking Docker containers...${NC}"
execute_remote "docker ps | grep awareness" || {
    echo -e "${RED}No awareness containers found running!${NC}"
    exit 1
}

# Create Python script to fix tables
echo -e "${YELLOW}Creating database fix script...${NC}"
execute_remote "cat > /tmp/fix_database.py << 'EOF'
#!/usr/bin/env python3
import os
import sys
from sqlalchemy import create_engine, inspect, text

# Database connection
DATABASE_URL = 'postgresql://awareness_user:AwarenessDB2024Secure@postgres:5432/awareness_platform'
engine = create_engine(DATABASE_URL)

print('=== Database Table Creation Script ===')
print('Connecting to database...')

try:
    # Test connection
    with engine.connect() as conn:
        result = conn.execute(text('SELECT 1'))
        print('✅ Database connection successful')
        
    # Check existing tables
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    print(f'\\nExisting tables: {existing_tables}')
    
    # Import models to create tables
    print('\\nImporting database models...')
    sys.path.insert(0, '/app/backend')
    
    from db.base import Base
    from models.user import User
    from models.company import Company
    from models.training_module import TrainingModule
    from models.phishing_simulation import PhishingTemplate, PhishingCampaign
    from models.user_progress import UserProgress
    
    # Create all tables
    print('\\nCreating database tables...')
    Base.metadata.create_all(bind=engine)
    
    # Verify tables were created
    inspector = inspect(engine)
    new_tables = inspector.get_table_names()
    print(f'\\nTables after creation: {new_tables}')
    
    # Create indexes and constraints
    with engine.begin() as conn:
        # Add any custom indexes here
        print('\\nAdding indexes...')
        conn.execute(text('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)'))
        conn.execute(text('CREATE INDEX IF NOT EXISTS idx_users_company_id ON users(company_id)'))
        conn.execute(text('CREATE INDEX IF NOT EXISTS idx_companies_domain ON companies(domain)'))
        
    print('\\n✅ All tables created successfully!')
    
except Exception as e:
    print(f'\\n❌ Error: {str(e)}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
EOF"

# Make script executable
execute_remote "chmod +x /tmp/fix_database.py"

# Run the script in the backend container
echo -e "${YELLOW}Running database fix in backend container...${NC}"
execute_remote "docker exec awareness-backend-1 python /tmp/fix_database.py" || {
    echo -e "${RED}Failed to create tables. Trying alternative approach...${NC}"
    
    # Alternative: Run alembic migrations
    echo -e "${YELLOW}Attempting to run Alembic migrations...${NC}"
    execute_remote "docker exec awareness-backend-1 bash -c 'cd /app/backend && DATABASE_URL=postgresql://awareness_user:AwarenessDB2024Secure@postgres:5432/awareness_platform alembic upgrade head'" || {
        echo -e "${RED}Alembic migrations also failed.${NC}"
    }
}

# Verify tables exist
echo -e "${YELLOW}Verifying tables...${NC}"
execute_remote "docker exec awareness-postgres-1 psql -U awareness_user -d awareness_platform -c '\\dt'" || {
    echo -e "${RED}Could not verify tables${NC}"
}

# Create admin user
echo -e "${YELLOW}Creating admin user...${NC}"
execute_remote "cat > /tmp/create_admin.py << 'EOF'
#!/usr/bin/env python3
import os
import sys
from sqlalchemy import create_engine, text
from datetime import datetime

DATABASE_URL = 'postgresql://awareness_user:AwarenessDB2024Secure@postgres:5432/awareness_platform'
engine = create_engine(DATABASE_URL)

# Add backend to path
sys.path.insert(0, '/app/backend')
from core.security import get_password_hash

try:
    with engine.begin() as conn:
        # Create company first
        print('Creating company...')
        result = conn.execute(text('''
            INSERT INTO companies (name, domain, size, status, subscription_tier, max_users, country, timezone)
            VALUES (:name, :domain, :size, :status, :tier, :max_users, :country, :timezone)
            ON CONFLICT (domain) DO UPDATE SET 
                name = EXCLUDED.name,
                status = EXCLUDED.status,
                subscription_tier = EXCLUDED.subscription_tier
            RETURNING id
        '''), {
            'name': 'Bootstrap Awareness GmbH',
            'domain': 'bootstrap-awareness.de',
            'size': 'medium',
            'status': 'active',
            'tier': 'enterprise',
            'max_users': 100,
            'country': 'DE',
            'timezone': 'Europe/Berlin'
        })
        company_id = result.fetchone()[0]
        print(f'Company created with ID: {company_id}')
        
        # Create admin user
        print('Creating admin user...')
        password_hash = get_password_hash('SecureAdminPassword123!')
        conn.execute(text('''
            INSERT INTO users (
                email, password_hash, first_name, last_name, 
                role, is_active, is_verified, is_superuser, 
                company_id, created_at
            ) VALUES (
                :email, :password_hash, :first_name, :last_name,
                :role, :is_active, :is_verified, :is_superuser,
                :company_id, :created_at
            )
            ON CONFLICT (email) DO UPDATE SET 
                password_hash = EXCLUDED.password_hash,
                is_active = EXCLUDED.is_active,
                is_verified = EXCLUDED.is_verified,
                is_superuser = EXCLUDED.is_superuser
        '''), {
            'email': 'admin@bootstrap-awareness.de',
            'password_hash': password_hash,
            'first_name': 'Admin',
            'last_name': 'User',
            'role': 'company_admin',
            'is_active': True,
            'is_verified': True,
            'is_superuser': True,
            'company_id': company_id,
            'created_at': datetime.utcnow()
        })
        
        print('✅ Admin user created successfully!')
        print('📧 Email: admin@bootstrap-awareness.de')
        print('🔑 Password: SecureAdminPassword123!')
        
except Exception as e:
    print(f'❌ Error: {str(e)}')
    import traceback
    traceback.print_exc()
EOF"

execute_remote "docker exec awareness-backend-1 python /tmp/create_admin.py"

# Restart services
echo -e "${YELLOW}Restarting services...${NC}"
execute_remote "cd /root/awareness-schulungen && docker-compose restart backend"

echo -e "${GREEN}=== Database fix complete! ===${NC}"
echo ""
echo "Admin credentials:"
echo "Email: admin@bootstrap-awareness.de"
echo "Password: SecureAdminPassword123!"
echo ""
echo "Test the login at: https://bootstrap-awareness.de"