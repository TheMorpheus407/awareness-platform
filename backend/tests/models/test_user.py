"""Tests for User model."""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.user import User, UserRole
from models.company import Company, CompanySize


class TestUserModel:
    """Test cases for User model."""
    
    async def test_create_user(self, db_session: AsyncSession):
        """Test creating a new user."""
        user = User(
            email="test@example.com",
            username="testuser",
            password_hash="hashed_password_123",
            full_name="Test User",
            phone_number="+491234567890",
            department="IT",
            job_title="Developer",
            language="de",
            timezone="Europe/Berlin"
        )
        
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.full_name == "Test User"
        assert user.role == UserRole.USER  # Default role
        assert user.is_active is True
        assert user.is_verified is False
        assert user.created_at is not None
        assert user.updated_at is not None
    
    async def test_user_unique_email(self, db_session: AsyncSession):
        """Test that user email must be unique."""
        user1 = User(
            email="unique@example.com",
            username="user1",
            password_hash="hashed123"
        )
        db_session.add(user1)
        await db_session.commit()
        
        # Try to create another user with same email
        user2 = User(
            email="unique@example.com",
            username="user2",
            password_hash="hashed123"
        )
        db_session.add(user2)
        
        with pytest.raises(Exception):  # Should raise IntegrityError
            await db_session.commit()
    
    async def test_user_unique_username(self, db_session: AsyncSession):
        """Test that username must be unique."""
        user1 = User(
            email="user1@example.com",
            username="uniqueusername",
            password_hash="hashed123"
        )
        db_session.add(user1)
        await db_session.commit()
        
        # Try to create another user with same username
        user2 = User(
            email="user2@example.com",
            username="uniqueusername",
            password_hash="hashed123"
        )
        db_session.add(user2)
        
        with pytest.raises(Exception):  # Should raise IntegrityError
            await db_session.commit()
    
    async def test_user_company_relationship(self, db_session: AsyncSession):
        """Test user-company relationship."""
        # Create a company first
        company = Company(
            name="Test Company",
            domain="testcompany.com",
            size=CompanySize.MEDIUM
        )
        db_session.add(company)
        await db_session.commit()
        await db_session.refresh(company)
        
        # Create user with company
        user = User(
            email="employee@testcompany.com",
            username="employee1",
            password_hash="hashed123",
            company_id=company.id
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        assert user.company_id == company.id
        
        # Query user with company
        result = await db_session.execute(
            select(User).where(User.id == user.id)
        )
        user_with_company = result.scalar_one()
        
        assert user_with_company.company_id == company.id
    
    async def test_user_roles(self):
        """Test UserRole enum values."""
        assert UserRole.USER.value == "user"
        assert UserRole.COMPANY_ADMIN.value == "company_admin"
        assert UserRole.ADMIN.value == "admin"
    
    async def test_user_soft_delete(self, db_session: AsyncSession):
        """Test soft delete functionality."""
        user = User(
            email="delete@example.com",
            username="deleteuser",
            password_hash="hashed123"
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        # Soft delete
        user.deleted_at = datetime.utcnow()
        await db_session.commit()
        
        # User should still exist in database
        result = await db_session.execute(
            select(User).where(User.id == user.id)
        )
        deleted_user = result.scalar_one()
        
        assert deleted_user is not None
        assert deleted_user.deleted_at is not None
    
    async def test_user_verification(self, db_session: AsyncSession):
        """Test user verification functionality."""
        user = User(
            email="verify@example.com",
            username="verifyuser",
            password_hash="hashed123"
        )
        db_session.add(user)
        await db_session.commit()
        
        assert user.is_verified is False
        assert user.verified_at is None
        
        # Verify user
        user.is_verified = True
        user.verified_at = datetime.utcnow()
        await db_session.commit()
        await db_session.refresh(user)
        
        assert user.is_verified is True
        assert user.verified_at is not None
    
    async def test_user_login_tracking(self, db_session: AsyncSession):
        """Test login tracking fields."""
        user = User(
            email="login@example.com",
            username="loginuser",
            password_hash="hashed123"
        )
        db_session.add(user)
        await db_session.commit()
        
        assert user.last_login is None
        assert user.failed_login_attempts == 0
        assert user.locked_until is None
        
        # Simulate successful login
        user.last_login = datetime.utcnow()
        user.failed_login_attempts = 0
        await db_session.commit()
        
        assert user.last_login is not None
        assert user.failed_login_attempts == 0
        
        # Simulate failed login attempts
        user.failed_login_attempts = 3
        user.locked_until = datetime.utcnow() + timedelta(minutes=30)
        await db_session.commit()
        
        assert user.failed_login_attempts == 3
        assert user.locked_until is not None
    
    async def test_user_default_values(self, db_session: AsyncSession):
        """Test default values for user fields."""
        user = User(
            email="defaults@example.com",
            username="defaultuser",
            password_hash="hashed123"
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        assert user.role == UserRole.USER
        assert user.is_active is True
        assert user.is_verified is False
        assert user.failed_login_attempts == 0
        assert user.language == "en"
        assert user.timezone == "UTC"
        assert user.email_notifications_enabled is True
        assert user.deleted_at is None
    
    async def test_user_update(self, db_session: AsyncSession):
        """Test updating user fields."""
        user = User(
            email="update@example.com",
            username="updateuser",
            password_hash="hashed123",
            full_name="Original Name"
        )
        db_session.add(user)
        await db_session.commit()
        
        original_created_at = user.created_at
        
        # Update user
        user.full_name = "Updated Name"
        user.role = UserRole.COMPANY_ADMIN
        user.department = "Management"
        user.job_title = "Manager"
        
        await db_session.commit()
        await db_session.refresh(user)
        
        assert user.full_name == "Updated Name"
        assert user.role == UserRole.COMPANY_ADMIN
        assert user.department == "Management"
        assert user.job_title == "Manager"
        assert user.created_at == original_created_at
        assert user.updated_at > original_created_at
    
    async def test_user_email_notifications(self, db_session: AsyncSession):
        """Test email notification settings."""
        user = User(
            email="notifications@example.com",
            username="notifyuser",
            password_hash="hashed123"
        )
        db_session.add(user)
        await db_session.commit()
        
        # Default should be enabled
        assert user.email_notifications_enabled is True
        
        # Disable notifications
        user.email_notifications_enabled = False
        await db_session.commit()
        await db_session.refresh(user)
        
        assert user.email_notifications_enabled is False