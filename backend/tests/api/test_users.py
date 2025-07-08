"""Tests for users API endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User, UserRole
from models.company import Company


@pytest.mark.asyncio
class TestUsersAPI:
    """Test cases for users API endpoints."""
    
    async def test_list_users_as_admin(
        self, 
        async_client: AsyncClient, 
        async_admin_auth_headers: dict,
        async_test_user: User
    ):
        """Test listing users as admin."""
        response = await async_client.get(
            "/api/v1/users/",
            headers=async_admin_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert len(data["items"]) >= 1
    
    async def test_list_users_as_company_admin(
        self, 
        async_client: AsyncClient, 
        async_admin_auth_headers: dict,
        async_test_company: Company,
        db: AsyncSession
    ):
        """Test that company admin can only see users from their company."""
        # Create a user in the same company
        company_user = User(
            email="samecompany@example.com",
            username="samecompanyuser",
            password_hash="hashed123",
            company_id=async_test_company.id
        )
        db.add(company_user)
        
        # Create a user in a different company
        other_company = Company(
            name="Other Company",
            domain="other.com"
        )
        db.add(other_company)
        await db.commit()
        
        other_user = User(
            email="othercompany@example.com",
            username="othercompanyuser",
            password_hash="hashed123",
            company_id=other_company.id
        )
        db.add(other_user)
        await db.commit()
        
        response = await async_client.get(
            "/api/v1/users/",
            headers=async_admin_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should only see users from their company
        for user in data["items"]:
            assert user["company_id"] == str(test_company.id)
    
    async def test_get_user_by_id(
        self, 
        async_client: AsyncClient, 
        async_admin_auth_headers: dict,
        async_test_user: User
    ):
        """Test getting a specific user by ID."""
        response = await async_client.get(
            f"/api/v1/users/{test_user.id}",
            headers=async_admin_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_user.id)
        assert data["email"] == test_user.email
        assert data["email"] == test_user.email
        assert data["role"] == test_user.role.value
        assert "password_hash" not in data  # Should not expose password
    
    async def test_get_current_user(
        self, 
        async_client: AsyncClient, 
        async_auth_headers: dict,
        async_test_user: User
    ):
        """Test getting current user info."""
        response = await async_client.get(
            "/api/v1/users/me",
            headers=async_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["email"] == test_user.email
    
    async def test_create_user_as_admin(
        self, 
        async_client: AsyncClient, 
        async_admin_auth_headers: dict,
        test_company: Company
    ):
        """Test creating a new user as admin."""
        user_data = {
            "email": "newuser@example.com",
            "email": "newuser",
            "password": "StrongPassword123!",
            "full_name": "New User",
            "role": "user",
            "company_id": str(test_company.id),
            "department": "Sales",
            "job_title": "Sales Manager"
        }
        
        response = await async_client.post(
            "/api/v1/users/",
            json=user_data,
            headers=async_admin_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["email"] == user_data["email"]
        assert data["full_name"] == user_data["full_name"]
        assert data["role"] == user_data["role"]
        assert data["is_active"] is True
        assert data["email_verified"] is False
    
    async def test_create_user_duplicate_email(
        self, 
        async_client: AsyncClient, 
        async_admin_auth_headers: dict,
        async_test_user: User
    ):
        """Test creating a user with duplicate email."""
        user_data = {
            "email": test_user.email,  # Use existing email
            "email": "newusername",
            "password": "StrongPassword123!"
        }
        
        response = await async_client.post(
            "/api/v1/users/",
            json=user_data,
            headers=async_admin_auth_headers
        )
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()
    
    async def test_create_user_weak_password(
        self, 
        async_client: AsyncClient, 
        admin_token_headers: dict
    ):
        """Test creating a user with weak password."""
        user_data = {
            "email": "weakpass@example.com",
            "email": "weakpassuser",
            "password": "weak"  # Too short and simple
        }
        
        response = await async_client.post(
            "/api/v1/users/",
            json=user_data,
            headers=async_admin_auth_headers
        )
        
        assert response.status_code == 422  # Validation error
    
    async def test_update_user(
        self, 
        async_client: AsyncClient, 
        async_admin_auth_headers: dict,
        async_test_user: User
    ):
        """Test updating a user."""
        update_data = {
            "full_name": "Updated Name",
            "department": "IT",
            "job_title": "Senior Developer",
            "phone_number": "+491234567890"
        }
        
        response = await async_client.put(
            f"/api/v1/users/{test_user.id}",
            json=update_data,
            headers=async_admin_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == update_data["full_name"]
        assert data["department"] == update_data["department"]
        assert data["job_title"] == update_data["job_title"]
        assert data["phone_number"] == update_data["phone_number"]
        # Email should not change
        assert data["email"] == test_user.email
    
    async def test_update_own_profile(
        self, 
        async_client: AsyncClient, 
        async_auth_headers: dict
    ):
        """Test users updating their own profile."""
        update_data = {
            "full_name": "Self Updated",
            "language": "de",
            "language": "Europe/Berlin",
            "# email_notifications_enabled": False
        }
        
        response = await async_client.put(
            "/api/v1/users/me",
            json=update_data,
            headers=async_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == update_data["full_name"]
        assert data["language"] == update_data["language"]
        assert data["language"] == update_data["language"]
        assert data["# email_notifications_enabled"] is False
    
    async def test_change_password(
        self, 
        async_client: AsyncClient, 
        async_auth_headers: dict
    ):
        """Test changing user password."""
        password_data = {
            "current_password": "testpassword123",  # Assuming this is the test password
            "new_password": "NewStrongPassword123!"
        }
        
        response = await async_client.post(
            "/api/v1/users/me/change-password",
            json=password_data,
            headers=async_auth_headers
        )
        
        assert response.status_code == 200
        assert response.json()["message"] == "Password updated successfully"
    
    async def test_delete_user(
        self, 
        async_client: AsyncClient, 
        async_admin_auth_headers: dict,
        db: AsyncSession
    ):
        """Test deleting a user."""
        # Create a user to delete
        user = User(
            email="todelete@example.com",
            username="todeleteuser",
            password_hash="hashed123"
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        response = await async_client.delete(
            f"/api/v1/users/{user.id}",
            headers=async_admin_auth_headers
        )
        
        assert response.status_code == 204
        
        # Verify user is deleted
        response = await async_client.get(
            f"/api/v1/users/{user.id}",
            headers=async_admin_auth_headers
        )
        assert response.status_code == 404
    
    async def test_regular_user_cannot_delete_others(
        self, 
        async_client: AsyncClient, 
        async_auth_headers: dict,
        db: AsyncSession
    ):
        """Test that regular users cannot delete other users."""
        # Create another user
        other_user = User(
            email="other@example.com",
            username="otheruser",
            password_hash="hashed123"
        )
        db.add(other_user)
        await db.commit()
        await db.refresh(other_user)
        
        response = await async_client.delete(
            f"/api/v1/users/{other_user.id}",
            headers=async_auth_headers
        )
        
        assert response.status_code == 403
    
    async def test_filter_users_by_role(
        self, 
        async_client: AsyncClient, 
        async_admin_auth_headers: dict,
        db: AsyncSession
    ):
        """Test filtering users by role."""
        # Create users with different roles
        roles = [UserRole.USER, UserRole.COMPANY_ADMIN, UserRole.ADMIN]
        for i, role in enumerate(roles):
            user = User(
                email=f"role{i}@example.com",
                username=f"roleuser{i}",
                password_hash="hashed123",
                role=role
            )
            db.add(user)
        await db.commit()
        
        # Filter by company_admin role
        response = await async_client.get(
            "/api/v1/users/?role=company_admin",
            headers=async_admin_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # All returned users should have company_admin role
        for user in data["items"]:
            assert user["role"] == "company_admin"
    
    async def test_search_users_by_email(
        self, 
        async_client: AsyncClient, 
        async_admin_auth_headers: dict,
        async_test_user: User
    ):
        """Test searching users by email."""
        response = await async_client.get(
            f"/api/v1/users/?search={test_user.email[:5]}",
            headers=async_admin_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should find at least the test user
        assert len(data["items"]) >= 1
        emails = [item["email"] for item in data["items"]]
        assert test_user.email in emails
    
    async def test_user_count_endpoint(
        self, 
        async_client: AsyncClient, 
        admin_token_headers: dict
    ):
        """Test getting total user count."""
        response = await async_client.get(
            "/api/v1/users/count",
            headers=async_admin_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert isinstance(data["count"], int)
        assert data["count"] >= 1  # At least the admin user exists