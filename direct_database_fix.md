# Direct Database Fix Commands

Run these commands directly on your server where Docker is running:

## 1. Connect to your server
```bash
ssh -p 21 root@217.160.180.62
# or if port 21 doesn't work:
ssh root@217.160.180.62
```

## 2. Navigate to the project directory
```bash
cd /root/awareness-schulungen
# or find the correct directory with:
find / -name "docker-compose.yml" -path "*/awareness*" 2>/dev/null
```

## 3. Check container status
```bash
docker ps | grep awareness
# or
docker-compose ps
```

## 4. Create database tables manually

### Option A: Using Python in the container
```bash
# Enter the backend container
docker exec -it awareness-backend-1 bash

# Inside the container, run Python
python3

# Paste this Python code:
import os
os.environ['DATABASE_URL'] = 'postgresql://awareness_user:AwarenessDB2024Secure@postgres:5432/awareness_platform'

from sqlalchemy import create_engine
from db.base import Base

engine = create_engine(os.environ['DATABASE_URL'])
Base.metadata.create_all(bind=engine)
print("Tables created!")
exit()

# Exit the container
exit
```

### Option B: Using Alembic migrations
```bash
# Run migrations with explicit database URL
docker exec awareness-backend-1 bash -c "DATABASE_URL=postgresql://awareness_user:AwarenessDB2024Secure@postgres:5432/awareness_platform alembic upgrade head"
```

### Option C: Direct SQL creation
```bash
# Connect to postgres container
docker exec -it awareness-postgres-1 psql -U awareness_user -d awareness_platform

# Run these SQL commands to create the tables:
```

```sql
-- Create companies table
CREATE TABLE IF NOT EXISTS companies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(255) UNIQUE NOT NULL,
    size VARCHAR(50),
    status VARCHAR(50) DEFAULT 'active',
    subscription_tier VARCHAR(50) DEFAULT 'basic',
    max_users INTEGER DEFAULT 10,
    country VARCHAR(2),
    timezone VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    role VARCHAR(50) DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    is_superuser BOOLEAN DEFAULT false,
    company_id INTEGER REFERENCES companies(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create other necessary tables
CREATE TABLE IF NOT EXISTS training_modules (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    difficulty_level VARCHAR(50),
    duration_minutes INTEGER,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_progress (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    module_id INTEGER REFERENCES training_modules(id),
    status VARCHAR(50),
    score INTEGER,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS phishing_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    subject VARCHAR(255),
    body TEXT,
    difficulty_level VARCHAR(50),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS phishing_campaigns (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    company_id INTEGER REFERENCES companies(id),
    template_id INTEGER REFERENCES phishing_templates(id),
    status VARCHAR(50),
    scheduled_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_company_id ON users(company_id);
CREATE INDEX idx_companies_domain ON companies(domain);

-- Exit psql
\q
```

## 5. Create the admin user

```bash
# Save this as create_admin.py on the server
cat > /tmp/create_admin.py << 'EOF'
import os
os.environ['DATABASE_URL'] = 'postgresql://awareness_user:AwarenessDB2024Secure@postgres:5432/awareness_platform'

from sqlalchemy import create_engine, text
from core.security import get_password_hash

engine = create_engine(os.environ['DATABASE_URL'])

with engine.begin() as conn:
    # Create company
    conn.execute(text("""
        INSERT INTO companies (name, domain, size, status, subscription_tier, max_users)
        VALUES ('Bootstrap Awareness GmbH', 'bootstrap-awareness.de', 'medium', 'active', 'enterprise', 100)
        ON CONFLICT (domain) DO NOTHING
    """))
    
    # Get company ID
    result = conn.execute(text("SELECT id FROM companies WHERE domain = 'bootstrap-awareness.de'")).fetchone()
    company_id = result[0]
    
    # Create admin user
    password_hash = get_password_hash("SecureAdminPassword123!")
    conn.execute(text("""
        INSERT INTO users (email, password_hash, first_name, last_name, role, is_active, is_verified, is_superuser, company_id)
        VALUES ('admin@bootstrap-awareness.de', :pwd, 'Admin', 'User', 'company_admin', true, true, true, :cid)
        ON CONFLICT (email) DO UPDATE SET password_hash = :pwd, is_active = true, is_verified = true, is_superuser = true
    """), {"pwd": password_hash, "cid": company_id})

print("Admin user created!")
EOF

# Run it
docker exec awareness-backend-1 python /tmp/create_admin.py
```

## 6. Restart the backend
```bash
docker-compose restart backend
# or
docker restart awareness-backend-1
```

## 7. Test the login
```bash
# From the server
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@bootstrap-awareness.de&password=SecureAdminPassword123!"

# Or test from your local machine
curl -X POST https://bootstrap-awareness.de/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@bootstrap-awareness.de&password=SecureAdminPassword123!"
```

## Admin Credentials
- **Email**: admin@bootstrap-awareness.de
- **Password**: SecureAdminPassword123!

## Troubleshooting

If tables still don't exist:
1. Check backend logs: `docker logs awareness-backend-1`
2. Check postgres logs: `docker logs awareness-postgres-1`
3. Verify database connection: `docker exec awareness-backend-1 python -c "import os; print(os.environ.get('DATABASE_URL'))"`
4. Check if alembic is installed: `docker exec awareness-backend-1 pip list | grep alembic`