#!/usr/bin/env python3
"""Basic seed data for production"""
import os
import sys
sys.path.insert(0, '/app')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Company, User
from core.security import get_password_hash
import uuid

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def seed_data():
    db = SessionLocal()
    
    try:
        # Check if data already exists
        if db.query(Company).count() > 0:
            print("Data already exists, skipping seed")
            return
        
        # Create demo company
        demo_company = Company(
            id=uuid.uuid4(),
            name="Demo Company",
            domain="demo.com",
            is_active=True,
            employee_count=50,
            industry="Technology"
        )
        db.add(demo_company)
        
        # Create bootstrap company
        bootstrap_company = Company(
            id=uuid.uuid4(),
            name="Bootstrap Academy GmbH",
            domain="bootstrap-academy.com",
            is_active=True,
            employee_count=10,
            industry="Education"
        )
        db.add(bootstrap_company)
        
        # Create admin user
        admin_user = User(
            id=uuid.uuid4(),
            email="admin@bootstrap-awareness.de",
            username="admin",
            full_name="System Administrator",
            hashed_password=get_password_hash("admin123!"),
            is_active=True,
            is_superuser=True,
            company_id=bootstrap_company.id,
            role="system_admin"
        )
        db.add(admin_user)
        
        # Create demo users
        demo_admin = User(
            id=uuid.uuid4(),
            email="admin@demo.com",
            username="demo_admin",
            full_name="Demo Admin",
            hashed_password=get_password_hash("demo123!"),
            is_active=True,
            is_superuser=False,
            company_id=demo_company.id,
            role="company_admin"
        )
        db.add(demo_admin)
        
        demo_user = User(
            id=uuid.uuid4(),
            email="user@demo.com",
            username="demo_user",
            full_name="Demo User",
            hashed_password=get_password_hash("demo123!"),
            is_active=True,
            is_superuser=False,
            company_id=demo_company.id,
            role="user"
        )
        db.add(demo_user)
        
        db.commit()
        print("Seed data created successfully!")
        print("\nLogin credentials:")
        print("System Admin: admin@bootstrap-awareness.de / admin123!")
        print("Demo Admin: admin@demo.com / demo123!")
        print("Demo User: user@demo.com / demo123!")
        
    except Exception as e:
        print(f"Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()