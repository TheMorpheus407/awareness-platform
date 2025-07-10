# Backend Authentication Tests

This directory contains comprehensive tests for the authentication system.

## Test Structure

### Main Test Files

- `test_auth.py` - Comprehensive authentication tests including:
  - Login endpoint tests (with form data)
  - 2FA authentication tests
  - Registration tests
  - User profile management tests
  - Password change tests
  - Session management tests

- `conftest.py` - Pytest configuration and fixtures:
  - Database session fixtures
  - Test client fixtures
  - User and company test data fixtures
  - Authentication header fixtures

## Running Tests

### Prerequisites

1. Install test dependencies:
```bash
pip install -r requirements-dev.txt
```

2. Ensure you have a test database configured or use SQLite (default for tests)

### Running All Authentication Tests

```bash
# From the backend directory
python -m pytest tests/test_auth.py -v

# Or use the provided script
./run_auth_tests.sh
```

### Running Specific Test Classes

```bash
# Test only login functionality
python -m pytest tests/test_auth.py::TestLoginEndpoint -v

# Test only 2FA functionality
python -m pytest tests/test_auth.py::TestLoginWith2FA -v

# Test only registration
python -m pytest tests/test_auth.py::TestRegistration -v
```

### Running with Coverage

```bash
python -m pytest tests/test_auth.py -v --cov=api.routes.auth --cov=core.security --cov-report=term-missing
```

## Test Scenarios Covered

### Login Tests
- ✅ Valid credentials with form data (OAuth2 format)
- ✅ Invalid email
- ✅ Invalid password
- ✅ Inactive user
- ✅ Case-insensitive email
- ✅ Last login timestamp update
- ✅ JSON body rejection (OAuth2 requires form data)

### 2FA Tests
- ✅ Login with 2FA returns temporary token
- ✅ Complete 2FA with valid TOTP code
- ✅ Invalid TOTP code handling
- ✅ Backup code usage

### Registration Tests
- ✅ New company and admin user creation
- ✅ Duplicate email prevention
- ✅ Data validation

### User Management Tests
- ✅ Get current user profile
- ✅ Authentication required
- ✅ Invalid token handling

### Password Management Tests
- ✅ Change password with correct current password
- ✅ Reject wrong current password
- ✅ Password confirmation matching

### Session Management Tests
- ✅ Logout functionality
- ✅ Session history retrieval

## Important Notes

1. **OAuth2 Form Data**: The login endpoint expects form-encoded data, not JSON. This is standard for OAuth2 password flow.

2. **Test Isolation**: Each test is isolated with its own database transaction that's rolled back after the test.

3. **Fixtures**: The `conftest.py` file provides reusable fixtures for common test data like users, companies, and authentication headers.

4. **2FA Testing**: Tests include proper TOTP generation and validation using the actual 2FA implementation.

## Troubleshooting

If tests fail, check:

1. Database connection settings in test environment
2. All required dependencies are installed
3. The backend application can be imported correctly
4. No conflicting environment variables

## Adding New Tests

When adding new authentication tests:

1. Use the existing test classes as templates
2. Leverage the fixtures from `conftest.py`
3. Ensure proper test isolation
4. Test both success and failure cases
5. Use descriptive test names that explain what's being tested