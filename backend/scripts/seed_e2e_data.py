#!/usr/bin/env python3
"""Seed database with test data for E2E tests."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.session import async_session_maker
from models.user import User
from models.company import Company
from core.security import get_password_hash
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_test_users(db: AsyncSession):
    """Create test users for E2E tests."""
    test_users = [
        {
            "email": "admin@example.com",
            "password": "AdminPassword123!",
            "first_name": "Admin",
            "last_name": "User",
            "role": "admin",
            "is_active": True,
            "is_verified": True,
        },
        {
            "email": "instructor@example.com",
            "password": "InstructorPassword123!",
            "first_name": "Instructor",
            "last_name": "User",
            "role": "instructor",
            "is_active": True,
            "is_verified": True,
        },
        {
            "email": "user@example.com",
            "password": "UserPassword123!",
            "first_name": "Regular",
            "last_name": "User",
            "role": "user",
            "is_active": True,
            "is_verified": True,
        },
        {
            "email": "inactive@example.com",
            "password": "InactivePassword123!",
            "first_name": "Inactive",
            "last_name": "User",
            "role": "user",
            "is_active": False,
            "is_verified": True,
        },
        {
            "email": "unverified@example.com",
            "password": "UnverifiedPassword123!",
            "first_name": "Unverified",
            "last_name": "User",
            "role": "user",
            "is_active": True,
            "is_verified": False,
        },
    ]
    
    created_users = []
    for user_data in test_users:
        # Check if user exists
        result = await db.execute(
            select(User).where(User.email == user_data["email"])
        )
        existing_user = result.scalar_one_or_none()
        
        if not existing_user:
            password = user_data.pop("password")
            user = User(
                **user_data,
                password_hash=get_password_hash(password)
            )
            db.add(user)
            created_users.append(user)
            logger.info(f"Created test user: {user.email}")
        else:
            logger.info(f"Test user already exists: {existing_user.email}")
            created_users.append(existing_user)
    
    await db.commit()
    return created_users

async def create_test_companies(db: AsyncSession):
    """Create test companies for E2E tests."""
    test_companies = [
        {
            "name": "Test Company Alpha",
            "domain": "test-alpha.com",
            "industry": "Technology",
            "employee_count": 100,
            "is_active": True,
        },
        {
            "name": "Test Company Beta",
            "domain": "test-beta.com",
            "industry": "Healthcare",
            "employee_count": 250,
            "is_active": True,
        },
        {
            "name": "Test Company Gamma",
            "domain": "test-gamma.com",
            "industry": "Finance",
            "employee_count": 500,
            "is_active": True,
        },
        {
            "name": "Inactive Test Company",
            "domain": "test-inactive.com",
            "industry": "Retail",
            "employee_count": 50,
            "is_active": False,
        },
    ]
    
    created_companies = []
    for company_data in test_companies:
        # Check if company exists
        result = await db.execute(
            select(Company).where(Company.domain == company_data["domain"])
        )
        existing_company = result.scalar_one_or_none()
        
        if not existing_company:
            company = Company(**company_data)
            db.add(company)
            created_companies.append(company)
            logger.info(f"Created test company: {company.name}")
        else:
            logger.info(f"Test company already exists: {existing_company.name}")
            created_companies.append(existing_company)
    
    await db.commit()
    return created_companies

async def assign_users_to_companies(db: AsyncSession, users: list[User], companies: list[Company]):
    """Assign some test users to test companies."""
    # Assign regular user to first company
    regular_user = next((u for u in users if u.email == "user@example.com"), None)
    if regular_user and companies:
        regular_user.company_id = companies[0].id
        logger.info(f"Assigned {regular_user.email} to {companies[0].name}")
    
    # Assign instructor to second company
    instructor = next((u for u in users if u.email == "instructor@example.com"), None)
    if instructor and len(companies) > 1:
        instructor.company_id = companies[1].id
        logger.info(f"Assigned {instructor.email} to {companies[1].name}")
    
    await db.commit()

async def main():
    """Main function to seed E2E test data."""
    logger.info("Starting E2E test data seeding...")
    
    async with async_session_maker() as db:
        try:
            # Create test users
            users = await create_test_users(db)
            logger.info(f"Created/verified {len(users)} test users")
            
            # Create test companies
            companies = await create_test_companies(db)
            logger.info(f"Created/verified {len(companies)} test companies")
            
            # Assign users to companies
            await assign_users_to_companies(db, users, companies)
            
            logger.info("E2E test data seeding completed successfully!")
            
        except Exception as e:
            logger.error(f"Error seeding test data: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(main())