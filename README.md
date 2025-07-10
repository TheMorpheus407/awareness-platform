# Cybersecurity Awareness Platform

[![License](https://img.shields.io/badge/license-proprietary-red.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![React](https://img.shields.io/badge/react-18.2-61dafb.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/fastapi-0.104-009688.svg)](https://fastapi.tiangolo.com/)

A comprehensive enterprise platform for cybersecurity awareness training, phishing simulations, and compliance management.

## 🚀 Overview

The Cybersecurity Awareness Platform helps organizations build a strong security culture through:

- **Interactive Training**: Video-based courses with quizzes and certificates
- **Phishing Simulations**: Realistic campaigns to test and educate employees
- **Compliance Management**: NIS-2, GDPR, ISO 27001, and TISAX reporting
- **Analytics Dashboard**: Real-time insights and predictive analytics
- **Multi-tenant Architecture**: Secure data isolation for enterprise use

## 📋 Documentation

For complete project information, see:
- [`SOURCE_OF_TRUTH.md`](SOURCE_OF_TRUTH.md) - Single source of project truth
- [`ROADMAP.md`](ROADMAP.md) - Development roadmap and milestones
- [`docs/`](docs/) - All technical and user documentation
- [`docs/QUALITY_GATES.md`](docs/QUALITY_GATES.md) - Quality assurance and CI/CD setup

## 🛠️ Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (for local development)
- Node.js 20+ (for frontend development)
- PostgreSQL 15+ (for database)

### Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/TheMorpheus407/awareness-platform.git
cd awareness-platform

# Copy environment template
cp .env.example .env
# Edit .env with your configuration

# Start all services
docker-compose up -d

# Run database migrations
docker-compose exec backend alembic upgrade head

# Access the application
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000/docs
```

### Local Development

#### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload
```

#### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## 🏗️ Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  React Frontend │────▶│  FastAPI Backend│────▶│  PostgreSQL DB  │
│   (Port 5173)   │     │   (Port 8000)  │     │   (with RLS)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                       │                        │
         └───────────────────────┴────────────────────────┘
                                 │
                           ┌─────────────┐
                           │    Redis    │
                           │  (Cache)    │
                           └─────────────┘
```

## 🔒 Security Features

- **Multi-tenant isolation** with PostgreSQL Row-Level Security
- **JWT authentication** with refresh tokens
- **Two-Factor Authentication** (2FA) with TOTP
- **Role-Based Access Control** (RBAC)
- **Rate limiting** and DDoS protection
- **Security headers** and CORS configuration
- **Input validation** and SQL injection prevention

## 🚀 Deployment

The platform is deployed on:
- **Production**: https://bootstrap-awareness.de
- **Staging**: Coming soon

Deployment is automated via GitHub Actions on push to `main` branch.

## 📊 Project Status

Current Status: **Production Beta** (60% complete)

See [`todo.md`](todo.md) for current tasks and [`ROADMAP.md`](ROADMAP.md) for future plans.

## 🤝 Contributing

This is a proprietary project. For contribution guidelines, see [`CONTRIBUTING.md`](CONTRIBUTING.md).

## 📄 License

Copyright © 2025 Bootstrap Academy GmbH. All rights reserved.

This software is proprietary and confidential. Unauthorized copying or distribution is prohibited.

## 📞 Contact

- **Website**: https://bootstrap-awareness.de
- **Email**: hallo@bootstrap-awareness.de
- **GitHub**: https://github.com/TheMorpheus407/awareness-platform

---

For credentials and sensitive information, authorized personnel should refer to `CREDENTIALS.md` (not in repository).