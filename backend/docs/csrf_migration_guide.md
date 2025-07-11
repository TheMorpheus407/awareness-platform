# CSRF Protection Migration Guide

## Overview

This guide provides step-by-step instructions for enabling CSRF protection in existing deployments of the Cybersecurity Awareness Platform.

## Backend Migration Steps

### 1. Update Dependencies

No new dependencies are required. The implementation uses only standard Python libraries.

### 2. Deploy Backend Changes

The CSRF middleware is automatically enabled when you deploy the updated `main.py` and `middleware.py` files.

### 3. Configuration

The CSRF middleware uses the existing `SECRET_KEY` from your environment configuration. Ensure this is properly set in production.

### 4. Verify Deployment

After deployment, verify CSRF protection is active:

```bash
# Test CSRF token endpoint
curl -X GET https://your-domain.com/api/v1/auth/csrf-token

# Expected response:
{
  "csrf_token": "...",
  "header_name": "X-CSRF-Token",
  "cookie_name": "csrf_token"
}
```

## Frontend Migration Steps

### 1. Deploy Frontend Changes

Deploy the updated `api.ts` file which includes automatic CSRF token handling.

### 2. Clear Browser Cache

Instruct users to clear their browser cache or perform a hard refresh (Ctrl+F5) to ensure they get the updated JavaScript.

### 3. Verify Integration

The frontend will automatically:
- Fetch CSRF token on initialization
- Include token in all state-changing requests
- Handle token refresh on 403 errors

## Rollback Plan

If issues arise, you can temporarily disable CSRF protection:

### Option 1: Remove Middleware (Quick Fix)

Comment out the CSRF middleware in `main.py`:

```python
# app.add_middleware(
#     CSRFMiddleware,
#     ...
# )
```

### Option 2: Disable for Specific Endpoints

Add problematic endpoints to the `exclude_paths`:

```python
exclude_paths={
    "/api/v1/problematic-endpoint",
    # ... other excluded paths
}
```

## Testing in Staging

Before production deployment:

1. Deploy to staging environment
2. Run the test script: `python test_csrf.py`
3. Test all critical user flows
4. Monitor logs for CSRF-related errors

## Monitoring

After deployment, monitor for:

1. **403 Errors**: Check logs for "CSRF token missing" or "CSRF token invalid"
2. **User Reports**: Watch for users unable to perform actions
3. **API Metrics**: Monitor for increased 403 response rates

## Common Issues and Solutions

### Issue: Mobile Apps Failing

**Symptom**: Mobile applications receiving 403 errors

**Solution**: 
- Update mobile apps to fetch and include CSRF tokens
- Temporarily exclude mobile API endpoints from CSRF protection

### Issue: Third-Party Integrations

**Symptom**: Webhook or API integrations failing

**Solution**:
- Add integration endpoints to `exclude_paths`
- Or implement API key authentication for these endpoints

### Issue: Session Timeout

**Symptom**: Users getting CSRF errors after long idle periods

**Solution**:
- The frontend automatically refreshes tokens on 403 errors
- Ensure users are on the latest frontend version

## Performance Considerations

The CSRF implementation has minimal performance impact:
- Token generation: < 1ms
- Token validation: < 1ms
- Cookie overhead: ~100 bytes per request

## Security Notes

1. **Token Rotation**: Tokens are rotated on new sessions
2. **Secure Cookies**: In production, cookies use Secure flag (HTTPS only)
3. **SameSite Policy**: Strict SameSite prevents cross-origin attacks
4. **Token Signing**: All tokens are cryptographically signed

## Timeline

Recommended deployment timeline:

1. **Week 1**: Deploy to staging, test thoroughly
2. **Week 2**: Deploy to production with monitoring
3. **Week 3**: Remove any temporary exclusions
4. **Week 4**: Full CSRF protection active

## Support

For issues or questions:
1. Check logs for CSRF-related warnings
2. Run the test script for diagnostics
3. Review the troubleshooting section in the main documentation