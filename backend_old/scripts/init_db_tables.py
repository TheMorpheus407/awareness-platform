#!/usr/bin/env python3
"""Initialize database tables directly."""
import os
import sys

# Set database URL
os.environ['DATABASE_URL'] = 'postgresql://awareness_user:AwarenessDB2024Secure@postgres:5432/awareness_platform'

from sqlalchemy import create_engine
from db.base import Base
from core.security import get_password_hash

# Create engine without async
engine = create_engine(os.environ['DATABASE_URL'])

print("Creating all database tables...")
Base.metadata.create_all(bind=engine)
print("Tables created successfully!")

# Create initial data
from sqlalchemy.orm import Session
from models.company import Company
from models.user import User

with Session(engine) as session:
    # Check if company exists
    company = session.query(Company).filter_by(domain='bootstrap-awareness.de').first()
    if not company:
        company = Company(
            name='Bootstrap Awareness GmbH',
            domain='bootstrap-awareness.de',
            size='medium',
            status='active',
            subscription_tier='enterprise',
            max_users=100,
            country='DE',
            timezone='Europe/Berlin'
        )
        session.add(company)
        session.commit()
        print(f"Created company: {company.name}")
    
    # Check if admin exists
    admin = session.query(User).filter_by(email='admin@bootstrap-awareness.de').first()
    if not admin:
        admin = User(
            email='admin@bootstrap-awareness.de',
            password_hash=get_password_hash('SecureAdminPassword123!'),
            first_name='Admin',
            last_name='User',
            role='company_admin',
            is_active=True,
            is_verified=True,
            is_superuser=True,
            company_id=company.id
        )
        session.add(admin)
        session.commit()
        print(f"Created admin user: {admin.email}")
    
    print("\nSetup complete!")
    print("Admin login: admin@bootstrap-awareness.de / SecureAdminPassword123!")