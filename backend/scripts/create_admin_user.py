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