# Cybersecurity Platform Backend

Production-ready FastAPI backend for the Cybersecurity Awareness Platform.

## Features

- **FastAPI** framework with async support
- **PostgreSQL** database with **SQLAlchemy** ORM
- **JWT Authentication** with access and refresh tokens
- **Alembic** database migrations
- **Pydantic** for data validation
- **Company-based multi-tenancy**
- **Role-based access control** (User, Company Admin, Platform Admin)
- **Comprehensive error handling**
- **Structured logging** with Loguru
- **CORS support**
- **Environment-based configuration**
- **Production-ready security**

## Project Structure

```
backend/
├── alembic/              # Database migrations
├── api/                  # API endpoints
│   ├── routes/          # Route definitions
│   └── dependencies/    # FastAPI dependencies
├── core/                # Core functionality
│   ├── config.py       # Configuration
│   └── security.py     # Security utilities
├── db/                  # Database configuration
├── models/              # SQLAlchemy models
├── schemas/             # Pydantic schemas
├── tests/               # Test suite
├── main.py             # FastAPI application
└── requirements.txt     # Python dependencies
```

## Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Virtual environment tool (venv, virtualenv, etc.)

### Installation

1. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Copy environment template:
```bash
cp .env.template .env
```

4. Configure your `.env` file with appropriate values

5. Run database migrations:
```bash
alembic upgrade head
```

### Running the Application

Development mode:
```bash
python main.py
```

Production mode with Uvicorn:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Documentation

When running in development mode, access:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "Description of changes"
```

Apply migrations:
```bash
alembic upgrade head
```

Rollback one migration:
```bash
alembic downgrade -1
```

## Testing

Run tests:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=. --cov-report=html
```

## Code Quality

Format code:
```bash
black .
isort .
```

Type checking:
```bash
mypy .
```

Linting:
```bash
flake8
```

## Authentication

The API uses JWT tokens for authentication. Here are code examples for each endpoint:

### 1. Register New User
```bash
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "johndoe",
    "password": "SecurePassword123!",
    "full_name": "John Doe",
    "company_id": 1
  }'
```

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "johndoe",
  "full_name": "John Doe",
  "is_active": true,
  "is_verified": false,
  "role": "user",
  "company_id": 1,
  "created_at": "2025-01-07T10:00:00Z"
}
```

### 2. Login
```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user@example.com",
    "password": "SecurePassword123!"
  }'
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### 3. Refresh Token
```bash
curl -X POST "http://localhost:8000/api/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }'
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### 4. Get Current User
```bash
curl -X GET "http://localhost:8000/api/auth/me" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "johndoe",
  "full_name": "John Doe",
  "is_active": true,
  "is_verified": true,
  "role": "user",
  "company": {
    "id": 1,
    "name": "Acme Corp",
    "domain": "acme.com"
  },
  "created_at": "2025-01-07T10:00:00Z",
  "last_login": "2025-01-07T12:00:00Z"
}
```

### 5. Email Verification
```bash
# Request verification email
curl -X POST "http://localhost:8000/api/auth/verify-email/request" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."

# Verify email with token
curl -X POST "http://localhost:8000/api/auth/verify-email/confirm" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "verification-token-from-email"
  }'
```

### 6. Password Reset
```bash
# Request password reset
curl -X POST "http://localhost:8000/api/auth/password-reset/request" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com"
  }'

# Reset password with token
curl -X POST "http://localhost:8000/api/auth/password-reset/confirm" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "reset-token-from-email",
    "new_password": "NewSecurePassword123!"
  }'
```

Include the access token in the Authorization header for protected endpoints:
```
Authorization: Bearer <access_token>
```

## Roles and Permissions

- **User**: Basic access to own profile and company
- **Company Admin**: Manage company and its users
- **Platform Admin**: Full system access

## API Examples

### Company Management

#### List Companies (Admin only)
```bash
curl -X GET "http://localhost:8000/api/companies?page=1&page_size=20" \
  -H "Authorization: Bearer <admin_token>"
```

#### Get Company Details
```bash
curl -X GET "http://localhost:8000/api/companies/1" \
  -H "Authorization: Bearer <access_token>"
```

#### Create Company (Admin only)
```bash
curl -X POST "http://localhost:8000/api/companies" \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "New Company Inc",
    "domain": "newcompany.com",
    "industry": "Technology",
    "size": "50-100"
  }'
```

#### Update Company
```bash
curl -X PUT "http://localhost:8000/api/companies/1" \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Company Inc",
    "industry": "FinTech"
  }'
```

### User Management

#### List Users (Admin/Company Admin)
```bash
curl -X GET "http://localhost:8000/api/users?company_id=1&is_active=true" \
  -H "Authorization: Bearer <admin_token>"
```

#### Get User Details
```bash
curl -X GET "http://localhost:8000/api/users/1" \
  -H "Authorization: Bearer <access_token>"
```

#### Update User
```bash
curl -X PATCH "http://localhost:8000/api/users/1" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Jane Doe",
    "phone": "+1234567890"
  }'
