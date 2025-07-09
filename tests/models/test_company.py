"""Tests for Company model."""

import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.company import Company, CompanySize, SubscriptionTier
from models.user import User


class TestCompanyModel:
    """Test cases for Company model."""
    
    async def test_create_company(self, db_session: AsyncSession):
        """Test creating a new company."""
        company = Company(
            name="Test Company",
            domain="testcompany.com",
            size=CompanySize.MEDIUM,
            subscription_tier=SubscriptionTier.PROFESSIONAL,
            max_users=100,
            industry="Technology",
            country="Germany",
            address="Test Street 123",
            city="Berlin",
            postal_code="10115"
        )
        
        db_session.add(company)
        await db_session.commit()
        await db_session.refresh(company)
        
        assert company.id is not None
        assert company.name == "Test Company"
        assert company.domain == "testcompany.com"
        assert company.size == CompanySize.MEDIUM
        assert company.subscription_tier == SubscriptionTier.PROFESSIONAL
        assert company.max_users == 100
        assert company.is_active is True
        assert company.created_at is not None
        assert company.updated_at is not None
    
    async def test_company_unique_domain(self, db_session: AsyncSession):
        """Test that company domain must be unique."""
        company1 = Company(
            name="Company 1",
            domain="unique.com",
            size=CompanySize.SMALL
        )
        db_session.add(company1)
        await db_session.commit()
        
        # Try to create another company with same domain
        company2 = Company(
            name="Company 2",
            domain="unique.com",
            size=CompanySize.LARGE
        )
        db_session.add(company2)
        
        with pytest.raises(Exception):  # Should raise IntegrityError
            await db_session.commit()
    
    async def test_company_user_relationship(self, db_session: AsyncSession):
        """Test company-user relationships."""
        company = Company(
            name="Relationship Test Company",
            domain="relationship.com",
            size=CompanySize.SMALL
        )
        db_session.add(company)
        await db_session.commit()
        await db_session.refresh(company)
        
        # Create users for the company
        user1 = User(
            email="user1@relationship.com",
            username="user1",
            password_hash="hashed123",
            first_name="User One",
            company_id=company.id
        )
        user2 = User(
            email="user2@relationship.com",
            username="user2",
            password_hash="hashed123",
            first_name="User Two",
            company_id=company.id
        )
        
        db_session.add_all([user1, user2])
        await db_session.commit()
        
        # Refresh company to load relationships
        await db_session.refresh(company)
        
        # Query company with users
        result = await db_session.execute(
            select(Company).where(Company.id == company.id)
        )
        company_with_users = result.scalar_one()
        
        # We need to explicitly load the users relationship
        users = await db_session.execute(
            select(User).where(User.company_id == company.id)
        )
        company_users = users.scalars().all()
        
        assert len(company_users) == 2
        assert all(user.company_id == company.id for user in company_users)
    
    async def test_company_soft_delete(self, db_session: AsyncSession):
        """Test soft delete functionality."""
        company = Company(
            name="Delete Test Company",
            domain="deletetest.com",
            size=CompanySize.SMALL
        )
        db_session.add(company)
        await db_session.commit()
        await db_session.refresh(company)
        
        # Soft delete
        company.deleted_at = datetime.utcnow()
        await db_session.commit()
        
        # Company should still exist in database
        result = await db_session.execute(
            select(Company).where(Company.id == company.id)
        )
        deleted_company = result.scalar_one()
        
        assert deleted_company is not None
        assert deleted_company.deleted_at is not None
    
    async def test_company_size_enum(self):
        """Test CompanySize enum values."""
        assert CompanySize.SMALL.value == "small"
        assert CompanySize.MEDIUM.value == "medium"
        assert CompanySize.LARGE.value == "large"
        assert CompanySize.ENTERPRISE.value == "enterprise"
    
    async def test_subscription_tier_enum(self):
        """Test SubscriptionTier enum values."""
        assert SubscriptionTier.FREE.value == "free"
        assert SubscriptionTier.BASIC.value == "basic"
        assert SubscriptionTier.STARTER.value == "starter"
        assert SubscriptionTier.PREMIUM.value == "premium"
        assert SubscriptionTier.PROFESSIONAL.value == "professional"
        assert SubscriptionTier.ENTERPRISE.value == "enterprise"
    
    async def test_company_default_values(self, db_session: AsyncSession):
        """Test default values for company fields."""
        company = Company(
            name="Default Test Company",
            domain="defaults.com"
        )
        db_session.add(company)
        await db_session.commit()
        await db_session.refresh(company)
        
        assert company.size == CompanySize.SMALL  # Default size
        assert company.subscription_tier == SubscriptionTier.FREE  # Default tier
        assert company.max_users == 10  # Default max users
        assert company.is_active is True  # Default active status
        assert company.deleted_at is None  # Not deleted by default
    
    async def test_company_update(self, db_session: AsyncSession):
        """Test updating company fields."""
        company = Company(
            name="Update Test Company",
            domain="updatetest.com",
            size=CompanySize.SMALL
        )
        db_session.add(company)
        await db_session.commit()
        
        original_created_at = company.created_at
        
        # Update company
        company.name = "Updated Company Name"
        company.size = CompanySize.LARGE
        company.subscription_tier = SubscriptionTier.ENTERPRISE
        company.max_users = 1000
        
        await db_session.commit()
        await db_session.refresh(company)
        
        assert company.name == "Updated Company Name"
        assert company.size == CompanySize.LARGE
        assert company.subscription_tier == SubscriptionTier.ENTERPRISE
        assert company.max_users == 1000
        assert company.created_at == original_created_at
        assert company.updated_at > original_created_at  # Updated timestamp should be newer