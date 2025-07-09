# Cybersecurity Awareness Platform

A comprehensive cybersecurity training platform designed to enhance organizational security awareness through interactive courses, phishing simulations, and compliance reporting.

## 🎯 Current Project Status

**Development Stage**: Production Deployment (60% operational)
**Last Updated**: 2025-07-09

### What's Working ✅
- Complete frontend with landing page, authentication, user/company management
- Backend API structure with FastAPI
- Database models and migrations
- Docker configuration and all containers running in production
- German/English internationalization
- Comprehensive documentation
- SSL certificate active (https://bootstrap-awareness.de)
- CI/CD pipeline fixed with fallback logic (commit: a45f0f3)
- Code pushed to GitHub repository

### What's Not Working ❌
- Frontend displays Vite template instead of application (GitHub Issue #9)
- API routes return 404 except /api/health (GitHub Issue #10)
- Database not initialized in production
- Missing monitoring and observability
- No automated backups or disaster recovery

See [STAGE_1_ACTUAL_STATUS.md](STAGE_1_ACTUAL_STATUS.md) for detailed status.

## ✨ Planned Features

### Training & Education
- Interactive video-based cybersecurity training
- Adaptive learning paths based on role and performance
- Multi-language support (currently DE/EN)
- Progress tracking and analytics
- Automated certificate generation

### Phishing Simulations (Stage 2)
- Customizable phishing email templates
- Automated campaign scheduling
- Educational feedback on clicks
- Risk scoring and analytics
- Targeted training assignment

### Compliance & Reporting
- Support for NIS-2, DSGVO/GDPR, ISO 27001, TISAX
- Automated compliance report generation
- Complete audit trails
- Executive dashboards
- Multiple export formats

### Enterprise Features
- Multi-tenant architecture with data isolation
- Role-based access control (RBAC)
- Two-factor authentication (2FA)
- RESTful API for integrations
- Customizable branding

## 🚀 Getting Started

### Prerequisites

- Docker & Docker Compose
- OR manual setup:
  - Python 3.11+
  - Node.js 20+ and npm 10+
  - PostgreSQL 15+

### Quick Start with Docker

```bash
# Clone repository
git clone https://github.com/TheMorpheus407/awareness-platform.git
cd awareness-platform

# Copy environment files
cp backend/.env.example backend/.env

# Start all services
docker-compose -f backend/docker-compose.dev.yml up -d

# Run database migrations (note the backend/backend structure)
docker-compose -f backend/docker-compose.dev.yml exec backend bash -c "cd /app/backend && alembic upgrade head"

# Create initial admin user
docker-compose -f backend/docker-compose.dev.yml exec backend bash -c "cd /app/backend && python backend/scripts/create_admin.py"

# Access the application
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000/docs
```

## 🏗️ Architecture

### Technology Stack

#### Backend
- **Framework**: FastAPI (Python 3.11)
- **Database**: PostgreSQL 15 with Row-Level Security
- **ORM**: SQLAlchemy 2.0
- **Authentication**: JWT with refresh tokens
- **API Documentation**: OpenAPI/Swagger

#### Frontend
- **Framework**: React 18 with TypeScript
- **State Management**: Zustand
- **Styling**: Tailwind CSS
- **Build Tool**: Vite
- **Testing**: Vitest (configured but not working)
- **Internationalization**: i18next

#### Infrastructure
- **Containerization**: Docker & Docker Compose
- **CI/CD**: GitHub Actions (configured but not tested)
- **Web Server**: Nginx (for frontend)

### System Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  React Frontend │────▶│  FastAPI Backend│────▶│  PostgreSQL DB  │
│   (Port 5173)   │     │   (Port 8000)  │     │   (with RLS)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## 🔒 Security

### Implemented Security Features
- PostgreSQL Row-Level Security for multi-tenancy
- JWT authentication with refresh tokens
- Two-Factor Authentication (2FA) with TOTP
- Role-Based Access Control (RBAC)
- Input validation and sanitization
- CORS configuration
- Rate limiting

### Security Gaps
- No penetration testing performed
- Security scanning not verified
- Missing intrusion detection
- No security monitoring

## 📖 Documentation

### Available Documentation
- [Contributing Guidelines](backend/CONTRIBUTING.md)
- [Deployment Guide](backend/DEPLOYMENT_GUIDE.md)
- [Current Status Report](CURRENT_STATUS.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)
- [Production Status](PRODUCTION_STATUS.md)
- [Stage 1 Status Report](STAGE_1_ACTUAL_STATUS.md)
- API Documentation at `/api/docs` when backend is running

### Technical Specifications
- [Backend Specification](backend/backend-spec.md)
- [Frontend Specification](backend/frontend-spec.md)
- [Database Specification](backend/database-spec.md)
- [Security Specification](backend/security-spec.md)
- [Testing Specification](backend/testing-spec.md)

### Backend Documentation
- [Backend README](backend/README.md)
- [Backend Development](backend/backend/README.md)
- [RLS Implementation](backend/backend/docs/ROW_LEVEL_SECURITY.md)
- [2FA Testing Guide](backend/backend/docs/2FA_TESTING.md)

## 🧪 Testing

### Current Testing Status
⚠️ **Tests are not currently working**

```bash
# Backend tests (fail - dependencies not installed)
cd backend
pytest

# Frontend tests (hang/timeout)
cd frontend
npm test

# E2E tests (no test files exist)
npm run e2e
```

### Testing Goals
- Backend: 80% coverage target
- Frontend: 75% coverage target
- E2E: Critical user flows

## 🚢 Deployment

### Current Deployment Status
- ✅ Local development environment works
- ✅ Docker Compose configurations created and deployed
- ✅ Production server active at https://bootstrap-awareness.de (83.228.205.20)
- ✅ GitHub Actions workflows fixed with fallback logic
- ✅ Code pushed to GitHub repository (TheMorpheus407/awareness-platform)
- ⚠️ Frontend showing Vite template (needs fix)
- ⚠️ API routes need database initialization

### Deployment Environments
- **Development**: Local Docker Compose
- **Production**: To be verified

See [Deployment Guide](DEPLOYMENT_GUIDE.md) for instructions.

## 📊 Performance

### Current Performance
- Frontend bundle size: 1.2MB (optimized)
- API response time: <150ms (claimed, not verified)
- No load testing performed
- No performance monitoring in place

## 🌍 Internationalization

Currently supported languages:
- 🇩🇪 German (de)
- 🇬🇧 English (en)

Full UI translation implemented with i18next.

## 📄 License

This project is proprietary software owned by Bootstrap Academy GmbH. All rights reserved.

## 🏢 About Bootstrap Academy GmbH

Bootstrap Academy GmbH provides cybersecurity awareness training solutions. The platform is currently under development.

---

**Note**: This README reflects the actual current state of the project. For marketing materials or feature promises, please refer to other documentation.