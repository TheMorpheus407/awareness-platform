"""Tests for users API endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User, UserRole
from models.company import Company


class TestUsersAPI:
    """Test cases for users API endpoints."""
    
    async def test_list_users_as_admin(
        self, 
        client: AsyncClient, 
        admin_token_headers: dict,
        test_user: User
    ):
        """Test listing users as admin."""
        response = await client.get(
            "/api/users/",
            headers=admin_token_headers
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
        client: AsyncClient, 
        company_admin_token_headers: dict,
        test_company: Company,
        db_session: AsyncSession
    ):
        """Test that company admin can only see users from their company."""
        # Create a user in the same company
        company_user = User(
            email="samecompany@example.com",
            username="samecompanyuser",
            hashed_password="hashed123",
            company_id=test_company.id
        )
        db_session.add(company_user)
        
        # Create a user in a different company
        other_company = Company(
            name="Other Company",
            domain="other.com"
        )
        db_session.add(other_company)
        await db_session.commit()
        
        other_user = User(
            email="othercompany@example.com",
            username="othercompanyuser",
            hashed_password="hashed123",
            company_id=other_company.id
        )
        db_session.add(other_user)
        await db_session.commit()
        
        response = await client.get(
            "/api/users/",
            headers=company_admin_token_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should only see users from their company
        for user in data["items"]:
            assert user["company_id"] == str(test_company.id)
    
    async def test_get_user_by_id(
        self, 
        client: AsyncClient, 
        admin_token_headers: dict,
        test_user: User
    ):
        """Test getting a specific user by ID."""
        response = await client.get(
            f"/api/users/{test_user.id}",
            headers=admin_token_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_user.id)
        assert data["email"] == test_user.email
        assert data["username"] == test_user.username
        assert data["role"] == test_user.role.value
        assert "hashed_password" not in data  # Should not expose password
    
    async def test_get_current_user(
        self, 
        client: AsyncClient, 
        user_token_headers: dict,
        test_user: User
    ):
        """Test getting current user info."""
        response = await client.get(
            "/api/users/me",
            headers=user_token_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["username"] == test_user.username
    
    async def test_create_user_as_admin(
        self, 
        client: AsyncClient, 
        admin_token_headers: dict,
        test_company: Company
    ):
        """Test creating a new user as admin."""
        user_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "StrongPassword123!",
            "full_name": "New User",
            "role": "user",
            "company_id": str(test_company.id),
            "department": "Sales",
            "job_title": "Sales Manager"
        }
        
        response = await client.post(
            "/api/users/",
            json=user_data,
            headers=admin_token_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["username"] == user_data["username"]
        assert data["full_name"] == user_data["full_name"]
        assert data["role"] == user_data["role"]
        assert data["is_active"] is True
        assert data["is_verified"] is False
    
    async def test_create_user_duplicate_email(
        self, 
        client: AsyncClient, 
        admin_token_headers: dict,
        test_user: User
    ):
        """Test creating a user with duplicate email."""
        user_data = {
            "email": test_user.email,  # Use existing email
            "username": "newusername",
            "password": "StrongPassword123!"
        }
        
        response = await client.post(
            "/api/users/",
            json=user_data,
            headers=admin_token_headers
        )
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()
    
    async def test_create_user_weak_password(
        self, 
        client: AsyncClient, 
        admin_token_headers: dict
    ):
        """Test creating a user with weak password."""
        user_data = {
            "email": "weakpass@example.com",
            "username": "weakpassuser",
            "password": "weak"  # Too short and simple
        }
        
        response = await client.post(
            "/api/users/",
            json=user_data,
            headers=admin_token_headers
        )
        
        assert response.status_code == 422  # Validation error
    
    async def test_update_user(
        self, 
        client: AsyncClient, 
        admin_token_headers: dict,
        test_user: User
    ):
        """Test updating a user."""
        update_data = {
            "full_name": "Updated Name",
            "department": "IT",
            "job_title": "Senior Developer",
            "phone_number": "+491234567890"
        }
        
        response = await client.put(
            f"/api/users/{test_user.id}",
            json=update_data,
            headers=admin_token_headers
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
        client: AsyncClient, 
        user_token_headers: dict
    ):
        """Test users updating their own profile."""
        update_data = {
            "full_name": "Self Updated",
            "language": "de",
            "timezone": "Europe/Berlin",
            "email_notifications_enabled": False
        }
        
        response = await client.put(
            "/api/users/me",
            json=update_data,
            headers=user_token_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == update_data["full_name"]
        assert data["language"] == update_data["language"]
        assert data["timezone"] == update_data["timezone"]
        assert data["email_notifications_enabled"] is False
    
    async def test_change_password(
        self, 
        client: AsyncClient, 
        user_token_headers: dict
    ):
        """Test changing user password."""
        password_data = {
            "current_password": "testpassword123",  # Assuming this is the test password
            "new_password": "NewStrongPassword123!"
        }
        
        response = await client.post(
            "/api/users/me/change-password",
            json=password_data,
            headers=user_token_headers
        )
        
        assert response.status_code == 200
        assert response.json()["message"] == "Password updated successfully"
    
    async def test_delete_user(
        self, 
        client: AsyncClient, 
        admin_token_headers: dict,
        db_session: AsyncSession
    ):
        """Test deleting a user."""
        # Create a user to delete
        user = User(
            email="todelete@example.com",
            username="todeleteuser",
            hashed_password="hashed123"
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        response = await client.delete(
            f"/api/users/{user.id}",
            headers=admin_token_headers
        )
        
        assert response.status_code == 204
        
        # Verify user is deleted
        response = await client.get(
            f"/api/users/{user.id}",
            headers=admin_token_headers
        )
        assert response.status_code == 404
    
    async def test_regular_user_cannot_delete_others(
        self, 
        client: AsyncClient, 
        user_token_headers: dict,
        db_session: AsyncSession
    ):
        """Test that regular users cannot delete other users."""
        # Create another user
        other_user = User(
            email="other@example.com",
            username="otheruser",
            hashed_password="hashed123"
        )
        db_session.add(other_user)
        await db_session.commit()
        await db_session.refresh(other_user)
        
        response = await client.delete(
            f"/api/users/{other_user.id}",
            headers=user_token_headers
        )
        
        assert response.status_code == 403
    
    async def test_filter_users_by_role(
        self, 
        client: AsyncClient, 
        admin_token_headers: dict,
        db_session: AsyncSession
    ):
        """Test filtering users by role."""
        # Create users with different roles
        roles = [UserRole.USER, UserRole.COMPANY_ADMIN, UserRole.ADMIN]
        for i, role in enumerate(roles):
            user = User(
                email=f"role{i}@example.com",
                username=f"roleuser{i}",
                hashed_password="hashed123",
                role=role
            )
            db_session.add(user)
        await db_session.commit()
        
        # Filter by company_admin role
        response = await client.get(
            "/api/users/?role=company_admin",
            headers=admin_token_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # All returned users should have company_admin role
        for user in data["items"]:
            assert user["role"] == "company_admin"
    
    async def test_search_users_by_email(
        self, 
        client: AsyncClient, 
        admin_token_headers: dict,
        test_user: User
    ):
        """Test searching users by email."""
        response = await client.get(
            f"/api/users/?search={test_user.email[:5]}",
            headers=admin_token_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should find at least the test user
        assert len(data["items"]) >= 1
        emails = [item["email"] for item in data["items"]]
        assert test_user.email in emails
    
    async def test_user_count_endpoint(
        self, 
        client: AsyncClient, 
        admin_token_headers: dict
    ):
        """Test getting total user count."""
        response = await client.get(
            "/api/users/count",
            headers=admin_token_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert isinstance(data["count"], int)
        assert data["count"] >= 1  # At least the admin user exists