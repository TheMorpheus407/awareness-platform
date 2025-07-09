import asyncio
import os
import sys
from pathlib import Path
from typing import AsyncGenerator, Generator
import pytest
import pytest_asyncio
import uuid
import json

# Add backend directory to sys.path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Set test environment variables before importing app
os.environ["DATABASE_URL"] = "postgresql://test:test@localhost/test"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["FRONTEND_URL"] = "http://localhost:5173"
os.environ["TESTING"] = "true"
os.environ["ENVIRONMENT"] = "test"
os.environ["STRIPE_SECRET_KEY"] = "sk_test_placeholder_for_testing"
os.environ["STRIPE_PUBLISHABLE_KEY"] = "pk_test_placeholder_for_testing"
os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_test_placeholder_for_testing"

from httpx import AsyncClient
from sqlalchemy import create_engine, event, TypeDecorator, CHAR, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from fastapi.testclient import TestClient

# Test database URL - using sync SQLite for simplicity
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
ASYNC_SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Create async engine for async tests
async_engine = create_async_engine(
    ASYNC_SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Create test session
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncTestingSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=async_engine, class_=AsyncSession
)


def override_get_db():
    """Override the get_db dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


async def override_get_async_db():
    """Override the get_db dependency for async testing."""
    async with AsyncTestingSessionLocal() as session:
        yield session


# Add UUID compatibility for SQLite
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Enable foreign keys for SQLite."""
    if "sqlite" in SQLALCHEMY_DATABASE_URL:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


# Monkey patch PostgreSQL types to work with SQLite
from sqlalchemy.dialects import postgresql
import json

