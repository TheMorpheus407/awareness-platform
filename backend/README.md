# Cybersecurity Awareness Platform - Backend

A comprehensive FastAPI-based backend for cybersecurity awareness training, phishing simulations, and compliance reporting.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 14+
- Redis 6+
- Node.js 18+ (for frontend)

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd backend
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development
```

4. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Set up the database**
```bash
# Create database
createdb cybersec_platform

# Run migrations
alembic upgrade head

# Create initial admin user
python scripts/create_admin.py
```

6. **Run the application**
```bash
# Development
python main.py

# Production
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📁 Project Structure

```
backend/
├── alembic/              # Database migrations
├── api/                  # API routes and dependencies
│   ├── dependencies/     # Common dependencies (auth, pagination)
│   └── routes/          # API endpoints
├── core/                # Core functionality
│   ├── config.py        # Application configuration
│   ├── security.py      # Security utilities
│   ├── middleware.py    # Custom middleware
│   └── ...
├── models/              # SQLAlchemy models
├── schemas/             # Pydantic schemas
├── services/            # Business logic
├── scripts/             # Utility scripts
├── tests/               # Test suite
└── main.py             # Application entry point
```

## 🔑 Key Features

### Authentication & Security
- JWT-based authentication with refresh tokens
- Two-factor authentication (2FA) with TOTP
- Role-based access control (RBAC)
- Row-level security (RLS) for multi-tenancy
- Password policies and secure reset flows
- Email verification

### Training & Compliance
- Interactive video courses with progress tracking
- Quiz system with immediate feedback
- Certificate generation upon completion
- Compliance reporting (NIS2, DSGVO, ISO27001, etc.)
- Multi-language support

### Phishing Simulations
- Template-based phishing campaigns
- Click and report tracking
- Real-time statistics and analytics
- Automated training for clicked users
- Customizable landing pages

### Analytics & Reporting
- Executive dashboards
- Risk score calculations
- Department-level analytics
- Compliance status tracking
- Export to PDF/CSV

### Email Campaigns
- Template management with Jinja2
- Scheduled campaigns with Celery
- Bounce and click tracking
- User preference management

### Payment Integration
- Stripe subscription management
- Multiple pricing tiers
- Usage-based billing
- Invoice generation

## 🛠️ Development

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/api/test_auth.py
```

### Code Quality
```bash
# Format code
black .
isort .

# Lint code
flake8
mypy .

# Pre-commit hooks
pre-commit install
pre-commit run --all-files
```

### Database Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

### API Documentation
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc
- OpenAPI JSON: http://localhost:8000/api/openapi.json

## 🔧 Configuration

### Environment Variables
See `.env.example` for all available configuration options.

### Key Configurations:
- `ENVIRONMENT`: development, staging, production
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `SECRET_KEY`: JWT signing key (generate with `openssl rand -hex 32`)
- `STRIPE_*`: Payment processing configuration
- `AWS_*`: S3/CloudFront configuration for content delivery
- `SMTP_*`: Email server configuration

### Security Best Practices
1. Always use HTTPS in production
2. Set strong SECRET_KEY
3. Enable CORS only for trusted origins
4. Use environment-specific configurations
5. Regular security updates
6. Enable monitoring (Sentry, Prometheus)

## 📊 Monitoring

### Health Checks
- Basic: `GET /health`
- Detailed: `GET /api/health/db`
- Prometheus metrics: `GET /metrics`

### Logging
- Structured JSON logging in production
- Loguru for enhanced debugging
- Sentry integration for error tracking

### Performance
- Redis caching for frequently accessed data
- Database connection pooling
- Async request handling
- CDN integration for static content

## 🚢 Deployment

### Docker
```bash
# Build image
docker build -t cybersec-backend .

# Run container
docker run -p 8000:8000 --env-file .env cybersec-backend
```

### Docker Compose
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend
```

### Production Checklist
- [ ] Set ENVIRONMENT=production
- [ ] Generate strong SECRET_KEY
- [ ] Configure PostgreSQL with connection pooling
- [ ] Set up Redis with persistence
- [ ] Configure reverse proxy (Nginx)
- [ ] Enable HTTPS with valid certificates
- [ ] Set up monitoring (Prometheus, Grafana)
- [ ] Configure backups
- [ ] Set up log aggregation
- [ ] Review security headers

## 📚 API Documentation

See [api-documentation.md](../api-documentation.md) for complete API reference.

### Key Endpoints:
- `POST /api/v1/auth/login` - User authentication
- `GET /api/v1/courses` - List available courses
- `POST /api/v1/phishing/campaigns` - Create phishing campaign
- `GET /api/v1/reports/compliance/{type}` - Generate compliance reports
- `GET /api/v1/users/me` - Get current user profile

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Coding Standards
- Follow PEP 8
- Use type hints
- Write docstrings
- Add tests for new features
- Update documentation

## 📄 License

This project is proprietary software. All rights reserved.

## 🆘 Support

- Documentation: [/docs](../docs/)
- Issues: GitHub Issues
- Email: support@cybersec-platform.de

## 🔄 Changelog

See [CHANGELOG.md](../CHANGELOG.md) for version history.

---

Built with ❤️ using FastAPI, SQLAlchemy, and modern Python best practices.# Trigger Quick Build Test
