# Single Source of Truth - Cybersecurity Awareness Platform

## 🎯 Project Overview

**Project Name**: Cybersecurity Awareness Platform  
**Company**: Bootstrap Academy GmbH  
**Domain**: https://bootstrap-awareness.de  
**Status**: Production Deployment Phase (60% operational)

## 📁 Project Structure

```
AwarenessSchulungen/
├── README.md                    # Main project documentation
├── SOURCE_OF_TRUTH.md          # This file - single source of truth
├── CREDENTIALS.md              # All access credentials (secure!)
├── ROADMAP.md                  # Development roadmap
├── todo.md                     # Current tasks and progress
├── .env.example                # Environment variables template
│
├── backend/                    # FastAPI backend
│   ├── alembic/               # Database migrations
│   ├── api/                   # API endpoints
│   ├── core/                  # Core functionality
│   ├── models/                # Database models
│   ├── schemas/               # Pydantic schemas
│   ├── services/              # Business logic
│   ├── tests/                 # Backend tests
│   ├── main.py               # Application entry
│   ├── requirements.txt       # Python dependencies
│   └── Dockerfile            # Backend container
│
├── frontend/                   # React frontend
│   ├── public/                # Static assets
│   ├── src/                   # Source code
│   ├── package.json          # Node dependencies
│   └── Dockerfile           # Frontend container
│
├── infrastructure/            # Deployment configs
│   ├── docker/               # Docker configurations
│   ├── nginx/                # Web server configs
│   ├── scripts/              # Deployment scripts
│   └── kubernetes/           # K8s manifests
│
└── docs/                     # All documentation
    ├── api/                  # API documentation
    ├── guides/               # User/admin guides
    ├── legal/                # Legal documents
    └── technical/            # Technical specs
```

## 🚀 Technology Stack

### Backend
- **Framework**: FastAPI 0.104.1 (Python 3.11+)
- **Database**: PostgreSQL 15 with Row-Level Security
- **ORM**: SQLAlchemy 2.0
- **Cache**: Redis 7
- **Queue**: Celery with Redis broker
- **Authentication**: JWT with refresh tokens + 2FA

### Frontend
- **Framework**: React 18.2 with TypeScript 5.2
- **Styling**: Tailwind CSS 3.3
- **State**: Zustand 4.4
- **HTTP Client**: Axios 1.6
- **Build**: Vite 5.0
- **Testing**: Vitest + React Testing Library

### Infrastructure
- **Container**: Docker 24.0
- **Orchestration**: Docker Compose / Kubernetes
- **Web Server**: Nginx 1.24
- **CI/CD**: GitHub Actions
- **Monitoring**: Prometheus + Grafana
- **SSL**: Let's Encrypt

## 📊 Project Status

### ✅ Completed
1. Backend API structure with FastAPI
2. Database models and migrations
3. Authentication system with JWT + 2FA
4. User and company management
5. Docker configuration
6. Basic frontend structure
7. CI/CD pipeline setup
8. Production server provisioned

### 🚧 In Progress
1. Frontend UI completion
2. Course management system
3. Phishing simulation engine
4. Email campaign system
5. Analytics dashboard
6. Payment integration

### 📅 Planned
1. Advanced reporting
2. Mobile applications
3. SSO integration
4. Multi-language support
5. Advanced analytics
6. Partner portal

## 🔐 Access Information

See `CREDENTIALS.md` for all access credentials including:
- SSH keys and server access
- Database passwords
- API keys and secrets
- GitHub repository access
- Email service credentials

## 🚀 Deployment

### Local Development
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

### Production Deployment
```bash
# Automated via GitHub Actions
git push origin main

# Manual deployment
ssh -i "bootstrap-awareness private key.txt" root@83.228.205.20
cd /opt/awareness-platform
git pull
docker-compose -f docker-compose.prod.yml up -d
```

## 📋 Key Decisions

1. **FastAPI over Django**: Better performance, modern async support
2. **PostgreSQL with RLS**: Multi-tenant security at database level
3. **React over Vue**: Larger ecosystem, better TypeScript support
4. **Docker Compose**: Simpler than K8s for current scale
5. **GitHub Actions**: Native CI/CD with good Docker support

## 🔄 Development Workflow

1. Create feature branch from `main`
2. Implement feature with tests
3. Create pull request
4. Pass CI checks (tests, linting, security)
5. Code review by team
6. Merge to main (auto-deploys)

## 📞 Contact

- **Technical Lead**: TheMorpheus407
- **Email**: hallo@bootstrap-awareness.de
- **GitHub**: https://github.com/TheMorpheus407/awareness-platform

## 🚨 Important Notes

1. This is the ONLY source of truth for project information
2. All other documentation should reference this file
3. Keep this file updated with any major changes
4. Credentials file is separate for security
5. Legal documents in docs/legal/ are authoritative

---

Last Updated: 2025-07-09  
Version: 1.0.0