# Test Framework Documentation

## Overview

This document describes the custom test framework for the Awareness Platform, replacing SonarQube with a comprehensive in-house testing solution.

## Test Structure

```
tests/
├── unit/           # Fast, isolated unit tests
├── integration/    # Tests with external dependencies
├── api/           # API endpoint tests
├── security/      # Security-focused tests
├── performance/   # Performance benchmarks
└── fixtures/      # Shared test fixtures
```

## Test Categories

### 1. Unit Tests (`@pytest.mark.unit`)
- Fast, isolated tests
- No external dependencies
- Mock all I/O operations
- Target: < 1 second per test

### 2. Integration Tests (`@pytest.mark.integration`)
- Test component interactions
- May use test database
- May make network calls
- Target: < 5 seconds per test

### 3. API Tests (`@pytest.mark.api`)
- Test REST endpoints
- Full request/response cycle
- Authentication/authorization
- Input validation

### 4. Security Tests (`@pytest.mark.security`)
- SQL injection prevention
- XSS protection
- Authentication bypass attempts
- Rate limiting verification

### 5. Critical Tests (`@pytest.mark.critical`)
- Core business logic
- Must pass for deployment
- High priority fixes

## Running Tests

### Basic Commands

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific category
pytest -m unit
pytest -m integration
pytest -m "not slow"

# Run specific file
pytest tests/api/test_auth.py

# Run with verbose output
pytest -vv

# Stop on first failure
pytest -x

# Run in parallel (requires pytest-xdist)
pytest -n 4
```

### Using the Test Runner

```bash
# Run unit tests only
python run_tests.py --unit

# Run with coverage and HTML report
python run_tests.py --coverage --html

# Quick test run (skip slow tests)
python run_tests.py --quick

# Run security tests
python run_tests.py --security

# Run specific tests
python run_tests.py tests/api/test_auth.py
```

## Writing Tests

### Test File Structure

```python
import pytest
from unittest.mock import Mock, patch

@pytest.mark.unit
class TestUserService:
    """Test user service functionality."""
    
    @pytest.fixture
    def user_service(self):
        """Create a user service instance."""
        return UserService()
    
    def test_create_user_success(self, user_service):
        """Test successful user creation."""
        # Arrange
        user_data = {"email": "test@example.com", "password": "secure123"}
        
        # Act
        user = user_service.create_user(user_data)
        
        # Assert
        assert user.email == "test@example.com"
        assert user.id is not None
```

### Best Practices

1. **Test Naming**: Use descriptive names that explain what is being tested
   - ✅ `test_login_with_invalid_password_returns_401`
   - ❌ `test_login_fail`

2. **Arrange-Act-Assert**: Structure tests clearly
   ```python
   def test_example():
       # Arrange: Set up test data
       data = {"key": "value"}
       
       # Act: Perform the action
       result = process_data(data)
       
       # Assert: Verify the outcome
       assert result.status == "success"
   ```

3. **Use Fixtures**: Share common setup
   ```python
   @pytest.fixture
   def authenticated_client(client, user):
       client.force_authenticate(user)
       return client
   ```

4. **Mock External Dependencies**
   ```python
   @patch('app.services.email.send_email')
   def test_send_notification(mock_send):
       # Test without actually sending emails
       notify_user(user_id=1)
       mock_send.assert_called_once()
   ```

## Coverage Requirements

### Minimum Coverage Thresholds
- Overall: 70%
- Critical paths: 90%
- API endpoints: 80%
- Business logic: 85%
- Utilities: 60%

### Coverage Exclusions
- Database migrations
- Configuration files
- Test files themselves
- Third-party integrations (mocked)

## CI/CD Integration

Tests are automatically run in the CI/CD pipeline:

1. **Pull Requests**: All tests must pass
2. **Pre-deployment**: Critical tests must pass
3. **Post-deployment**: Smoke tests verify deployment

### Pipeline Stages

```yaml
test:
  - lint (flake8, black)
  - type-check (mypy)
  - unit-tests
  - integration-tests
  - security-scan
  - coverage-check
```

## Test Data Management

### Fixtures
- Use `conftest.py` for shared fixtures
- Create minimal, focused test data
- Clean up after tests

### Database
- Use transactions for isolation
- Reset sequences between tests
- Use factory patterns for complex data

## Performance Testing

### Benchmarks
```python
@pytest.mark.performance
def test_api_response_time(client):
    start = time.time()
    response = client.get('/api/users')
    duration = time.time() - start
    
    assert response.status_code == 200
    assert duration < 0.1  # 100ms threshold
```

### Load Testing
- Use `locust` for load testing
- Define user scenarios
- Monitor resource usage

## Security Testing

### Common Security Tests
1. SQL Injection
2. XSS Prevention
3. CSRF Protection
4. Authentication Bypass
5. Authorization Checks
6. Rate Limiting

### Example Security Test
```python
@pytest.mark.security
def test_sql_injection_prevention(client):
    # Attempt SQL injection
    malicious_input = "'; DROP TABLE users; --"
    response = client.get(f'/api/users?search={malicious_input}')
    
    # Should handle safely
    assert response.status_code in [200, 400]
    # Verify users table still exists
    assert User.query.count() > 0
```

## Debugging Tests

### Useful Commands
```bash
# Run with debugger
pytest --pdb

# Show print statements
pytest -s

# Show local variables on failure
pytest -l

# Generate detailed HTML report
pytest --html=report.html --self-contained-html
```

### VS Code Integration
```json
{
    "python.testing.pytestEnabled": true,
    "python.testing.unittestEnabled": false,
    "python.testing.pytestArgs": [
        "tests"
    ]
}
```

## Continuous Improvement

1. **Review test failures**: Identify flaky tests
2. **Monitor coverage**: Increase coverage over time
3. **Performance metrics**: Track test execution time
4. **Test quality**: Ensure tests are meaningful

## Migration from SonarQube

### What We Replaced
- Code coverage analysis → pytest-cov
- Code quality checks → flake8, mypy, bandit
- Security scanning → bandit, custom security tests
- Duplication detection → flake8 plugins
- Complexity analysis → radon (optional)

### Advantages
- No external dependencies
- Faster feedback loop
- Customizable rules
- Integrated with development workflow
- Cost-effective

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- [Python testing best practices](https://realpython.com/pytest-python-testing/)
- [Test-Driven Development](https://testdriven.io/)