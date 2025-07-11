# CSRF Protection Implementation

## Overview

This document describes the Cross-Site Request Forgery (CSRF) protection implementation for the Cybersecurity Awareness Platform. The implementation follows security best practices and is based on the pattern from issue #209.

## Backend Implementation

### CSRF Middleware

The CSRF protection is implemented as a FastAPI middleware in `/backend/core/middleware.py`:

```python
class CSRFMiddleware(BaseHTTPMiddleware):
    """CSRF protection middleware for FastAPI."""
```

#### Key Features:

1. **Token Generation**: Uses `secrets.token_urlsafe()` for cryptographically secure tokens
2. **Token Signing**: Tokens are signed with HMAC-SHA256 using the application's secret key
3. **Cookie-based Storage**: CSRF tokens are stored in secure, httpOnly cookies
4. **Header Validation**: Validates CSRF tokens sent in the `X-CSRF-Token` header
5. **Automatic Token Rotation**: New tokens are generated for new sessions

#### Configuration:

- **Cookie Name**: `csrf_token`
- **Header Name**: `X-CSRF-Token`
- **Token Lifetime**: 24 hours
- **Safe Methods**: GET, HEAD, OPTIONS, TRACE (no CSRF check)
- **Excluded Paths**: 
  - `/api/health`
  - `/api/health/db`
  - `/api/docs`
  - `/api/v1/auth/login`
  - `/api/v1/auth/register`

### Endpoint for Token Retrieval

A dedicated endpoint is available at `/api/v1/auth/csrf-token` to retrieve the current CSRF token:

```python
@router.get("/csrf-token")
async def get_csrf_token(request: Request) -> dict:
    """Get CSRF token for the current session."""
    return {
        "csrf_token": csrf_token,
        "header_name": "X-CSRF-Token",
        "cookie_name": "csrf_token"
    }
```

## Frontend Implementation

### API Client Integration

The frontend API client (`/frontend/src/services/api.ts`) automatically handles CSRF tokens:

#### Automatic Token Management:

1. **Initialization**: Fetches CSRF token on client initialization
2. **Request Interceptor**: Automatically adds CSRF token to state-changing requests
3. **Response Interceptor**: Updates CSRF token from response headers
4. **Error Handling**: Automatically refreshes token on 403 CSRF errors and retries request

#### Implementation Details:

```typescript
// Request interceptor adds CSRF token to state-changing requests
if (isStateChangingMethod && !isExcludedPath && this.csrfToken) {
  config.headers['X-CSRF-Token'] = this.csrfToken;
}
```

#### Token Refresh on Login:

The CSRF token is automatically refreshed after successful login to ensure session consistency:

```typescript
// Refresh CSRF token after successful login
await this.fetchCsrfToken();
```

## Security Considerations

1. **Token Validation**: All tokens are cryptographically signed and verified
2. **Secure Cookies**: In production, cookies use the `Secure` flag (HTTPS only)
3. **SameSite Policy**: Cookies use `SameSite=Strict` to prevent CSRF attacks
4. **HttpOnly Cookies**: Prevents JavaScript access to the signed token
5. **Token Rotation**: New tokens for new sessions prevent token fixation

## Testing

### Manual Testing

Use the provided test script to verify CSRF protection:

```bash
cd backend
python test_csrf.py
```

### Expected Behavior:

1. **GET Requests**: Should work without CSRF token
2. **POST/PUT/DELETE without token**: Should return 403 Forbidden
3. **POST/PUT/DELETE with valid token**: Should be processed normally
4. **Excluded endpoints**: Should work without CSRF token

## Integration Guide

### For New Endpoints

No special configuration needed! The middleware automatically protects all state-changing endpoints.

To exclude an endpoint from CSRF protection, add it to the `exclude_paths` in `main.py`:

```python
exclude_paths={
    "/api/v1/your-endpoint",
    # ... other excluded paths
}
```

### For Frontend Developers

The API client handles CSRF tokens automatically. Just use the API client normally:

```typescript
// CSRF token is automatically included
await api.post('/api/v1/users', userData);
await api.put('/api/v1/users/123', updateData);
await api.delete('/api/v1/users/123');
```

## Troubleshooting

### Common Issues:

1. **403 CSRF token missing**: Ensure the frontend is using the API client
2. **403 CSRF token invalid**: Token may have expired, client will auto-refresh
3. **Cookie not set**: Check CORS configuration allows credentials

### Debug Mode:

Enable debug logging to see CSRF token validation:

```python
logger.warning(f"CSRF token mismatch for {request.method} {request.url.path}")
```

## Compliance

This implementation addresses the security requirements from issue #209 and follows OWASP guidelines for CSRF protection.