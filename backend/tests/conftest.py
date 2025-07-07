import asyncio
import os
from typing import AsyncGenerator, Generator
import pytest

# Set test environment variables before importing app
os.environ["DATABASE_URL"] = "postgresql://test:test@localhost/test"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["FRONTEND_URL"] = "http://localhost:5173"

from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from main import app
from db.base import Base
from db.session import get_db
from core.config import settings
from models.user import User
from models.company import Company
from core.security import get_password_hash

# Test database URL
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

# Create test engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Create test session
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override the get_db dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session) -> Generator:
    """Create a test client."""
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def async_client(db_session) -> AsyncGenerator:
    """Create an async test client."""
    app.dependency_overrides[get_db] = lambda: db_session
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
def test_company(db_session) -> Company:
    """Create a test company."""
    company = Company(
        name="Test Company",
        domain="testcompany.com",
        industry="Technology",
        size="50-100",
        is_active=True
    )
    db_session.add(company)
    db_session.commit()
    db_session.refresh(company)
    return company


@pytest.fixture
def test_user(db_session, test_company) -> User:
    """Create a test user."""
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpassword123"),
        full_name="Test User",
        company_id=test_company.id,
        is_active=True,
        is_superuser=False,
        role="user"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_admin(db_session, test_company) -> User:
    """Create a test admin user."""
    admin = User(
        email="admin@example.com",
        hashed_password=get_password_hash("adminpassword123"),
        full_name="Admin User",
        company_id=test_company.id,
        is_active=True,
        is_superuser=True,
        role="admin"
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


@pytest.fixture
def auth_headers(client, test_user) -> dict:
    """Get authentication headers for a regular user."""
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user.email,
            "password": "testpassword123"
        }
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_auth_headers(client, test_admin) -> dict:
    """Get authentication headers for an admin user."""
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": test_admin.email,
            "password": "adminpassword123"
        }
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}