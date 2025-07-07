# Cybersecurity Awareness Platform

A comprehensive, automated cybersecurity training platform designed to enhance organizational security awareness through interactive courses, phishing simulations, and compliance reporting.

## 🎯 Overview

The Cybersecurity Awareness Platform helps organizations improve their security posture by providing:
- Automated security awareness training
- Realistic phishing simulations
- Compliance management and reporting
- Real-time risk analytics
- Multi-tenant SaaS architecture

## ✨ Key Features

### Training & Education
- **Interactive Courses**: Engaging video-based cybersecurity training
- **Adaptive Learning**: Personalized learning paths based on role and performance
- **Multi-language Support**: Full internationalization (DE/EN)
- **Progress Tracking**: Detailed analytics on user engagement and completion
- **Certificates**: Automated certificate generation upon course completion

### Phishing Simulations
- **Realistic Templates**: 50+ customizable phishing email templates
- **Automated Campaigns**: Schedule and automate phishing tests
- **Instant Feedback**: Educational content shown immediately upon clicking
- **Detailed Analytics**: Track click rates, report rates, and risk scores
- **Targeted Training**: Automatic enrollment in training for clicked users

### Compliance & Reporting
- **Regulatory Compliance**: NIS-2, DSGVO/GDPR, ISO 27001, TISAX support
- **Automated Reports**: Generate compliance reports with one click
- **Audit Trails**: Complete logging of all security-relevant activities
- **Executive Dashboards**: Real-time visibility into organizational security posture
- **Export Options**: PDF, Excel, and API access for reports

### Enterprise Features
- **Multi-tenancy**: Complete data isolation between organizations
- **SSO Integration**: SAML 2.0 support for enterprise authentication
- **API Access**: RESTful API for custom integrations
- **White-labeling**: Customizable branding per organization
- **Role-based Access**: Granular permissions system

## 🚀 Getting Started

### Prerequisites

- Docker & Docker Compose (recommended)
- OR manual setup:
  - Python 3.11+
  - Node.js 20+ and npm 10+
  - PostgreSQL 15+
  - Redis 7+

### Quick Start with Docker

```bash
# Clone the repository
git clone https://github.com/bootstrap-academy/AwarenessSchulungen.git
cd AwarenessSchulungen

# Copy environment files
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Start all services
docker-compose -f docker-compose.dev.yml up -d

# Run database migrations
docker-compose exec backend alembic upgrade head

# Create a superuser
docker-compose exec backend python scripts/create_superuser.py

# Access the application
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000/docs
```

### Manual Setup

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed manual setup instructions.

## 🏗️ Architecture

### Technology Stack

#### Backend
- **Framework**: FastAPI (Python 3.11)
- **Database**: PostgreSQL 15 with Row-Level Security
- **ORM**: SQLAlchemy 2.0
- **Cache**: Redis 7
- **Task Queue**: Celery with Redis broker
- **Authentication**: JWT with refresh tokens

#### Frontend
- **Framework**: React 18 with TypeScript
- **State Management**: Zustand
- **Styling**: Tailwind CSS
- **Build Tool**: Vite
- **Testing**: Vitest + React Testing Library
- **Internationalization**: i18next

#### Infrastructure
- **Containerization**: Docker & Docker Compose
- **CI/CD**: GitHub Actions
- **Monitoring**: Prometheus + Grafana
- **Error Tracking**: Sentry
- **Logging**: ELK Stack

### System Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  React Frontend │────▶│  FastAPI Backend│────▶│  PostgreSQL DB  │
│                 │     │                 │     │   (with RLS)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────┐
                        │    Redis    │
                        │   (Cache)   │
                        └─────────────┘
```

## 🔒 Security

### Security Features
- **Data Isolation**: PostgreSQL Row-Level Security for multi-tenancy
- **Encryption**: TLS 1.3 for all communications
- **Authentication**: Secure JWT implementation with refresh tokens
- **Authorization**: Fine-grained RBAC (Role-Based Access Control)
- **Input Validation**: Comprehensive validation at API and database levels
- **Security Headers**: HSTS, CSP, X-Frame-Options, etc.
- **Rate Limiting**: API rate limiting per user/IP
- **Audit Logging**: Complete audit trail of security events

### Security Practices
- OWASP Top 10 compliance
- Regular dependency updates
- Automated security scanning in CI/CD
- Penetration testing (quarterly)
- Security-focused code reviews

## 📖 Documentation

- [Coding Standards](docs/CODING_STANDARDS.md)
- [Development Workflow](docs/DEVELOPMENT_WORKFLOW.md)
- [API Documentation](http://localhost:8000/docs) (when running)
- [Architecture Decision Records](docs/adr/)
- [Database Schema](docs/DATABASE_SCHEMA.md)
- [Deployment Guide](docs/DEPLOYMENT_GUIDE.md)

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details on:
- Code of Conduct
- Development setup
- Coding standards
- Pull request process
- Issue reporting

## 🧪 Testing

### Running Tests

```bash
# Backend tests
cd backend
pytest --cov=app --cov-report=html

# Frontend tests
cd frontend
npm test
npm run test:coverage

# E2E tests
npm run test:e2e
```

### Test Coverage
- Backend: Minimum 80% coverage required
- Frontend: Minimum 75% coverage required
- Critical paths: 100% coverage required

## 🚢 Deployment

### Environments
- **Development**: Automatic deployment from `develop` branch
- **Staging**: Automatic deployment from `release/*` branches
- **Production**: Manual deployment from `main` branch with approval

### Deployment Methods
- Docker Compose (simple deployments)
- Kubernetes (production deployments)
- GitHub Actions CI/CD pipeline

See [Deployment Guide](docs/DEPLOYMENT_GUIDE.md) for detailed instructions.

## 📊 Performance

### Benchmarks
- API Response Time: <200ms (p95)
- Page Load Time: <2s
- Concurrent Users: 10,000+
- Database Queries: <50ms
- Uptime: 99.95% SLA

### Optimization
- Database query optimization with indexes
- Redis caching for frequently accessed data
- CDN for static assets
- Horizontal scaling support

## 🌍 Internationalization

Currently supported languages:
- 🇩🇪 German (de)
- 🇬🇧 English (en)

Adding new languages is straightforward - see [i18n documentation](frontend/src/i18n/README.md).

## 📞 Support

- **Documentation**: See `/docs` directory
- **Issues**: [GitHub Issues](https://github.com/bootstrap-academy/AwarenessSchulungen/issues)
- **Email**: support@bootstrap-academy.com
- **Security Issues**: security@bootstrap-academy.com (PGP available)

## 📄 License

This project is proprietary software owned by Bootstrap Academy GmbH. All rights reserved.

For licensing inquiries, contact: business@bootstrap-academy.com

## 🏢 About Bootstrap Academy GmbH

Bootstrap Academy GmbH is a leading provider of cybersecurity awareness training solutions based in Germany. We help organizations build a strong security culture through engaging training and realistic simulations.

---

Built with ❤️ by Bootstrap Academy GmbH