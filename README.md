# Cybersecurity Awareness Platform (Simplified MVP)

A streamlined cybersecurity awareness training platform focused on essential features.

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 20+ (for local development)
- PostgreSQL 15+

### Using Docker (Recommended)

```bash
# Clone and setup
git clone https://github.com/TheMorpheus407/awareness-platform.git
cd awareness-platform

# Start all services
docker-compose up -d

# Run database migrations
docker-compose exec backend alembic upgrade head

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/docs
```

### Local Development

#### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
python main.py
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

## 🏗️ Architecture (Simplified)

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  React Frontend │────▶│  FastAPI Backend│────▶│  PostgreSQL DB  │
│   (Port 3000)   │     │   (Port 8000)  │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## ✨ Core Features

- **User Authentication** - Email/password login with JWT tokens
- **Course System** - Video-based training with quizzes
- **Phishing Simulations** - Basic email templates and tracking
- **Analytics Dashboard** - Key metrics and compliance rates
- **Multi-tenant** - Company-based user management

## 📁 Simplified Structure

```
awareness-platform/
├── backend/
│   ├── api/routes/       # API endpoints
│   ├── models/           # Database models
│   ├── schemas/          # Pydantic schemas
│   ├── alembic/          # Database migrations
│   ├── requirements.txt  # Python dependencies (25 packages)
│   └── main.py          # FastAPI application
├── frontend/
│   ├── src/
│   │   ├── pages/       # Simple page components
│   │   ├── api/         # API client
│   │   └── SimpleApp.tsx # Main app component
│   └── package.json
├── docker-compose.yml    # Single Docker configuration
└── nginx.conf           # Simple nginx config
```

## 🔒 Security

- JWT authentication
- Password hashing with bcrypt
- CORS configuration
- Input validation
- SQL injection prevention

## 🚀 Deployment

The platform is deployed on:
- **Production**: https://bootstrap-awareness.de

Deployment is automated via GitHub Actions on push to `main` branch.

## 📊 Technology Stack

### Backend
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- JWT Authentication

### Frontend
- React 18
- TypeScript
- Tailwind CSS
- Axios

### Infrastructure
- Docker
- Nginx
- GitHub Actions

## 📄 License

Copyright © 2025 Bootstrap Academy GmbH. All rights reserved.