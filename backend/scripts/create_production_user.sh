#!/bin/bash
# Create admin user directly on production server

echo "Creating admin user on production server..."

# Create Python script on server
cat << 'PYTHON_SCRIPT' > /tmp/create_admin.py
import asyncio
import sys
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

DATABASE_URL = "postgresql+asyncpg://awareness_user:AwarenessDB2024Secure@localhost:5432/awareness_platform"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_admin():
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        # First, get or create company
        result = await db.execute(
            "SELECT id FROM companies WHERE domain = 'bootstrap-awareness.de'"
        )
        company = result.fetchone()
        
        if not company:
            # Create company
            await db.execute("""
                INSERT INTO companies (name, domain, size, status, subscription_tier, max_users, country, timezone, created_at, updated_at)
                VALUES ('Bootstrap Awareness GmbH', 'bootstrap-awareness.de', 'medium', 'active', 'enterprise', 100, 'DE', 'Europe/Berlin', NOW(), NOW())
                RETURNING id
            """)
            await db.commit()
            result = await db.execute(
                "SELECT id FROM companies WHERE domain = 'bootstrap-awareness.de'"
            )
            company = result.fetchone()
        
        company_id = company[0]
        
        # Create admin user
        password_hash = pwd_context.hash("SecureAdminPassword123!")
        
        # Check if admin exists
        result = await db.execute(
            "SELECT id FROM users WHERE email = 'admin@bootstrap-awareness.de'"
        )
        admin = result.fetchone()
        
        if admin:
            # Update password
            await db.execute(f"""
                UPDATE users 
                SET password_hash = '{password_hash}', 
                    is_active = true, 
                    is_verified = true,
                    is_superuser = true,
                    role = 'company_admin'
                WHERE email = 'admin@bootstrap-awareness.de'
            """)
            print("Admin user updated successfully!")
        else:
            # Create admin
            await db.execute(f"""
                INSERT INTO users (
                    email, password_hash, first_name, last_name, 
                    role, is_active, is_verified, is_superuser, 
                    company_id, created_at, updated_at, password_changed_at
                ) VALUES (
                    'admin@bootstrap-awareness.de', '{password_hash}', 'Admin', 'User',
                    'company_admin', true, true, true,
                    '{company_id}', NOW(), NOW(), NOW()
                )
            """)
            print("Admin user created successfully!")
        
        await db.commit()
        print("Done! You can login with: admin@bootstrap-awareness.de / SecureAdminPassword123!")

asyncio.run(create_admin())
PYTHON_SCRIPT

# Copy and run on server
scp /tmp/create_admin.py ubuntu@83.228.205.20:/tmp/
ssh ubuntu@83.228.205.20 "cd /opt/awareness && sudo docker exec awareness-backend-1 python /tmp/create_admin.py"