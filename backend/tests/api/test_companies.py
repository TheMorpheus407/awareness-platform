"""Tests for companies API endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models.company import Company, CompanySize, SubscriptionTier
from models.user import User, UserRole


@pytest.mark.asyncio
class TestCompaniesAPI:
    """Test cases for companies API endpoints."""
    
    async def test_list_companies_as_admin(
        self, 
        async_client: AsyncClient, 
        async_admin_auth_headers: dict,
        async_test_company: Company
    ):
        """Test listing companies as admin."""
        response = await async_client.get(
            "/api/v1/companies/",
            headers=async_admin_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert len(data["items"]) >= 1
        
        # Check if test company is in the list
        company_ids = [item["id"] for item in data["items"]]
        assert str(async_test_company.id) in company_ids
    
    async def test_list_companies_as_user_forbidden(
        self, 
        async_client: AsyncClient, 
        async_auth_headers: dict
    ):
        """Test that regular users cannot list all companies."""
        response = await async_client.get(
            "/api/v1/companies/",
            headers=async_auth_headers
        )
        
        assert response.status_code == 403
    
    async def test_get_company_by_id(
        self, 
        async_client: AsyncClient, 
        async_admin_auth_headers: dict,
        async_test_company: Company
    ):
        """Test getting a specific company by ID."""
        response = await async_client.get(
            f"/api/v1/companies/{async_test_company.id}",
            headers=async_admin_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(async_test_company.id)
        assert data["name"] == async_test_company.name
        assert data["domain"] == async_test_company.domain
        assert data["size"] == async_test_company.size.value
    
    async def test_get_nonexistent_company(
        self, 
        async_client: AsyncClient, 
        admin_token_headers: dict
    ):
        """Test getting a company that doesn't exist."""
        response = await async_client.get(
            "/api/v1/companies/00000000-0000-0000-0000-000000000000",
            headers=async_admin_auth_headers
        )
        
        assert response.status_code == 404
    
    async def test_create_company_as_admin(
        self, 
        async_client: AsyncClient, 
        admin_token_headers: dict
    ):
        """Test creating a new company as admin."""
        company_data = {
            "name": "New Test Company",
            "domain": "newtestcompany.com",
            "size": "medium",
            "subscription_tier": "professional",
            "max_users": 50,
            "industry": "Technology",
            "country": "Germany",
            "city": "Munich"
        }
        
        response = await async_client.post(
            "/api/v1/companies/",
            json=company_data,
            headers=async_admin_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == company_data["name"]
        assert data["domain"] == company_data["domain"]
        assert data["size"] == company_data["size"]
        assert data["subscription_tier"] == company_data["subscription_tier"]
        assert data["is_active"] is True
    
    async def test_create_company_duplicate_domain(
        self, 
        async_client: AsyncClient, 
        async_admin_auth_headers: dict,
        async_test_company: Company
    ):
        """Test creating a company with duplicate domain."""
        company_data = {
            "name": "Duplicate Domain Company",
            "domain": test_company.domain,  # Use existing domain
            "size": "small"
        }
        
        response = await async_client.post(
            "/api/v1/companies/",
            json=company_data,
            headers=async_admin_auth_headers
        )
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()
    
    async def test_update_company(
        self, 
        async_client: AsyncClient, 
        async_admin_auth_headers: dict,
        async_test_company: Company
    ):
        """Test updating a company."""
        update_data = {
            "name": "Updated Company Name",
            "size": "large",
            "subscription_tier": "enterprise",
            "max_users": 200
        }
        
        response = await async_client.put(
            f"/api/v1/companies/{async_test_company.id}",
            json=update_data,
            headers=async_admin_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["size"] == update_data["size"]
        assert data["subscription_tier"] == update_data["subscription_tier"]
        assert data["max_users"] == update_data["max_users"]
        # Domain should not change
        assert data["domain"] == test_company.domain
    
    async def test_delete_company(
        self, 
        async_client: AsyncClient, 
        async_admin_auth_headers: dict,
        db_session: AsyncSession
    ):
        """Test deleting a company."""
        # Create a company to delete
        company = Company(
            name="Company to Delete",
            domain="todelete.com",
            size=CompanySize.SMALL
        )
        db_session.add(company)
        await db_session.commit()
        await db_session.refresh(company)
        
        response = await async_client.delete(
            f"/api/v1/companies/{company.id}",
            headers=async_admin_auth_headers
        )
        
        assert response.status_code == 204
        
        # Verify company is deleted
        response = await async_client.get(
            f"/api/v1/companies/{company.id}",
            headers=async_admin_auth_headers
        )
        assert response.status_code == 404
    
    async def test_company_user_count(
        self, 
        async_client: AsyncClient, 
        async_admin_auth_headers: dict,
        test_company: Company,
        db_session: AsyncSession
    ):
        """Test getting user count for a company."""
        # Create some users for the company
        for i in range(3):
            user = User(
                email=f"user{i}@{test_company.domain}",
                username=f"companyuser{i}",
                password_hash="hashed123",
                company_id=test_company.id
            )
            db_session.add(user)
        await db_session.commit()
        
        response = await async_client.get(
            f"/api/v1/companies/{test_company.id}/users/count",
            headers=async_admin_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 3
    
    async def test_company_admin_can_view_own_company(
        self, 
        async_client: AsyncClient, 
        company_admin_token_headers: dict,
        async_test_company: Company
    ):
        """Test that company admin can view their own company."""
        response = await async_client.get(
            f"/api/v1/companies/{async_test_company.id}",
            headers=company_admin_token_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_company.id)
    
    async def test_company_admin_cannot_view_other_companies(
        self, 
        async_client: AsyncClient, 
        company_admin_token_headers: dict,
        db_session: AsyncSession
    ):
        """Test that company admin cannot view other companies."""
        # Create another company
        other_company = Company(
            name="Other Company",
            domain="othercompany.com",
            size=CompanySize.MEDIUM
        )
        db_session.add(other_company)
        await db_session.commit()
        await db_session.refresh(other_company)
        
        response = await async_client.get(
            f"/api/v1/companies/{other_company.id}",
            headers=company_admin_token_headers
        )
        
        assert response.status_code == 403
    
    async def test_filter_companies_by_size(
        self, 
        async_client: AsyncClient, 
        async_admin_auth_headers: dict,
        db_session: AsyncSession
    ):
        """Test filtering companies by size."""
        # Create companies with different sizes
        sizes = [CompanySize.SMALL, CompanySize.MEDIUM, CompanySize.LARGE]
        for i, size in enumerate(sizes):
            company = Company(
                name=f"Size Test Company {i}",
                domain=f"sizetest{i}.com",
                size=size
            )
            db_session.add(company)
        await db_session.commit()
        
        # Filter by medium size
        response = await async_client.get(
            "/api/v1/companies/?size=medium",
            headers=async_admin_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # All returned companies should be medium size
        for company in data["items"]:
            assert company["size"] == "medium"
    
    async def test_search_companies_by_name(
        self, 
        async_client: AsyncClient, 
        async_admin_auth_headers: dict,
        async_test_company: Company
    ):
        """Test searching companies by name."""
        response = await async_client.get(
            f"/api/v1/companies/?search={test_company.name[:5]}",
            headers=async_admin_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should find at least the test company
        assert len(data["items"]) >= 1
        company_names = [item["name"] for item in data["items"]]
        assert test_company.name in company_names