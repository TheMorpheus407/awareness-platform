#!/bin/bash
# Manual fix for production

echo "Manual Production Fix"
echo "===================="

# Create a simple Python script to add admin
cat > /tmp/fix_admin.py << 'EOF'
import psycopg2
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Connect to database
conn = psycopg2.connect(
    host="localhost",
    database="awareness_platform",
    user="awareness_user",
    password="AwarenessDB2024Secure"
)
cur = conn.cursor()

# Get or create company
cur.execute("SELECT id FROM companies WHERE domain = 'bootstrap-awareness.de'")
company = cur.fetchone()

if not company:
    cur.execute("""
        INSERT INTO companies (name, domain, size, status, subscription_tier, max_users, country, timezone, created_at, updated_at)
        VALUES ('Bootstrap Awareness GmbH', 'bootstrap-awareness.de', 'medium', 'active', 'enterprise', 100, 'DE', 'Europe/Berlin', NOW(), NOW())
        RETURNING id
    """)
    company = cur.fetchone()
    conn.commit()

company_id = company[0]

# Create/update admin
password_hash = pwd_context.hash("admin")
cur.execute("SELECT id FROM users WHERE email = 'admin@bootstrap-awareness.de'")
admin = cur.fetchone()

if admin:
    cur.execute("""
        UPDATE users SET 
            password_hash = %s,
            is_active = true,
            is_verified = true,
            is_superuser = true,
            role = 'company_admin',
            company_id = %s
        WHERE email = 'admin@bootstrap-awareness.de'
    """, (password_hash, company_id))
else:
    cur.execute("""
        INSERT INTO users (
            email, password_hash, first_name, last_name,
            role, is_active, is_verified, is_superuser,
            company_id, created_at, updated_at, password_changed_at
        ) VALUES (
            'admin@bootstrap-awareness.de', %s, 'Admin', 'User',
            'company_admin', true, true, true,
            %s, NOW(), NOW(), NOW()
        )
    """, (password_hash, company_id))

conn.commit()
cur.close()
conn.close()
print("Admin user ready! Login: admin@bootstrap-awareness.de / admin")
EOF

echo "Running fix on server..."
# Note: This would need proper SSH setup
# ssh ubuntu@83.228.205.20 "sudo docker cp /tmp/fix_admin.py awareness-backend-1:/tmp/ && sudo docker exec awareness-backend-1 python /tmp/fix_admin.py"

echo "Testing login..."
curl -X POST https://bootstrap-awareness.de/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@bootstrap-awareness.de&password=admin" \
  -s | python3 -m json.tool