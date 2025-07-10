# API Versioning Strategy

## Overview
This document outlines the API versioning strategy for the Cybersecurity Awareness Platform, ensuring backward compatibility, smooth transitions, and clear communication of changes to API consumers.

## Table of Contents
1. [Versioning Principles](#versioning-principles)
2. [Versioning Scheme](#versioning-scheme)
3. [Implementation Approach](#implementation-approach)
4. [Version Lifecycle](#version-lifecycle)
5. [Breaking Changes](#breaking-changes)
6. [Migration Guidelines](#migration-guidelines)
7. [Documentation Standards](#documentation-standards)
8. [Client Best Practices](#client-best-practices)

## Versioning Principles

### Core Principles
1. **Backward Compatibility**: Existing clients should continue to work
2. **Clear Communication**: Changes must be well-documented
3. **Graceful Deprecation**: Provide migration paths and timelines
4. **Semantic Versioning**: Use meaningful version numbers
5. **Minimal Versions**: Avoid version proliferation

### When to Version
- **DO version** when making breaking changes
- **DON'T version** for backward-compatible changes
- **DO version** when changing core behavior
- **DON'T version** for bug fixes or performance improvements

## Versioning Scheme

### URL Path Versioning
We use URL path versioning for clarity and simplicity:
```
https://api.cybersec-platform.de/api/v1/users
https://api.cybersec-platform.de/api/v2/users
```

### Version Format
- **Major Version Only**: `v1`, `v2`, `v3`
- **No Minor Versions**: Use feature flags instead
- **Beta Versions**: `v2-beta` for preview features

### Version Structure
```python
# FastAPI implementation
from fastapi import APIRouter

# Version 1 router
v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(auth_v1.router, prefix="/auth", tags=["auth-v1"])
v1_router.include_router(users_v1.router, prefix="/users", tags=["users-v1"])

# Version 2 router
v2_router = APIRouter(prefix="/api/v2")
v2_router.include_router(auth_v2.router, prefix="/auth", tags=["auth-v2"])
v2_router.include_router(users_v2.router, prefix="/users", tags=["users-v2"])

# Main app
app.include_router(v1_router)
app.include_router(v2_router)
```

## Implementation Approach

### 1. Router Organization
```
api/
├── v1/
│   ├── __init__.py
│   ├── auth.py
│   ├── users.py
│   ├── courses.py
│   └── schemas.py
├── v2/
│   ├── __init__.py
│   ├── auth.py
│   ├── users.py
│   ├── courses.py
│   └── schemas.py
└── common/
    ├── dependencies.py
    ├── exceptions.py
    └── utils.py
```

### 2. Shared Logic Pattern
```python
# api/common/business_logic.py
class UserService:
    """Shared business logic across versions."""
    
    async def get_user(self, user_id: int) -> User:
        # Common implementation
        return await db.get(User, user_id)
    
    async def update_user_v1(self, user_id: int, data: UserUpdateV1):
        # V1 specific logic
        pass
    
    async def update_user_v2(self, user_id: int, data: UserUpdateV2):
        # V2 specific logic with new fields
        pass

# api/v1/users.py
@router.put("/{user_id}")
async def update_user(
    user_id: int,
    data: UserUpdateV1,
    service: UserService = Depends()
):
    return await service.update_user_v1(user_id, data)

# api/v2/users.py
@router.put("/{user_id}")
async def update_user(
    user_id: int,
    data: UserUpdateV2,
    service: UserService = Depends()
):
    return await service.update_user_v2(user_id, data)
```

### 3. Schema Versioning
```python
# api/v1/schemas.py
class UserResponseV1(BaseModel):
    id: int
    email: str
    name: str
    created_at: datetime

# api/v2/schemas.py
class UserResponseV2(BaseModel):
    id: int
    email: str
    full_name: str  # Renamed from 'name'
    display_name: str  # New field
    created_at: datetime
    last_login: Optional[datetime]  # New field
    
    @field_validator('full_name', mode='before')
    def handle_legacy_name(cls, v, values):
        # Handle old 'name' field for backward compatibility
        if 'name' in values:
            return values['name']
        return v
```

### 4. Database Compatibility Layer
```python
# core/compatibility.py
class CompatibilityLayer:
    """Handle version differences at data layer."""
    
    @staticmethod
    def user_to_v1(user: User) -> dict:
        return {
            "id": user.id,
            "email": user.email,
            "name": user.full_name,  # Map to old field name
            "created_at": user.created_at
        }
    
    @staticmethod
    def user_to_v2(user: User) -> dict:
        return {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "display_name": user.display_name,
            "created_at": user.created_at,
            "last_login": user.last_login
        }
```

## Version Lifecycle

### 1. Version States
```yaml
versions:
  v1:
    state: deprecated
    release_date: 2023-01-01
    deprecation_date: 2024-01-01
    sunset_date: 2024-07-01
    
  v2:
    state: current
    release_date: 2024-01-01
    deprecation_date: null
    sunset_date: null
    
  v3:
    state: beta
    release_date: 2024-06-01
    deprecation_date: null
    sunset_date: null
```

### 2. Lifecycle Stages
1. **Beta**: New version available for testing
2. **Current**: Recommended version for new implementations
3. **Deprecated**: Still functional but not recommended
4. **Sunset**: No longer available

### 3. Timeline Requirements
- **Beta Period**: Minimum 3 months
- **Deprecation Notice**: Minimum 6 months
- **Sunset Notice**: Minimum 12 months
- **Support Overlap**: At least 2 versions

## Breaking Changes

### What Constitutes a Breaking Change
1. **Removing fields** from responses
2. **Changing field types** (string to number)
3. **Renaming fields** without aliases
4. **Changing authentication** methods
5. **Removing endpoints**
6. **Changing error formats**
7. **Modifying pagination** structure

### Non-Breaking Changes
1. **Adding optional fields** to requests
2. **Adding fields** to responses
3. **Adding new endpoints**
4. **Adding new optional parameters**
5. **Deprecating fields** (with continued support)

### Breaking Change Process
```python
# 1. Announce deprecation
@router.get("/old-endpoint", deprecated=True)
async def old_endpoint():
    """
    Deprecated: Use /new-endpoint instead.
    This endpoint will be removed in v2.
    """
    warnings.warn(
        "This endpoint is deprecated. Use /new-endpoint",
        DeprecationWarning
    )
    return {"message": "This endpoint is deprecated"}

# 2. Add deprecation headers
@router.get("/users/{user_id}")
async def get_user(response: Response):
    response.headers["Deprecation"] = "true"
    response.headers["Sunset"] = "2024-07-01"
    response.headers["Link"] = '</api/v2/users/{user_id}>; rel="successor-version"'
    return user

# 3. Log usage for monitoring
@router.middleware("http")
async def log_deprecated_usage(request: Request, call_next):
    if "/api/v1/" in request.url.path:
        logger.warning(f"Deprecated API call: {request.url.path}")
    response = await call_next(request)
    return response
```

## Migration Guidelines

### 1. Version Migration Headers
```python
class VersionMiddleware:
    """Add version information to responses."""
    
    async def __call__(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add version headers
        response.headers["API-Version"] = "v2"
        response.headers["API-Deprecated-Versions"] = "v1"
        response.headers["API-Supported-Versions"] = "v1,v2"
        
        # Add migration hints
        if "/api/v1/" in request.url.path:
            response.headers["API-Migration-Guide"] = "https://docs.api.com/migration/v1-to-v2"
        
        return response
```

### 2. Gradual Migration Support
```python
# Support both old and new field names
class FlexibleSchema(BaseModel):
    """Schema that accepts both v1 and v2 field names."""
    
    # V2 field names (canonical)
    full_name: str
    phone_number: str
    
    # Accept v1 field names
    @field_validator('full_name', mode='before')
    def accept_name_field(cls, v, info):
        if 'name' in info.data:
            return info.data['name']
        return v
    
    @field_validator('phone_number', mode='before')
    def accept_phone_field(cls, v, info):
        if 'phone' in info.data:
            return info.data['phone']
        return v
```

### 3. Migration Tools
```python
# tools/api_migration_validator.py
class MigrationValidator:
    """Validate API responses across versions."""
    
    async def validate_compatibility(self, endpoint: str, params: dict):
        # Get responses from both versions
        v1_response = await client.get(f"/api/v1{endpoint}", params=params)
        v2_response = await client.get(f"/api/v2{endpoint}", params=params)
        
        # Check critical fields are present
        v1_data = v1_response.json()
        v2_data = v2_response.json()
        
        # Validate mapping
        assert v1_data["id"] == v2_data["id"]
        assert v1_data["name"] == v2_data["full_name"]
        
        return True
```

## Documentation Standards

### 1. OpenAPI Documentation
```python
# Separate docs per version
@app.get("/api/v1/openapi.json", include_in_schema=False)
async def get_v1_openapi():
    return get_openapi(
        title="Cybersec API",
        version="1.0.0",
        description="API Version 1 - Deprecated",
        routes=app.routes,
        servers=[{"url": "/api/v1"}]
    )

@app.get("/api/v2/openapi.json", include_in_schema=False)
async def get_v2_openapi():
    return get_openapi(
        title="Cybersec API",
        version="2.0.0",
        description="API Version 2 - Current",
        routes=app.routes,
        servers=[{"url": "/api/v2"}]
    )
```

### 2. Migration Documentation Template
```markdown
# Migration Guide: v1 to v2

## Overview
This guide helps you migrate from API v1 to v2.

## Breaking Changes

### 1. User Endpoint Changes
- **Field Renamed**: `name` → `full_name`
- **New Required Field**: `display_name`
- **Response Format**: Pagination structure changed

#### Before (v1):
```json
{
  "id": 123,
  "name": "John Doe",
  "email": "john@example.com"
}
```

#### After (v2):
```json
{
  "id": 123,
  "full_name": "John Doe",
  "display_name": "John",
  "email": "john@example.com",
  "last_login": "2024-01-15T10:00:00Z"
}
```

### 2. Authentication Changes
- JWT token expiry reduced from 7 days to 24 hours
- Refresh token rotation implemented

## Migration Steps

1. Update client libraries to latest version
2. Update field mappings in your code
3. Test with v2-beta endpoint
4. Switch production traffic to v2
5. Remove v1 code after verification
```

### 3. Changelog Format
```markdown
# API Changelog

## [2.0.0] - 2024-01-01

### Breaking Changes
- Renamed `name` field to `full_name` in user responses
- Changed pagination format to use `cursor` instead of `offset`
- Removed deprecated `/api/v1/legacy` endpoints

### Added
- New `display_name` field in user responses
- Webhook support for real-time updates
- GraphQL endpoint at `/graphql`

### Fixed
- Rate limiting now properly resets at midnight UTC
- Unicode handling in search queries

### Deprecated
- `/api/v2/old-search` endpoint (use `/api/v2/search` instead)
```

## Client Best Practices

### 1. Version Detection
```javascript
// JavaScript client example
class APIClient {
  constructor(baseURL) {
    this.baseURL = baseURL;
    this.version = null;
  }
  
  async detectVersion() {
    const response = await fetch(`${this.baseURL}/api/version`);
    const data = await response.json();
    this.version = data.current_version;
    return this.version;
  }
  
  async request(endpoint, options = {}) {
    const version = this.version || 'v2';  // Default to latest
    const url = `${this.baseURL}/api/${version}${endpoint}`;
    
    const response = await fetch(url, {
      ...options,
      headers: {
        ...options.headers,
        'Accept': `application/vnd.api+json; version=${version}`,
        'API-Client-Version': '2.0.0'
      }
    });
    
    // Check for deprecation warnings
    if (response.headers.get('Deprecation') === 'true') {
      console.warn(`API endpoint deprecated. Sunset: ${response.headers.get('Sunset')}`);
    }
    
    return response;
  }
}
```

### 2. Graceful Degradation
```python
# Python client example
class APIClient:
    def __init__(self, base_url, preferred_version='v2'):
        self.base_url = base_url
        self.preferred_version = preferred_version
        self.fallback_versions = ['v1']
    
    async def get_user(self, user_id):
        # Try preferred version first
        try:
            response = await self._request(
                f'/users/{user_id}',
                version=self.preferred_version
            )
            return self._normalize_user_v2(response)
        except VersionNotSupported:
            # Fall back to older version
            for version in self.fallback_versions:
                try:
                    response = await self._request(
                        f'/users/{user_id}',
                        version=version
                    )
                    return self._normalize_user_v1(response)
                except VersionNotSupported:
                    continue
            raise Exception("No supported API version available")
    
    def _normalize_user_v1(self, data):
        """Normalize v1 response to internal format."""
        return {
            'id': data['id'],
            'full_name': data['name'],  # Map old field
            'email': data['email']
        }
    
    def _normalize_user_v2(self, data):
        """Normalize v2 response to internal format."""
        return {
            'id': data['id'],
            'full_name': data['full_name'],
            'email': data['email'],
            'display_name': data.get('display_name', data['full_name'])
        }
```

### 3. Version-Specific Error Handling
```typescript
// TypeScript client example
interface APIError {
  code: string;
  message: string;
  details?: any;
}

class VersionAwareClient {
  async handleResponse(response: Response, version: string): Promise<any> {
    if (!response.ok) {
      const error = await this.parseError(response, version);
      throw new APIException(error);
    }
    return response.json();
  }
  
  async parseError(response: Response, version: string): Promise<APIError> {
    const data = await response.json();
    
    // Handle version-specific error formats
    switch (version) {
      case 'v1':
        return {
          code: data.error_code || 'UNKNOWN',
          message: data.error_message || 'Unknown error',
          details: data.error_details
        };
      
      case 'v2':
        return {
          code: data.error?.code || 'UNKNOWN',
          message: data.error?.message || 'Unknown error',
          details: data.error?.details
        };
      
      default:
        return {
          code: 'UNKNOWN',
          message: 'Unknown error format'
        };
    }
  }
}
```

## Implementation Checklist

### New Version Release
- [ ] Create new version directory structure
- [ ] Implement version-specific routes
- [ ] Update schemas for new version
- [ ] Add compatibility layer for data mapping
- [ ] Create migration documentation
- [ ] Update OpenAPI specifications
- [ ] Add version detection endpoint
- [ ] Implement deprecation warnings
- [ ] Update client libraries
- [ ] Test backward compatibility
- [ ] Set up monitoring for version usage
- [ ] Plan deprecation timeline
- [ ] Notify API consumers
- [ ] Update public documentation
- [ ] Create migration tools/scripts

### Version Deprecation
- [ ] Add deprecation headers to responses
- [ ] Update documentation with sunset date
- [ ] Send deprecation notices to users
- [ ] Monitor usage metrics
- [ ] Provide migration support
- [ ] Create automated migration tools
- [ ] Set up redirect rules
- [ ] Plan sunset date
- [ ] Remove version after sunset

---

For questions about API versioning or migration support, contact the API team or refer to the developer portal.