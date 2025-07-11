"""
Simplified test configuration using SQLite for environments without PostgreSQL.
Note: This may not test all PostgreSQL-specific features like ARRAY, UUID, etc.
"""
import asyncio
import os
import sys
from pathlib import Path
from typing import AsyncGenerator, Generator
import pytest
import pytest_asyncio

# Configure event loop for async tests
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()

# Add backend directory to sys.path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Set test environment variables before importing app
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["FRONTEND_URL"] = "http://localhost:5173"
os.environ["TESTING"] = "true"
os.environ["ENVIRONMENT"] = "test"
os.environ["STRIPE_SECRET_KEY"] = "sk_test_placeholder_for_testing"
os.environ["STRIPE_PUBLISHABLE_KEY"] = "pk_test_placeholder_for_testing"
os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_test_placeholder_for_testing"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["REDIS_PASSWORD"] = ""
os.environ["REDIS_POOL_SIZE"] = "10"
os.environ["REDIS_DECODE_RESPONSES"] = "true"

from httpx import AsyncClient

# Now import models and app after setting up environment
from main import app
from core.config import settings


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async HTTP client for testing."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    from fastapi.testclient import TestClient
    return TestClient(app)