class SQLiteUUID(TypeDecorator):
    """Platform-independent UUID type that works with SQLite."""
    impl = String(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return str(value)
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if not isinstance(value, uuid.UUID):
            value = uuid.UUID(value)
        return value


class SQLiteARRAY(TypeDecorator):
    """SQLite-compatible ARRAY type using JSON."""
    impl = String()
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return json.loads(value)


# Override PostgreSQL types to use our compatible versions in tests
original_uuid = postgresql.UUID
original_array = postgresql.ARRAY

def patched_uuid(*args, **kwargs):
    # Remove as_uuid argument for SQLite compatibility
    kwargs.pop('as_uuid', None)
    if 'sqlite' in engine.url.drivername:
        return SQLiteUUID(*args, **kwargs)
    return original_uuid(*args, **kwargs)

def patched_array(*args, **kwargs):
    if 'sqlite' in engine.url.drivername:
        return SQLiteARRAY(*args, **kwargs)
    return original_array(*args, **kwargs)

postgresql.UUID = patched_uuid
postgresql.ARRAY = patched_array

# Now import models and app after setting up UUID compatibility
from main import app
from db.base import Base
from db.session import get_db
from core.config import settings
from models.user import User, UserRole
from models.company import Company, CompanySize, CompanyStatus, SubscriptionTier
from core.security import get_password_hash


@pytest.fixture(scope="function")
def db_session():
    """Create a new database session for a test."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    session = TestingSessionLocal()
    
    yield session
    
    # Cleanup
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest_asyncio.fixture(scope="function")
async def db() -> AsyncGenerator[AsyncSession, None]:
    """Create a new async database session for a test."""
    # Create tables
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async with AsyncTestingSessionLocal() as session:
        yield session
    
    # Cleanup
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
def client(db_session) -> TestClient:
    """Create a test client."""
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app, base_url="http://localhost") as c:
        yield c
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def async_client(db: AsyncSession) -> AsyncClient:
    """Create an async test client."""
    async def get_test_db():
        yield db
    
    app.dependency_overrides[get_db] = get_test_db
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
        size=CompanySize.MEDIUM,
        status=CompanyStatus.ACTIVE,
        subscription_tier=SubscriptionTier.FREE
    )
    db_session.add(company)
    db_session.commit()
    db_session.refresh(company)
    return company


@pytest_asyncio.fixture
async def async_test_company(db: AsyncSession) -> Company:
    """Create a test company for async tests."""
    company = Company(
        name="Test Company",
        domain="testcompany.com",
        industry="Technology",
        size=CompanySize.MEDIUM,
        status=CompanyStatus.ACTIVE,
        subscription_tier=SubscriptionTier.FREE
    )
    db.add(company)
    await db.commit()
    await db.refresh(company)
    return company


@pytest.fixture
def test_user(db_session, test_company) -> User:
    """Create a test user."""
    user = User(
        email="test@example.com",
        password_hash=get_password_hash("testpassword123"),
        first_name="Test",
        last_name="User",
        company_id=test_company.id,
        is_active=True,
        email_verified=True,
        role=UserRole.EMPLOYEE
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def async_test_user(db: AsyncSession, async_test_company: Company) -> User:
    """Create a test user for async tests."""
    user = User(
        email="test@example.com",
        password_hash=get_password_hash("testpassword123"),
        first_name="Test",
        last_name="User",
        company_id=async_test_company.id,
        is_active=True,
        email_verified=True,
        role=UserRole.EMPLOYEE
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture
def test_admin(db_session, test_company) -> User:
    """Create a test admin user."""
    admin = User(
        email="admin@example.com",
        password_hash=get_password_hash("adminpassword123"),
        first_name="Admin",
        last_name="User",
        company_id=test_company.id,
        is_active=True,
        email_verified=True,
        role=UserRole.COMPANY_ADMIN
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


@pytest_asyncio.fixture
async def async_test_admin(db: AsyncSession, async_test_company: Company) -> User:
    """Create a test admin user for async tests."""
    admin = User(
        email="admin@example.com",
        password_hash=get_password_hash("adminpassword123"),
        first_name="Admin",
        last_name="User",
        company_id=async_test_company.id,
        is_active=True,
        email_verified=True,
        role=UserRole.COMPANY_ADMIN
    )
    db.add(admin)
    await db.commit()
    await db.refresh(admin)
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


@pytest_asyncio.fixture
async def async_auth_headers(async_client: AsyncClient, async_test_user: User) -> dict:
    """Get authentication headers for a regular user in async tests."""
    response = await async_client.post(
        "/api/v1/auth/login",
        data={
            "username": async_test_user.email,
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


@pytest_asyncio.fixture
async def async_admin_auth_headers(async_client: AsyncClient, async_test_admin: User) -> dict:
    """Get authentication headers for an admin user in async tests."""
    response = await async_client.post(
        "/api/v1/auth/login",
        data={
            "username": async_test_admin.email,
            "password": "adminpassword123"
        }
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# Additional fixtures for 2FA testing
@pytest.fixture
def test_user_with_2fa(db_session, test_company) -> User:
    """Create a test user with 2FA enabled."""
    from core.two_factor_auth import TwoFactorAuth
    
    user = User(
        email="2fa@example.com",
        password_hash=get_password_hash("2fapassword123"),
        first_name="TwoFA",
        last_name="User",
        company_id=test_company.id,
        is_active=True,
        email_verified=True,
        role=UserRole.EMPLOYEE
    )
    
    # Enable 2FA
    two_fa = TwoFactorAuth()
    user.totp_secret = two_fa.generate_secret()
    user.totp_enabled = True
    backup_codes = two_fa.generate_backup_codes()
    user.backup_codes = json.dumps([get_password_hash(code) for code in backup_codes])
    
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # Store the raw backup codes for testing
    user._raw_backup_codes = backup_codes
    user._totp_secret = user.totp_secret
    
    return user


@pytest_asyncio.fixture
async def async_test_user_with_2fa(db: AsyncSession, async_test_company: Company) -> User:
    """Create a test user with 2FA enabled for async tests."""
    from core.two_factor_auth import TwoFactorAuth
    
    user = User(
        email="2fa@example.com",
        password_hash=get_password_hash("2fapassword123"),
        first_name="TwoFA",
        last_name="User",
        company_id=async_test_company.id,
        is_active=True,
        email_verified=True,
        role=UserRole.EMPLOYEE
    )
    
    # Enable 2FA
    two_fa = TwoFactorAuth()
    user.totp_secret = two_fa.generate_secret()
    user.totp_enabled = True
    backup_codes = two_fa.generate_backup_codes()
    user.backup_codes = json.dumps([get_password_hash(code) for code in backup_codes])
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # Store the raw backup codes for testing
    user._raw_backup_codes = backup_codes
    user._totp_secret = user.totp_secret
    
    return user