# Cybersecurity Awareness Platform

Automated cybersecurity training platform with phishing simulations, compliance reporting, and interactive courses.

## Features

- Interactive cybersecurity awareness courses
- Automated phishing simulation campaigns
- Compliance reporting (NIS-2, DSGVO, ISO 27001, TISAX)
- Real-time analytics and dashboards
- Multi-tenant architecture
- Enterprise SSO integration

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 20+
- Python 3.11+
- PostgreSQL 15+
- Redis 7+

### Local Development

1. Clone the repository
2. Copy `.env.example` to `.env` and configure
3. Run `docker-compose up -d`
4. Access the application at http://localhost

### Production Deployment

The application automatically deploys to production when changes are pushed to the main branch.

## Architecture

- **Frontend**: React with TypeScript, Tailwind CSS
- **Backend**: FastAPI (Python), SQLAlchemy
- **Database**: PostgreSQL
- **Cache**: Redis
- **Deployment**: Docker, GitHub Actions CI/CD

## Security

- All communications encrypted with TLS
- OWASP security best practices
- Regular security audits
- Automated vulnerability scanning

## License

Proprietary - Bootstrap Academy GmbH