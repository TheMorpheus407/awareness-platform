# Single Source of Truth - Bootstrap Awareness Platform

**Last Updated**: 2025-07-09  
**Repository**: https://github.com/TheMorpheus407/awareness-platform  
**Production URL**: https://bootstrap-awareness.de

## Current Production Status

### Overall Status: **Partially Operational (55%)**

| Component | Status | Notes |
|-----------|--------|-------|
| Infrastructure | ✅ Running | All Docker containers healthy |
| SSL Certificate | ✅ Valid | Let's Encrypt configured |
| Frontend | ❌ Broken | Shows Vite template instead of app |
| Backend API | ⚠️ Partial | Only /api/health endpoint works |
| Database | ❌ Not Initialized | Tables need creation |
| CI/CD Pipeline | ✅ Working | With pytest workaround |

### Known Issues

1. **Frontend Display Issue**
   - **Problem**: Site shows "Vite + React" template instead of the awareness platform
   - **Impact**: Users cannot access the application
   - **GitHub Issue**: #9

2. **API Routes Not Working**
   - **Problem**: All endpoints except `/api/health` return 404
   - **Cause**: Database not initialized, routes may not be registered
   - **GitHub Issue**: #10

3. **Database Not Initialized**
   - **Problem**: Database tables have not been created
   - **Required Actions**:
     - Run migrations: `alembic upgrade head`
     - Initialize tables: `python scripts/init_db_tables.py`
     - Create admin user: `python scripts/create_admin_user.py`

## How to Deploy

### Prerequisites
- GitHub repository access
- GitHub Actions secrets configured (see below)
- SSH access to production server (83.228.205.20)

### Step 1: Push Code to GitHub
```bash
# The code is already in the repository
git push origin main
```

### Step 2: GitHub Actions will Automatically Deploy
- Monitor at: https://github.com/TheMorpheus407/awareness-platform/actions
- The pipeline runs tests, builds Docker images, and deploys to production

### Step 3: Initialize Database (One-time Setup)
```bash
# SSH to server
ssh root@bootstrap-awareness.de

# Run migrations
docker exec -it backend-container alembic upgrade head

# Initialize tables
docker exec -it backend-container python scripts/init_db_tables.py

# Create admin user
docker exec -it backend-container python scripts/create_admin_user.py
```

### Required GitHub Secrets
Configure at: https://github.com/TheMorpheus407/awareness-platform/settings/secrets/actions

- `SSH_PRIVATE_KEY` - SSH key for server access
- `DB_PASSWORD` - PostgreSQL password
- `SECRET_KEY` - Application secret key
- `JWT_SECRET_KEY` - JWT signing key
- `REDIS_PASSWORD` - Redis password

## How to Develop

### Local Development Setup
```bash
# Clone repository
git clone https://github.com/TheMorpheus407/awareness-platform.git
cd awareness-platform

# Start with Docker Compose
docker-compose -f docker-compose.dev.yml up -d

# Access:
# - Frontend: http://localhost:5173
# - Backend API: http://localhost:8000/docs
```

### Manual Setup (Without Docker)
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## Architecture Overview

### Technology Stack

**Backend**
- FastAPI (Python 3.11)
- PostgreSQL 15 with Row-Level Security
- SQLAlchemy 2.0
- JWT Authentication with 2FA
- Redis for caching

**Frontend**
- React 18 with TypeScript
- Vite build tool
- Tailwind CSS
- i18next (German/English)
- Zustand state management

**Infrastructure**
- Docker & Docker Compose
- Nginx reverse proxy
- GitHub Actions CI/CD
- Let's Encrypt SSL

### System Architecture
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  React Frontend │────▶│  FastAPI Backend│────▶│  PostgreSQL DB  │
│  (Nginx:80/443) │     │   (Port 8000)  │     │   (with RLS)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │   Redis Cache   │
                        │   (Port 6379)   │
                        └─────────────────┘
```

## Key Features

### Implemented ✅
- User authentication with 2FA
- Multi-tenant isolation (Row-Level Security)
- Company and user management
- Role-based access control (RBAC)
- German/English internationalization
- API documentation (Swagger/OpenAPI)

### Planned (Stage 2) 🚧
- Interactive cybersecurity training courses
- Phishing simulation campaigns
- Compliance reporting (NIS-2, GDPR, ISO 27001)
- Analytics and dashboards
- Certificate generation
- Payment processing

## Contact & Support

- **Company**: Bootstrap Academy GmbH
- **Support Email**: hallo@bootstrap-awareness.de
- **GitHub Issues**: https://github.com/TheMorpheus407/awareness-platform/issues

## Critical Next Steps

1. **Fix Frontend Display** - Investigate nginx configuration and build artifacts
2. **Initialize Database** - Run migrations and create initial data
3. **Fix API Routes** - Ensure all endpoints are properly registered
4. **Enable Monitoring** - Set up error tracking and performance monitoring
5. **Configure Backups** - Implement automated database backups

---

⚠️ **Note**: This document reflects the actual current state as of 2025-07-09. The platform is NOT fully operational and requires the fixes listed above before it can serve customers.