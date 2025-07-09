#!/usr/bin/env python3
"""Create admin user for production - simplified version."""

import os
import sys
from datetime import datetime

# Force production database URL
os.environ['DATABASE_URL'] = 'postgresql://awareness_user:AwarenessDB2024Secure@postgres:5432/awareness_platform'

from sqlalchemy import create_engine, text
from core.security import get_password_hash

def main():
    """Create admin user."""
    print("Creating admin user for production...")
    
    # Use sync engine for simplicity
    engine = create_engine(os.environ['DATABASE_URL'].replace('+asyncpg', ''))
    
    with engine.begin() as conn:
        # Check/create company
        result = conn.execute(text(
            "SELECT id FROM companies WHERE domain = 'bootstrap-awareness.de'"
        )).fetchone()
        
        if not result:
            conn.execute(text("""
                INSERT INTO companies (
                    name, domain, size, status, subscription_tier, 
                    max_users, country, timezone, created_at, updated_at
                ) VALUES (
                    'Bootstrap Awareness GmbH', 'bootstrap-awareness.de', 
                    'medium', 'active', 'enterprise', 
                    100, 'DE', 'Europe/Berlin', NOW(), NOW()
                )
            """))
            result = conn.execute(text(
                "SELECT id FROM companies WHERE domain = 'bootstrap-awareness.de'"
            )).fetchone()
        
        company_id = result[0]
        print(f"Company ID: {company_id}")
        
        # Create/update admin
        password_hash = get_password_hash("SecureAdminPassword123!")
        
        # Check if admin exists
        admin_result = conn.execute(text(
            "SELECT id FROM users WHERE email = 'admin@bootstrap-awareness.de'"
        )).fetchone()
        
        if admin_result:
            # Update existing
            conn.execute(text("""
                UPDATE users SET 
                    password_hash = :password_hash,
                    is_active = true,
                    is_verified = true,
                    is_superuser = true,
                    role = 'company_admin',
                    company_id = :company_id,
                    updated_at = NOW()
                WHERE email = 'admin@bootstrap-awareness.de'
            """), {"password_hash": password_hash, "company_id": company_id})
            print("Admin user updated!")
        else:
            # Create new
            conn.execute(text("""
                INSERT INTO users (
                    email, password_hash, first_name, last_name,
                    role, is_active, is_verified, is_superuser,
                    company_id, created_at, updated_at, password_changed_at
                ) VALUES (
                    'admin@bootstrap-awareness.de', :password_hash, 
                    'Admin', 'User', 'company_admin', true, true, true,
                    :company_id, NOW(), NOW(), NOW()
                )
            """), {"password_hash": password_hash, "company_id": company_id})
            print("Admin user created!")
        
        print("\nSuccess! Login credentials:")
        print("Email: admin@bootstrap-awareness.de")
        print("Password: SecureAdminPassword123!")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)