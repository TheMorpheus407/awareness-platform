"""Minimal conftest for basic pytest functionality without full app dependencies."""

import pytest
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))


@pytest.fixture
def simple_fixture():
    """A simple fixture for testing."""
    return {"test": "data", "value": 42}


@pytest.fixture
def mock_db_session():
    """Mock database session for testing without actual database."""
    class MockSession:
        def __init__(self):
            self.data = {}
            
        def add(self, obj):
            self.data[id(obj)] = obj
            
        def commit(self):
            pass
            
        def rollback(self):
            self.data.clear()
            
        def close(self):
            pass
            
    return MockSession()


# Minimal test configuration
def pytest_configure(config):
    """Configure pytest with minimal settings."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )