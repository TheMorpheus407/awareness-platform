# Login Functionality Analysis Report

## Executive Summary

The login functionality has multiple implementations causing confusion:

1. **Test Server** (`test_server.py`) - Uses JSON format with a custom endpoint
2. **Main Application** (`main.py` + `api/routes/auth.py`) - Uses OAuth2 form data format
3. **Database Field Mismatch** - Test DB uses `hashed_password`, main app uses `password_hash`

## Current State

### 1. Running Server
Currently, the **test server** is running on port 8000, which:
- Accepts JSON login requests at `/api/v1/auth/login`
- Uses SQLite database with `hashed_password` field
- Works with the credentials: `admin@bootstrap-academy.com` / `admin123`

### 2. Main Application Login Endpoint
The production-ready endpoint in `api/routes/auth.py`:
- Uses `OAuth2PasswordRequestForm` which expects **form data**, not JSON
- Expects fields: `username` (containing email) and `password`
- Database model uses `password_hash` field, not `hashed_password`

## Root Causes of Login Issues

### 1. **Content-Type Mismatch**
- Frontend sends: `application/json`
- Main backend expects: `application/x-www-form-urlencoded`

### 2. **Field Name Inconsistencies**
- Test DB: `hashed_password`
- Main app model: `password_hash`
- OAuth2 form: `username` (not `email`)

### 3. **Multiple Implementations**
- Test server accepts JSON with `email`/`password`
- Main app expects form data with `username`/`password`

## Working Login Examples

### Test Server (Currently Running)
```bash
# JSON format - WORKS
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@bootstrap-academy.com","password":"admin123"}'
```

### Main Application (When Running)
```bash
# Form data format - REQUIRED
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@bootstrap-academy.com&password=admin123"
```

## Recommendations

### Option 1: Modify Main App to Accept JSON (Recommended)
Add a JSON-compatible login endpoint alongside the OAuth2 endpoint:

```python
@router.post("/login/json", response_model=TokenResponse)
async def login_json(
    login_data: LoginRequest,  # Pydantic model expecting JSON
    db: AsyncSession = Depends(get_db),
    request: Request = None,
) -> TokenResponse:
    # Implementation similar to OAuth2 endpoint but accepts JSON
```

### Option 2: Update Frontend to Send Form Data
Modify frontend to send form-encoded data instead of JSON:
```javascript
const formData = new URLSearchParams();
formData.append('username', email);
formData.append('password', password);

fetch('/api/v1/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  body: formData
});
```

### Option 3: Use a Request Union Type
Modify the existing endpoint to accept both formats:
```python
from fastapi import Form, Body
from typing import Union

@router.post("/login")
async def login(
    form_data: Optional[OAuth2PasswordRequestForm] = None,
    json_data: Optional[LoginRequest] = None,
    db: AsyncSession = Depends(get_db),
):
    if json_data:
        username = json_data.email
        password = json_data.password
    elif form_data:
        username = form_data.username
        password = form_data.password
    else:
        raise HTTPException(status_code=400, detail="No login data provided")
```

## Database Schema Alignment

Ensure consistent field naming:
- Use `password_hash` everywhere (as defined in the User model)
- Update test database creation scripts
- Align all migration scripts

## CORS Configuration

Current CORS settings in `core/config.py`:
- Allows `http://localhost:3000` by default
- Credentials are allowed
- All standard HTTP methods are permitted

This should work for local development.

## Testing Strategy

1. **Unit Tests**: Update `tests/api/routes/test_auth.py` to test both formats
2. **Integration Tests**: Create end-to-end tests with actual frontend
3. **Database Tests**: Ensure field names are consistent across all environments

## Immediate Fix

To get login working immediately with the main application:

1. Stop the test server
2. Start the main application with proper database
3. Ensure frontend sends form-encoded data OR
4. Add a JSON endpoint to the main application

## Security Considerations

1. The OAuth2 form data approach is standard and secure
2. JSON login is also acceptable if properly implemented
3. Always use HTTPS in production
4. Implement rate limiting on login endpoints
5. Add proper logging for failed login attempts