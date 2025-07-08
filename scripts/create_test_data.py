#!/usr/bin/env python3
"""Create test data for production testing."""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.security import get_password_hash
from db.session import async_session_maker
from models.company import Company, CompanySize, CompanyStatus, SubscriptionTier
from models.user import User, UserRole


async def create_test_company(db: AsyncSession) -> Company:
    """Create a test company."""
    # Check if test company exists
    result = await db.execute(
        select(Company).where(Company.domain == "bootstrap-awareness.de")
    )
    company = result.scalar_one_or_none()
    
    if not company:
        company = Company(
            name="Bootstrap Awareness GmbH",
            domain="bootstrap-awareness.de",
            size=CompanySize.MEDIUM,
            status=CompanyStatus.ACTIVE,
            subscription_tier=SubscriptionTier.ENTERPRISE,
            max_users=100,
            industry="Cybersecurity",
            country="DE",
            timezone="Europe/Berlin",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(company)
        await db.commit()
        await db.refresh(company)
        print(f"✓ Created company: {company.name}")
    else:
        print(f"✓ Company already exists: {company.name}")
    
    return company


async def create_admin_user(db: AsyncSession, company: Company) -> User:
    """Create an admin user."""
    # Check if admin exists
    result = await db.execute(
        select(User).where(User.email == "admin@bootstrap-awareness.de")
    )
    admin = result.scalar_one_or_none()
    
    if not admin:
        admin = User(
            email="admin@bootstrap-awareness.de",
            password_hash=get_password_hash("SecureAdminPassword123!"),
            first_name="Admin",
            last_name="User",
            role=UserRole.COMPANY_ADMIN,
            is_active=True,
            is_verified=True,
            is_superuser=True,
            company_id=company.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            password_changed_at=datetime.utcnow()
        )
        db.add(admin)
        await db.commit()
        await db.refresh(admin)
        print(f"✓ Created admin user: {admin.email}")
    else:
        # Update password
        admin.password_hash = get_password_hash("SecureAdminPassword123!")
        admin.is_active = True
        admin.is_verified = True
        await db.commit()
        print(f"✓ Admin user already exists, password updated: {admin.email}")
    
    return admin


async def create_test_user(db: AsyncSession, company: Company) -> User:
    """Create a test employee user."""
    # Check if test user exists
    result = await db.execute(
        select(User).where(User.email == "test@bootstrap-awareness.de")
    )
    user = result.scalar_one_or_none()
    
    if not user:
        user = User(
            email="test@bootstrap-awareness.de",
            password_hash=get_password_hash("TestPassword123!"),
            first_name="Test",
            last_name="Employee",
            role=UserRole.EMPLOYEE,
            is_active=True,
            is_verified=True,
            company_id=company.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            password_changed_at=datetime.utcnow()
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        print(f"✓ Created test user: {user.email}")
    else:
        print(f"✓ Test user already exists: {user.email}")
    
    return user


async def main():
    """Create test data."""
    print("Creating test data for Bootstrap Awareness Platform...")
    print("=" * 60)
    
    async with async_session_maker() as db:
        try:
            # Create test company
            company = await create_test_company(db)
            
            # Create users
            admin = await create_admin_user(db, company)
            user = await create_test_user(db, company)
            
            print("=" * 60)
            print("Test data created successfully!")
            print("\nYou can now login with:")
            print(f"  Admin: admin@bootstrap-awareness.de / SecureAdminPassword123!")
            print(f"  User: test@bootstrap-awareness.de / TestPassword123!")
            
        except Exception as e:
            print(f"Error creating test data: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(main())