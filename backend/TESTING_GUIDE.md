# Testing Guide

## Overview
This guide covers comprehensive testing strategies for the Cybersecurity Awareness Platform backend, including unit tests, integration tests, performance tests, and security tests.

## Table of Contents
1. [Testing Philosophy](#testing-philosophy)
2. [Test Structure](#test-structure)
3. [Running Tests](#running-tests)
4. [Writing Tests](#writing-tests)
5. [Test Coverage](#test-coverage)
6. [Performance Testing](#performance-testing)
7. [Security Testing](#security-testing)
8. [E2E Testing](#e2e-testing)
9. [CI/CD Integration](#cicd-integration)
10. [Best Practices](#best-practices)

## Testing Philosophy

### Testing Pyramid
```
        /\         E2E Tests (10%)
       /  \        - Full user workflows
      /    \       - Critical paths only
     /------\      
    /        \     Integration Tests (30%)
   /          \    - API endpoint tests
  /            \   - Database interactions
 /--------------\  
/                \ Unit Tests (60%)
/                 \- Business logic
                   - Individual functions
                   - Edge cases
```

### Key Principles
1. **Fast Feedback**: Unit tests should run in milliseconds
2. **Isolation**: Tests should not depend on each other
3. **Deterministic**: Same input = same output always
4. **Readable**: Tests document expected behavior
5. **Maintainable**: Easy to update when code changes

## Test Structure

### Directory Layout
```
tests/
├── unit/                    # Unit tests
│   ├── core/               # Core functionality tests
│   ├── models/             # Model tests
│   ├── schemas/            # Schema validation tests
│   └── services/           # Service logic tests
├── integration/            # Integration tests
│   ├── api/               # API endpoint tests
│   ├── db/                # Database tests
│   └── external/          # External service tests
├── e2e/                   # End-to-end tests
├── performance/           # Performance tests
├── security/              # Security tests
├── fixtures/              # Test data and fixtures
├── utils/                 # Test utilities
└── conftest.py           # Pytest configuration
```

## Running Tests

### Basic Commands
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=backend --cov-report=html

# Run specific test file
pytest tests/unit/core/test_security.py

# Run tests matching pattern
pytest -k "test_password"

# Run tests in parallel
pytest -n auto

# Run with verbose output
pytest -v

# Run only marked tests
pytest -m "slow"
pytest -m "not slow"
```

### Test Configuration
```bash
# pytest.ini
[tool:pytest]
minversion = 7.0
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --strict-markers
    --tb=short
    --asyncio-mode=auto
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    security: marks tests as security tests
    unit: marks tests as unit tests
```

## Writing Tests

### Unit Test Example
```python
# tests/unit/core/test_security.py
import pytest
from datetime import datetime, timedelta

from backend.core.security import (
    create_access_token,
    verify_password,
    get_password_hash,
    decode_access_token
)


class TestPasswordHashing:
    """Test password hashing functionality."""
    
    def test_password_hash_is_different_from_password(self):
        """Test that hash is different from original password."""
        password = "mysecretpassword"
        hashed = get_password_hash(password)
        assert hashed != password
        assert hashed.startswith("$2b$")
    
    def test_verify_correct_password(self):
        """Test verifying correct password."""
        password = "correctpassword"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True
    
    def test_verify_incorrect_password(self):
        """Test verifying incorrect password."""
        password = "correctpassword"
        hashed = get_password_hash(password)
        assert verify_password("wrongpassword", hashed) is False
    
    @pytest.mark.parametrize("password", [
        "short",
        "averagelengthpassword",
        "very-long-password-with-special-chars-!@#$%^&*()",
        "password with spaces",
        "пароль",  # Unicode
        "🔐🔑",    # Emoji
    ])
    def test_various_password_formats(self, password):
        """Test hashing various password formats."""
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True


class TestJWTTokens:
    """Test JWT token functionality."""
    
    def test_create_access_token(self):
        """Test creating access token."""
        user_id = 123
        token = create_access_token({"sub": str(user_id)})
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_decode_valid_token(self):
        """Test decoding valid token."""
        user_id = 456
        token = create_access_token(
            {"sub": str(user_id)},
            expires_delta=timedelta(minutes=15)
        )
        payload = decode_access_token(token)
        assert payload["sub"] == str(user_id)
    
    def test_decode_expired_token(self):
        """Test decoding expired token."""
        token = create_access_token(
            {"sub": "123"},
            expires_delta=timedelta(minutes=-1)  # Already expired
        )
        with pytest.raises(Exception):  # Should raise token expired error
            decode_access_token(token)
```

### Integration Test Example
```python
# tests/integration/api/test_auth.py
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.main import app
from backend.models.user import User
from backend.core.security import get_password_hash


@pytest.mark.asyncio
class TestAuthEndpoints:
    """Test authentication endpoints."""
    
    async def test_login_success(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User
    ):
        """Test successful login."""
        response = await async_client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "testpassword123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    async def test_login_invalid_credentials(
        self,
        async_client: AsyncClient,
        test_user: User
    ):
        """Test login with invalid credentials."""
        response = await async_client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Incorrect username or password"
    
    async def test_protected_route_with_token(
        self,
        async_client: AsyncClient,
        auth_headers: dict
    ):
        """Test accessing protected route with valid token."""
        response = await async_client.get(
            "/api/v1/users/me",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert "id" in data
    
    async def test_protected_route_without_token(
        self,
        async_client: AsyncClient
    ):
        """Test accessing protected route without token."""
        response = await async_client.get("/api/v1/users/me")
        assert response.status_code == 401
```

### Async Test Fixtures
```python
# tests/conftest.py
import asyncio
import pytest
from typing import AsyncGenerator, Generator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from backend.main import app
from backend.db.base import Base
from backend.models.user import User
from backend.core.security import get_password_hash


# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://test:test@localhost/test_db"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def engine():
    """Create test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    """Create database session for tests."""
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create async HTTP client."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create test user."""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("testpassword123"),
        is_active=True,
        is_verified=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def auth_headers(async_client: AsyncClient, test_user: User) -> dict:
    """Get authentication headers."""
    response = await async_client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user.email,
            "password": "testpassword123"
        }
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
```

## Test Coverage

### Coverage Configuration
```ini
# .coveragerc
[run]
source = backend
omit = 
    */tests/*
    */migrations/*
    */__init__.py
    */conftest.py

[report]
precision = 2
show_missing = True
skip_covered = False

[html]
directory = htmlcov

[xml]
output = coverage.xml
```

### Coverage Goals
- **Overall**: > 80%
- **Core modules**: > 90%
- **API endpoints**: > 85%
- **Business logic**: > 90%
- **Models**: > 80%
- **Utilities**: > 75%

### Running Coverage
```bash
# Generate HTML report
pytest --cov=backend --cov-report=html
open htmlcov/index.html

# Generate terminal report
pytest --cov=backend --cov-report=term-missing

# Generate XML for CI
pytest --cov=backend --cov-report=xml

# Check specific module
pytest --cov=backend.core.security tests/unit/core/test_security.py
```

## Performance Testing

### Load Testing with Locust
```python
# tests/performance/locustfile.py
from locust import HttpUser, task, between
import random


class PlatformUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login before running tasks."""
        response = self.client.post("/api/v1/auth/login", json={
            "username": "loadtest@example.com",
            "password": "loadtest123"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(3)
    def view_courses(self):
        """View course list."""
        self.client.get("/api/v1/courses", headers=self.headers)
    
    @task(2)
    def view_course_detail(self):
        """View specific course."""
        course_id = random.randint(1, 10)
        self.client.get(f"/api/v1/courses/{course_id}", headers=self.headers)
    
    @task(1)
    def view_profile(self):
        """View user profile."""
        self.client.get("/api/v1/users/me", headers=self.headers)


class AdminUser(HttpUser):
    wait_time = between(2, 5)
    
    @task
    def view_analytics(self):
        """View analytics dashboard."""
        self.client.get("/api/v1/analytics/dashboard", headers=self.headers)
    
    @task
    def generate_report(self):
        """Generate compliance report."""
        self.client.get("/api/v1/reports/compliance/gdpr", headers=self.headers)
```

### Running Load Tests
```bash
# Run with web UI
locust -f tests/performance/locustfile.py --host=http://localhost:8000

# Run headless
locust -f tests/performance/locustfile.py \
    --host=http://localhost:8000 \
    --users=100 \
    --spawn-rate=10 \
    --run-time=5m \
    --headless
```

## Security Testing

### SQL Injection Tests
```python
# tests/security/test_sql_injection.py
import pytest
from httpx import AsyncClient


@pytest.mark.security
class TestSQLInjection:
    """Test for SQL injection vulnerabilities."""
    
    @pytest.mark.parametrize("payload", [
        "'; DROP TABLE users; --",
        "1' OR '1'='1",
        "admin'--",
        "1' UNION SELECT * FROM users--",
        "' OR 1=1--",
    ])
    async def test_login_sql_injection(
        self,
        async_client: AsyncClient,
        payload: str
    ):
        """Test login endpoint for SQL injection."""
        response = await async_client.post(
            "/api/v1/auth/login",
            data={
                "username": payload,
                "password": payload
            }
        )
        # Should return 401, not 500 (SQL error)
        assert response.status_code == 401
        # Should not leak database information
        assert "syntax" not in response.text.lower()
        assert "sql" not in response.text.lower()
```

### Authentication Tests
```python
# tests/security/test_authentication.py
import pytest
import jwt
from datetime import datetime, timedelta
from httpx import AsyncClient


@pytest.mark.security
class TestAuthentication:
    """Test authentication security."""
    
    async def test_jwt_token_expiration(
        self,
        async_client: AsyncClient,
        test_user
    ):
        """Test that expired tokens are rejected."""
        # Create expired token
        expired_token = jwt.encode(
            {
                "sub": str(test_user.id),
                "exp": datetime.utcnow() - timedelta(hours=1)
            },
            "secret",
            algorithm="HS256"
        )
        
        response = await async_client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        assert response.status_code == 401
    
    async def test_invalid_token_signature(
        self,
        async_client: AsyncClient,
        test_user
    ):
        """Test that tokens with invalid signatures are rejected."""
        # Create token with wrong secret
        invalid_token = jwt.encode(
            {
                "sub": str(test_user.id),
                "exp": datetime.utcnow() + timedelta(hours=1)
            },
            "wrong-secret",
            algorithm="HS256"
        )
        
        response = await async_client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {invalid_token}"}
        )
        assert response.status_code == 401
```

## E2E Testing

### User Journey Tests
```python
# tests/e2e/test_user_journey.py
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.e2e
class TestUserJourney:
    """Test complete user journeys."""
    
    async def test_new_user_registration_and_course_completion(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test new user registration through course completion."""
        # 1. Register new user
        register_response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "SecurePass123!",
                "full_name": "New User"
            }
        )
        assert register_response.status_code == 201
        user_id = register_response.json()["id"]
        
        # 2. Verify email
        # (In real scenario, extract token from email)
        verify_response = await async_client.post(
            f"/api/v1/auth/verify-email",
            json={"user_id": user_id, "token": "mock-token"}
        )
        assert verify_response.status_code == 200
        
        # 3. Login
        login_response = await async_client.post(
            "/api/v1/auth/login",
            data={
                "username": "newuser@example.com",
                "password": "SecurePass123!"
            }
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 4. Browse courses
        courses_response = await async_client.get(
            "/api/v1/courses",
            headers=headers
        )
        assert courses_response.status_code == 200
        courses = courses_response.json()
        assert len(courses) > 0
        course_id = courses[0]["id"]
        
        # 5. Enroll in course
        enroll_response = await async_client.post(
            f"/api/v1/courses/{course_id}/enroll",
            headers=headers
        )
        assert enroll_response.status_code == 200
        
        # 6. Complete course modules
        for module_num in range(1, 4):
            progress_response = await async_client.post(
                f"/api/v1/courses/{course_id}/progress",
                json={"module": module_num, "completed": True},
                headers=headers
            )
            assert progress_response.status_code == 200
        
        # 7. Take quiz
        quiz_response = await async_client.post(
            f"/api/v1/courses/{course_id}/quiz/submit",
            json={
                "answers": [
                    {"question_id": 1, "answer": "A"},
                    {"question_id": 2, "answer": "B"},
                    {"question_id": 3, "answer": "C"}
                ]
            },
            headers=headers
        )
        assert quiz_response.status_code == 200
        assert quiz_response.json()["passed"] is True
        
        # 8. Download certificate
        cert_response = await async_client.get(
            f"/api/v1/courses/{course_id}/certificate",
            headers=headers
        )
        assert cert_response.status_code == 200
        assert cert_response.headers["content-type"] == "application/pdf"
```

## CI/CD Integration

### GitHub Actions Configuration
```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:6
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Cache dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements*.txt') }}
        restore-keys: |
          ${{ runner.os }}-pip-
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run linting
      run: |
        black --check .
        isort --check-only .
        flake8 .
        mypy .
    
    - name: Run tests with coverage
      env:
        DATABASE_URL: postgresql+asyncpg://test:test@localhost/test_db
        REDIS_URL: redis://localhost:6379/0
        SECRET_KEY: test-secret-key
      run: |
        pytest --cov=backend --cov-report=xml --cov-report=term
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: true
    
    - name: Run security tests
      run: |
        pytest -m security
    
    - name: Run performance tests
      if: github.event_name == 'push' && github.ref == 'refs/heads/main'
      run: |
        locust -f tests/performance/locustfile.py \
          --host=http://localhost:8000 \
          --users=50 \
          --spawn-rate=5 \
          --run-time=2m \
          --headless \
          --only-summary
```

## Best Practices

### 1. Test Naming
```python
# Good test names
def test_user_can_login_with_valid_credentials():
def test_password_reset_expires_after_24_hours():
def test_admin_can_view_all_users():

# Bad test names
def test_login():
def test_password():
def test_admin():
```

### 2. Test Independence
```python
# Good - Independent test
async def test_create_user(db_session):
    user = User(email="test@example.com", ...)
    db_session.add(user)
    await db_session.commit()
    assert user.id is not None

# Bad - Dependent on external state
async def test_create_user():
    # Assumes user doesn't exist
    user = User(email="admin@example.com", ...)  # Might fail
```

### 3. Mock External Services
```python
# Good - Mock external service
@patch('backend.services.email.send_email')
async def test_password_reset(mock_send_email):
    mock_send_email.return_value = True
    # Test password reset without sending real email

# Bad - Real external call
async def test_password_reset():
    # Actually sends email - slow and unreliable
```

### 4. Use Factories
```python
# tests/factories.py
import factory
from backend.models.user import User


class UserFactory(factory.Factory):
    class Meta:
        model = User
    
    email = factory.Faker('email')
    username = factory.Faker('user_name')
    full_name = factory.Faker('name')
    is_active = True
    is_verified = True
    
    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        if extracted:
            obj.set_password(extracted)


# Usage in tests
def test_user_creation():
    user = UserFactory(email="specific@example.com")
    assert user.email == "specific@example.com"
```

### 5. Test Data Builders
```python
class CourseBuilder:
    def __init__(self):
        self.course = {
            "title": "Default Course",
            "description": "Default description",
            "duration_hours": 1
        }
    
    def with_title(self, title):
        self.course["title"] = title
        return self
    
    def with_modules(self, count):
        self.course["modules"] = [
            {"title": f"Module {i}", "order": i}
            for i in range(1, count + 1)
        ]
        return self
    
    def build(self):
        return self.course


# Usage
course_data = (CourseBuilder()
    .with_title("Advanced Security")
    .with_modules(5)
    .build())
```

### 6. Assertion Messages
```python
# Good - Clear assertion messages
def test_password_requirements():
    password = "weak"
    result = validate_password(password)
    assert result.is_valid is False, (
        f"Password '{password}' should be invalid but was accepted. "
        f"Errors: {result.errors}"
    )

# Bad - No context on failure
def test_password_requirements():
    assert validate_password("weak").is_valid is False
```

## Testing Checklist

### Before Committing
- [ ] All tests pass locally
- [ ] Coverage meets minimum requirements
- [ ] No hardcoded test data
- [ ] No disabled/skipped tests without explanation
- [ ] New features have corresponding tests
- [ ] Bug fixes have regression tests

### Test Review
- [ ] Tests are readable and self-documenting
- [ ] Tests cover happy path and edge cases
- [ ] Tests are independent
- [ ] Tests use appropriate fixtures
- [ ] Tests follow naming conventions
- [ ] Performance impact is acceptable

### Continuous Improvement
- [ ] Regularly review and update tests
- [ ] Remove obsolete tests
- [ ] Refactor complex test setups
- [ ] Monitor test execution time
- [ ] Track flaky tests
- [ ] Update test documentation

---

For more information on specific testing scenarios or advanced testing techniques, please refer to the official documentation or contact the development team.