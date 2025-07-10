# Cybersecurity Awareness Training Platform

[![License](https://img.shields.io/badge/license-proprietary-red.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![React](https://img.shields.io/badge/react-18.2-61dafb.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/fastapi-0.109-009688.svg)](https://fastapi.tiangolo.com/)

A comprehensive platform for cybersecurity awareness training with phishing simulations, course management, and analytics.

## 🚀 Features

- **Multi-tenant Architecture**: Company-based isolation with Row-Level Security
- **Authentication & Security**: JWT auth with 2FA support  
- **Course Management**: Video courses, quizzes, and certificates
- **Phishing Simulations**: Email campaigns and tracking
- **Analytics Dashboard**: Real-time insights and reporting
- **Payment Processing**: Stripe integration for subscriptions
- **Email Campaigns**: Automated training reminders

## 🛠️ Tech Stack

- **Backend**: FastAPI, PostgreSQL, Redis, SQLAlchemy
- **Frontend**: React, TypeScript, Vite, TailwindCSS
- **Infrastructure**: Docker, Nginx, Prometheus, Grafana

## 📋 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (optional)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/awareness-platform.git
cd awareness-platform

# Setup environment
make setup

# Edit .env file with your configuration

# Install dependencies
make install
```

### Development

With Docker:
```bash
make docker-up
```

Or run locally:
```bash
# Terminal 1: Backend
make dev

# Terminal 2: Frontend  
cd frontend && npm run dev
```

Access:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/api/docs

### Database Setup

```bash
# Run migrations
make migrate

# Create admin user
cd backend && ./venv/bin/python create_admin_user.py
```

## 📁 Project Structure

```
├── backend/              # FastAPI backend
│   ├── api/             # API routes and dependencies
│   ├── core/            # Core utilities and config
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic schemas
│   ├── services/        # Business logic
│   ├── tests/           # Test files
│   ├── alembic/         # Database migrations
│   └── main.py          # Application entry point
├── frontend/            # React frontend
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── pages/       # Page components
│   │   ├── services/    # API services
│   │   ├── store/       # State management
│   │   └── utils/       # Utilities
│   └── package.json
├── docker-compose.yml   # Docker services
├── Makefile            # Common commands
└── README.md
```

## 🧪 Testing

```bash
# Backend tests
make test

# Frontend tests
cd frontend && npm test
```

## 🚀 Deployment

### Production Configuration

1. Update `.env` for production:
   - Set strong SECRET_KEY
   - Configure database credentials
   - Set SMTP settings
   - Add Stripe keys
   - Configure domain names

2. Build and deploy:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Environment Variables

See `.env.example` for all available configuration options.

## 📚 API Documentation

When running in development mode:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under a proprietary license - see the LICENSE file for details.

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