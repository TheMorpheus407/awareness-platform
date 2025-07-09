# Backend Structure Documentation

## Overview
This document provides a comprehensive overview of the backend structure, including all modules, their responsibilities, and how they interact.

## Directory Structure

```
backend/
├── alembic/                 # Database migrations
│   ├── versions/           # Migration files
│   └── env.py             # Alembic configuration
│
├── api/                    # API layer
│   ├── __init__.py        # API router initialization
│   ├── dependencies/      # Common dependencies
│   │   ├── auth.py       # Authentication dependencies
│   │   └── common.py     # Pagination, DB session
│   └── routes/           # API endpoints
│       ├── auth.py       # Authentication endpoints
│       ├── users.py      # User management
│       ├── courses.py    # Course endpoints
│       ├── phishing.py   # Phishing simulations
│       └── ...          # Other route modules
│
├── core/                   # Core functionality
│   ├── config.py         # Settings management
│   ├── security.py       # Security utilities
│   ├── middleware.py     # Custom middleware
│   ├── logging.py        # Logging configuration
│   ├── cache.py         # Redis cache
│   ├── exceptions.py    # Custom exceptions
│   └── ...             # Other core modules
│
├── models/                # Database models
│   ├── base.py          # Base model classes
│   ├── user.py          # User model
│   ├── company.py       # Company model
│   ├── course.py        # Course-related models
│   └── ...             # Other models
│
├── schemas/              # Pydantic schemas
│   ├── base.py         # Base schemas
│   ├── user.py         # User schemas
│   ├── company.py      # Company schemas
│   └── ...            # Other schemas
│
├── services/            # Business logic
│   ├── email.py        # Email service
│   ├── phishing_service.py  # Phishing logic
│   ├── stripe_service.py    # Payment processing
│   └── ...                 # Other services
│
├── scripts/             # Utility scripts
│   ├── create_admin.py # Create admin user
│   ├── seed_data.py   # Seed test data
│   └── ...           # Other scripts
│
├── tests/              # Test suite
│   ├── conftest.py    # Test configuration
│   ├── api/          # API tests
│   ├── models/       # Model tests
│   └── ...          # Other tests
│
├── db/                # Database utilities
│   ├── base.py       # Model imports
│   └── session.py    # Session management
│
├── main.py           # Application entry point
├── requirements.txt  # Python dependencies
├── .env.example     # Environment template
└── README.md        # Documentation
```

## Module Responsibilities

### Core Layer (`core/`)
- **config.py**: Centralized configuration using pydantic-settings
- **security.py**: Password hashing, JWT tokens, authentication
- **middleware.py**: Request processing, security headers, rate limiting
- **logging.py**: Structured logging with loguru
- **cache.py**: Redis caching functionality
- **exceptions.py**: Application-specific exceptions
- **monitoring.py**: Sentry and Prometheus integration
- **rls.py**: Row-level security implementation
- **two_factor_auth.py**: TOTP-based 2FA

### API Layer (`api/`)
- **routes/**: RESTful endpoints following OpenAPI specification
- **dependencies/**: Reusable dependencies for authentication, pagination
- Handles HTTP requests/responses
- Input validation using Pydantic schemas
- Authentication and authorization checks

### Models Layer (`models/`)
- SQLAlchemy ORM models
- Database schema definitions
- Relationships and constraints
- Base classes with common functionality (timestamps, soft deletes)

### Schemas Layer (`schemas/`)
- Pydantic models for request/response validation
- Data transformation and serialization
- Input validation rules
- API documentation generation

### Services Layer (`services/`)
- Business logic implementation
- External service integrations (Stripe, AWS, SMTP)
- Complex operations and workflows
- Decoupled from API layer

### Database Layer (`db/`)
- **base.py**: Imports all models for Alembic
- **session.py**: Async database session management

## Key Features

### Authentication & Security
- JWT-based authentication with refresh tokens
- Two-factor authentication (TOTP)
- Role-based access control (RBAC)
- Row-level security for multi-tenancy
- Password policies and secure reset

### API Design
- RESTful design principles
- Consistent error responses
- Pagination support
- Rate limiting
- CORS configuration

### Database
- PostgreSQL with async support
- Alembic migrations
- Connection pooling
- Soft deletes
- Audit logging

### External Integrations
- Stripe for payments
- AWS S3 for content storage
- SMTP/SendGrid for emails
- Redis for caching
- Sentry for error tracking
- Prometheus for metrics

## Import Convention

All imports use absolute paths from the backend root:

```python
# Correct
from core.config import settings
from models.user import User
from schemas.user import UserCreate
from services.email import EmailService

# Incorrect
from .config import settings  # Relative import
from backend.core.config import settings  # Includes 'backend'
```

## Configuration

Environment variables are managed through:
1. `.env` file (development)
2. Environment variables (production)
3. `core.config.Settings` class validates and provides defaults

Key configuration areas:
- Application settings
- Database connection
- Redis connection
- Email configuration
- AWS credentials
- Stripe keys
- Security settings

## Testing

Tests are organized by module:
- `tests/api/` - API endpoint tests
- `tests/models/` - Model tests
- `tests/services/` - Service tests
- `tests/core/` - Core functionality tests

Run tests with: `pytest`

## Development Workflow

1. **Adding a new feature**:
   - Create/update model in `models/`
   - Create/update schema in `schemas/`
   - Implement business logic in `services/`
   - Create API endpoint in `api/routes/`
   - Add tests
   - Update documentation

2. **Database changes**:
   - Modify model
   - Generate migration: `alembic revision --autogenerate -m "description"`
   - Review and apply: `alembic upgrade head`

3. **API changes**:
   - Update route implementation
   - Update schema
   - Update API documentation
   - Add/update tests

## Security Considerations

- All passwords are hashed using bcrypt
- JWT tokens have expiration
- Rate limiting on sensitive endpoints
- Input validation on all endpoints
- SQL injection prevention via ORM
- XSS prevention via proper encoding
- CORS restricted to allowed origins
- Security headers in all responses

## Performance Optimizations

- Async/await throughout
- Database connection pooling
- Redis caching for frequent queries
- Pagination for large datasets
- Lazy loading relationships
- Batch operations where possible
- CDN for static content

## Monitoring & Logging

- Structured JSON logging
- Request ID tracking
- Performance metrics (Prometheus)
- Error tracking (Sentry)
- Health check endpoints
- Database query logging (development)

## Deployment

The backend is designed to be deployed as:
- Docker container
- Kubernetes deployment
- Traditional server with systemd

Key considerations:
- Environment-specific configuration
- Database migrations on startup
- Health checks for orchestration
- Graceful shutdown handling
- Log aggregation
- Metric collection

## Future Enhancements

Planned improvements:
- GraphQL API option
- WebSocket support for real-time updates
- More comprehensive caching strategy
- Event-driven architecture with message queues
- Microservices split for scaling
- Enhanced monitoring and alerting