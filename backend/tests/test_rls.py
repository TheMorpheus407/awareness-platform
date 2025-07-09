"""Tests for Row Level Security (RLS) policies."""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import ProgrammingError

from models.user import User, UserRole
from models.company import Company, CompanySize, CompanyStatus, SubscriptionTier
from models.course import Course, UserCourseProgress
from core.security import get_password_hash


@pytest.mark.asyncio
class TestRLSPolicies:
    """Test Row Level Security policies."""

    async def test_user_can_only_see_own_company_users(
        self, db: AsyncSession, async_test_company: Company
    ) -> None:
        """Test that users can only see users from their own company."""
        # Create another company
        other_company = Company(
            name="Other Company",
            domain="other.com",
            industry="Finance",
            size=CompanySize.SMALL,
            status=CompanyStatus.ACTIVE,
            subscription_tier=SubscriptionTier.BASIC
        )
        db.add(other_company)
        await db.commit()
        
        # Create users in both companies
        user1 = User(
            email="user1@test.com",
            password_hash=get_password_hash("password"),
            first_name="User",
            last_name="One",
            company_id=async_test_company.id,
            role=UserRole.EMPLOYEE
        )
        
        user2 = User(
            email="user2@other.com",
            password_hash=get_password_hash("password"),
            first_name="User",
            last_name="Two",
            company_id=other_company.id,
            role=UserRole.EMPLOYEE
        )
        
        db.add_all([user1, user2])
        await db.commit()
        
        # Set RLS context for user1
        await db.execute(text(f"SET LOCAL app.current_user_id = '{user1.id}'"))
        await db.execute(text(f"SET LOCAL app.current_company_id = '{user1.company_id}'"))
        
        # Query users - should only see users from same company
        result = await db.execute(text("SELECT email FROM users WHERE is_active = true"))
        emails = [row[0] for row in result]
        
        assert user1.email in emails
        assert user2.email not in emails

    async def test_company_admin_can_see_all_company_data(
        self, db: AsyncSession, async_test_company: Company
    ) -> None:
        """Test that company admins can see all data from their company."""
        # Create company admin
        admin = User(
            email="admin@test.com",
            password_hash=get_password_hash("password"),
            first_name="Admin",
            last_name="User",
            company_id=async_test_company.id,
            role=UserRole.COMPANY_ADMIN
        )
        db.add(admin)
        
        # Create regular employee
        employee = User(
            email="employee@test.com",
            password_hash=get_password_hash("password"),
            first_name="Employee",
            last_name="User",
            company_id=async_test_company.id,
            role=UserRole.EMPLOYEE
        )
        db.add(employee)
        await db.commit()
        
        # Set RLS context for admin
        await db.execute(text(f"SET LOCAL app.current_user_id = '{admin.id}'"))
        await db.execute(text(f"SET LOCAL app.current_company_id = '{admin.company_id}'"))
        await db.execute(text(f"SET LOCAL app.current_user_role = '{admin.role.value}'"))
        
        # Query users - admin should see all company users
        result = await db.execute(text("SELECT email FROM users WHERE company_id = :company_id"), 
                                {"company_id": str(async_test_company.id)})
        emails = [row[0] for row in result]
        
        assert admin.email in emails
        assert employee.email in emails

    async def test_user_cannot_update_other_users(
        self, db: AsyncSession, async_test_company: Company
    ) -> None:
        """Test that users cannot update other users' data."""
        # Create two users
        user1 = User(
            email="user1@test.com",
            password_hash=get_password_hash("password"),
            first_name="User",
            last_name="One",
            company_id=async_test_company.id,
            role=UserRole.EMPLOYEE
        )
        
        user2 = User(
            email="user2@test.com",
            password_hash=get_password_hash("password"),
            first_name="User",
            last_name="Two",
            company_id=async_test_company.id,
            role=UserRole.EMPLOYEE
        )
        
        db.add_all([user1, user2])
        await db.commit()
        
        # Set RLS context for user1
        await db.execute(text(f"SET LOCAL app.current_user_id = '{user1.id}'"))
        
        # Try to update user2 - should fail or have no effect
        try:
            await db.execute(
                text("UPDATE users SET first_name = :name WHERE id = :id"),
                {"name": "Hacked", "id": str(user2.id)}
            )
            await db.commit()
        except ProgrammingError:
            # RLS policy prevented the update
            await db.rollback()
        
        # Verify user2 was not updated
        await db.refresh(user2)
        assert user2.first_name == "User"

    async def test_course_progress_visibility(
        self, db: AsyncSession, async_test_company: Company
    ) -> None:
        """Test that users can only see their own course progress."""
        # Create users
        user1 = User(
            email="user1@test.com",
            password_hash=get_password_hash("password"),
            first_name="User",
            last_name="One",
            company_id=async_test_company.id,
            role=UserRole.EMPLOYEE
        )
        
        user2 = User(
            email="user2@test.com",
            password_hash=get_password_hash("password"),
            first_name="User",
            last_name="Two",
            company_id=async_test_company.id,
            role=UserRole.EMPLOYEE
        )
        
        db.add_all([user1, user2])
        await db.commit()
        
        # Create course
        course = Course(
            title="Security Training",
            description="Basic security training",
            category="security",
            duration_minutes=60,
            difficulty_level="beginner",
            is_active=True
        )
        db.add(course)
        await db.commit()
        
        # Create progress records
        progress1 = UserCourseProgress(
            user_id=user1.id,
            course_id=course.id,
            company_id=async_test_company.id,
            status="in_progress"
        )
        
        progress2 = UserCourseProgress(
            user_id=user2.id,
            course_id=course.id,
            company_id=async_test_company.id,
            status="in_progress"
        )
        
        db.add_all([progress1, progress2])
        await db.commit()
        
        # Set RLS context for user1
        await db.execute(text(f"SET LOCAL app.current_user_id = '{user1.id}'"))
        
        # Query progress - should only see own
        result = await db.execute(
            text("SELECT user_id FROM user_course_progress WHERE course_id = :course_id"),
            {"course_id": str(course.id)}
        )
        user_ids = [row[0] for row in result]
        
        assert str(user1.id) in user_ids
        assert str(user2.id) not in user_ids

    async def test_superuser_bypass_rls(
        self, db: AsyncSession, async_test_company: Company
    ) -> None:
        """Test that superusers can bypass RLS policies."""
        # Create another company
        other_company = Company(
            name="Other Company",
            domain="other.com",
            industry="Finance",
            size=CompanySize.SMALL,
            status=CompanyStatus.ACTIVE,
            subscription_tier=SubscriptionTier.BASIC
        )
        db.add(other_company)
        await db.commit()
        
        # Create superuser
        superuser = User(
            email="super@admin.com",
            password_hash=get_password_hash("password"),
            first_name="Super",
            last_name="Admin",
            company_id=async_test_company.id,
            role=UserRole.SUPER_ADMIN,
            is_superuser=True
        )
        
        # Create user in other company
        other_user = User(
            email="user@other.com",
            password_hash=get_password_hash("password"),
            first_name="Other",
            last_name="User",
            company_id=other_company.id,
            role=UserRole.EMPLOYEE
        )
        
        db.add_all([superuser, other_user])
        await db.commit()
        
        # Set RLS context for superuser
        await db.execute(text(f"SET LOCAL app.current_user_id = '{superuser.id}'"))
        await db.execute(text(f"SET LOCAL app.current_company_id = '{superuser.company_id}'"))
        await db.execute(text("SET LOCAL app.is_superuser = 'true'"))
        
        # Query all users - superuser should see everyone
        result = await db.execute(text("SELECT email FROM users"))
        emails = [row[0] for row in result]
        
        assert superuser.email in emails
        assert other_user.email in emails

    async def test_rls_prevents_data_leakage(
        self, db: AsyncSession
    ) -> None:
        """Test that RLS prevents data leakage between companies."""
        # Create two companies
        company1 = Company(
            name="Company One",
            domain="company1.com",
            industry="Tech",
            size=CompanySize.MEDIUM,
            status=CompanyStatus.ACTIVE,
            subscription_tier=SubscriptionTier.BASIC
        )
        
        company2 = Company(
            name="Company Two",
            domain="company2.com",
            industry="Finance",
            size=CompanySize.LARGE,
            status=CompanyStatus.ACTIVE,
            subscription_tier=SubscriptionTier.PREMIUM
        )
        
        db.add_all([company1, company2])
        await db.commit()
        
        # Create users in different companies
        user1 = User(
            email="user@company1.com",
            password_hash=get_password_hash("password"),
            first_name="Company1",
            last_name="User",
            company_id=company1.id,
            role=UserRole.EMPLOYEE
        )
        
        user2 = User(
            email="user@company2.com",
            password_hash=get_password_hash("password"),
            first_name="Company2",
            last_name="User",
            company_id=company2.id,
            role=UserRole.EMPLOYEE
        )
        
        db.add_all([user1, user2])
        await db.commit()
        
        # Set RLS context for user from company1
        await db.execute(text(f"SET LOCAL app.current_user_id = '{user1.id}'"))
        await db.execute(text(f"SET LOCAL app.current_company_id = '{company1.id}'"))
        
        # Try to query company2 data
        result = await db.execute(
            text("SELECT name FROM companies WHERE id = :id"),
            {"id": str(company2.id)}
        )
        companies = list(result)
        
        # Should not be able to see company2
        assert len(companies) == 0