```

#### Deactivate User (Admin only)
```bash
curl -X POST "http://localhost:8000/api/users/1/deactivate" \
  -H "Authorization: Bearer <admin_token>"
```

### Health Checks

#### Basic Health Check
```bash
curl -X GET "http://localhost:8000/health"
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-07T12:00:00Z"
}
```

#### Detailed Health Check
```bash
curl -X GET "http://localhost:8000/api/health/detailed" \
  -H "Authorization: Bearer <access_token>"
```

**Response:**
```json
{
  "status": "healthy",
  "services": {
    "database": "connected",
    "redis": "connected",
    "email": "configured"
  },
  "version": "1.0.0",
  "environment": "production"
}
```

### Error Responses

All endpoints return consistent error responses:

```json
{
  "detail": "Error message here",
  "status_code": 400,
  "type": "validation_error",
  "errors": [
    {
      "field": "email",
      "message": "Invalid email format"
    }
  ]
}
```

Common HTTP status codes:
- `200`: Success
- `201`: Created
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `422`: Validation Error
- `429`: Too Many Requests
- `500`: Internal Server Error

## Environment Variables

Complete list of environment variables with descriptions and examples:

### Application Settings

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `APP_NAME` | Application name | `Cybersecurity Awareness Platform` | `My Platform` |
| `APP_VERSION` | Application version | `1.0.0` | `2.0.0` |
| `DEBUG` | Enable debug mode | `false` | `true` |
| `ENVIRONMENT` | Environment name | `production` | `development`, `staging` |
| `LOG_LEVEL` | Logging level | `INFO` | `DEBUG`, `WARNING`, `ERROR` |

### Server Configuration

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `HOST` | Server host | `0.0.0.0` | `127.0.0.1` |
| `PORT` | Server port | `8000` | `8080` |
| `WORKERS` | Number of workers | `4` | `8` |

### Security

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `SECRET_KEY` | JWT signing key (REQUIRED) | - | `your-256-bit-secret` |
| `ALGORITHM` | JWT algorithm | `HS256` | `HS512` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token expiry | `30` | `60` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token expiry | `7` | `30` |

### Database

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `DATABASE_URL` | PostgreSQL URL (REQUIRED) | - | `postgresql+asyncpg://user:pass@localhost:5432/dbname` |
| `DATABASE_POOL_SIZE` | Connection pool size | `20` | `50` |
| `DATABASE_MAX_OVERFLOW` | Max overflow connections | `0` | `10` |

### CORS Settings

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `CORS_ORIGINS` | Allowed origins | `[]` | `["http://localhost:3000","https://myapp.com"]` |
| `CORS_ALLOW_CREDENTIALS` | Allow credentials | `true` | `false` |
| `CORS_ALLOW_METHODS` | Allowed methods | `["*"]` | `["GET","POST"]` |
| `CORS_ALLOW_HEADERS` | Allowed headers | `["*"]` | `["Authorization","Content-Type"]` |

### Email Configuration

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `SMTP_HOST` | SMTP server host | - | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP server port | `587` | `465` |
| `SMTP_USERNAME` | SMTP username | - | `noreply@myapp.com` |
| `SMTP_PASSWORD` | SMTP password | - | `app-specific-password` |
| `SMTP_FROM_EMAIL` | From email address | - | `noreply@myapp.com` |
| `SMTP_FROM_NAME` | From name | - | `My Platform` |

### External Services

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `SENTRY_DSN` | Sentry error tracking | - | `https://key@sentry.io/project` |
| `REDIS_URL` | Redis connection URL | - | `redis://localhost:6379/0` |
| `YOUTUBE_API_KEY` | YouTube API key | - | `AIza...` |
| `FRONTEND_URL` | Frontend URL (REQUIRED) | - | `http://localhost:3000` |

### Limits and Defaults

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `MAX_UPLOAD_SIZE` | Max file upload size (bytes) | `10485760` (10MB) | `52428800` (50MB) |
| `RATE_LIMIT_PER_MINUTE` | API rate limit | `60` | `100` |
| `DEFAULT_PAGE_SIZE` | Default pagination size | `20` | `50` |
| `MAX_PAGE_SIZE` | Maximum page size | `100` | `200` |

### Generating Secure Values

Generate a secure `SECRET_KEY`:
```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Generate a secure database password:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Security Features

- Password hashing with bcrypt
- JWT token authentication
- CORS protection
- SQL injection prevention via ORM
- Input validation with Pydantic
- Rate limiting ready (configure in production)
- Secure headers (configure reverse proxy)

## Production Deployment

1. Use a process manager (systemd, supervisor)
2. Run behind a reverse proxy (Nginx, Apache)
3. Enable HTTPS
4. Set `DEBUG=false` and `ENVIRONMENT=production`
5. Use a production database
6. Configure logging aggregation
7. Set up monitoring (Prometheus, Grafana)
8. Implement rate limiting
9. Regular security updates

## License

Proprietary - All rights reserved