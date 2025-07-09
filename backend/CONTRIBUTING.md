# Contributing to Cybersecurity Awareness Platform

Thank you for your interest in contributing to the Cybersecurity Awareness Platform! This document provides guidelines and instructions for contributing to the project.

## Table of Contents
1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [How to Contribute](#how-to-contribute)
5. [Reporting Issues](#reporting-issues)
6. [Submitting Pull Requests](#submitting-pull-requests)
7. [Development Workflow](#development-workflow)
8. [Developer Certificate of Origin](#developer-certificate-of-origin)

## Code of Conduct

### Our Pledge
We are committed to providing a friendly, safe, and welcoming environment for all contributors, regardless of experience level, gender identity and expression, sexual orientation, disability, personal appearance, body size, race, ethnicity, age, religion, or nationality.

### Our Standards
Examples of behavior that contributes to a positive environment:
- Using welcoming and inclusive language
- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

Examples of unacceptable behavior:
- The use of sexualized language or imagery
- Personal attacks or derogatory comments
- Trolling or insulting/derogatory comments
- Public or private harassment
- Publishing others' private information without explicit permission
- Other conduct which could reasonably be considered inappropriate

### Enforcement
Project maintainers are responsible for clarifying and enforcing standards of acceptable behavior and will take appropriate and fair corrective action in response to any instances of unacceptable behavior.

## Getting Started

### Prerequisites
Before you begin, ensure you have the following installed:
- Git (2.34+)
- Docker and Docker Compose (latest stable)
- Python 3.11+
- Node.js 20+ and npm
- PostgreSQL 15+ (for local development without Docker)
- Redis 7+ (for local development without Docker)

### Project Structure Overview
```
AwarenessSchulungen/
├── backend/          # FastAPI backend application
├── frontend/         # React/TypeScript frontend
├── docs/            # Project documentation
├── deployment/      # Deployment configurations
├── scripts/         # Utility scripts
└── tests/          # End-to-end tests
```

## Development Setup

### 1. Fork and Clone the Repository
```bash
# Fork the repository on GitHub first, then:
git clone https://github.com/YOUR_USERNAME/AwarenessSchulungen.git
cd AwarenessSchulungen

# Add upstream remote
git remote add upstream https://github.com/bootstrap-academy/AwarenessSchulungen.git
```

### 2. Backend Setup

#### Using Docker (Recommended)
```bash
cd backend
cp .env.example .env
# Edit .env with your configurations

# Start all services
docker-compose up -d

# Run migrations
docker-compose exec backend alembic upgrade head

# Create a superuser
docker-compose exec backend python scripts/create_superuser.py
```

#### Manual Setup
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Setup environment
cp .env.example .env
# Edit .env with your configurations

# Setup database
createdb awareness_platform
alembic upgrade head

# Run development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Setup environment
cp .env.example .env
# Edit .env with your configurations

# Start development server
npm run dev
```

### 4. Verify Setup
1. Backend API: http://localhost:8000/docs
2. Frontend: http://localhost:5173
3. Run tests: `npm test` (frontend) and `pytest` (backend)

## How to Contribute

### Types of Contributions

#### 1. Bug Reports
- Search existing issues before creating a new one
- Use the bug report template
- Include reproduction steps
- Provide system information

#### 2. Feature Requests
- Check the roadmap and existing issues
- Use the feature request template
- Explain the use case clearly
- Consider implementation approach

#### 3. Code Contributions
- Bug fixes
- New features
- Performance improvements
- Test coverage improvements
- Documentation updates

#### 4. Translations
- Help translate the platform to other languages
- Review and improve existing translations
- Update documentation for internationalization

#### 5. Security Reports
- **DO NOT** open public issues for security vulnerabilities
- Email security@bootstrap-academy.com directly
- Include detailed information and proof of concept if possible

## Reporting Issues

### Before Creating an Issue
1. Search existing issues (including closed ones)
2. Check the documentation
3. Try to reproduce with the latest version

### Creating a Good Issue
Use our issue templates and include:
- Clear, descriptive title
- Detailed description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Screenshots if applicable
- System information

### Issue Labels
- `bug`: Something isn't working
- `enhancement`: New feature or request
- `documentation`: Documentation improvements
- `good first issue`: Good for newcomers
- `help wanted`: Extra attention needed
- `question`: Further information requested

## Submitting Pull Requests

### PR Process
1. **Create a Feature Branch**
   ```bash
   git checkout -b feature/issue-123-description
   ```

2. **Make Your Changes**
   - Follow our [Coding Standards](docs/CODING_STANDARDS.md)
   - Write/update tests
   - Update documentation
   - Add yourself to CONTRIBUTORS.md (first PR only)

3. **Commit Your Changes**
   ```bash
   git add .
   git commit -m "feat(module): add new feature
   
   - Detailed description of changes
   - Why this change is necessary
   
   Closes #123"
   ```

4. **Keep Your Fork Updated**
   ```bash
   git fetch upstream
   git rebase upstream/develop
   ```

5. **Push and Create PR**
   ```bash
   git push origin feature/issue-123-description
   ```
   Then create a PR on GitHub using our template

### PR Requirements
- [ ] All tests pass
- [ ] Code coverage maintained or improved
- [ ] Documentation updated
- [ ] Commits follow conventional format
- [ ] No merge conflicts
- [ ] Approved by at least one maintainer

### PR Review Process
1. Automated checks run (linting, tests, coverage)
2. Code review by maintainers
3. Address feedback
4. Final approval and merge

## Development Workflow

### Git Workflow
We use Git Flow with the following branches:
- `main`: Production-ready code
- `develop`: Integration branch for features
- `feature/*`: New features
- `bugfix/*`: Bug fixes
- `hotfix/*`: Critical production fixes
- `release/*`: Release preparation

### Daily Development
1. **Start Your Day**
   ```bash
   git checkout develop
   git pull upstream develop
   ```

2. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature
   ```

3. **Development Cycle**
   - Write code
   - Run tests locally
   - Commit frequently
   - Push to your fork

4. **Before Creating PR**
   ```bash
   # Run all checks
   make lint
   make test
   make coverage
   ```

### Testing Guidelines

#### Backend Testing
```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py

# Run with verbose output
pytest -v
```

#### Frontend Testing
```bash
cd frontend

# Run all tests
npm test

# Run with coverage
npm run test:coverage

# Run in watch mode
npm run test:watch

# Run e2e tests
npm run test:e2e
```

### Code Quality Tools

#### Python/Backend
```bash
# Format code
black .

# Lint code
flake8 .

# Type checking
mypy .

# Security scan
bandit -r app/
```

#### TypeScript/Frontend
```bash
# Format code
npm run format

# Lint code
npm run lint

# Type checking
npm run type-check

# Bundle analysis
npm run analyze
```

## Developer Certificate of Origin

By contributing to this project, you agree to the Developer Certificate of Origin (DCO):

```
Developer Certificate of Origin
Version 1.1

Copyright (C) 2004, 2006 The Linux Foundation and its contributors.

Everyone is permitted to copy and distribute verbatim copies of this
license document, but changing it is not allowed.

Developer's Certificate of Origin 1.1

By making a contribution to this project, I certify that:

(a) The contribution was created in whole or in part by me and I
    have the right to submit it under the open source license
    indicated in the file; or

(b) The contribution is based upon previous work that, to the best
    of my knowledge, is covered under an appropriate open source
    license and I have the right under that license to submit that
    work with modifications, whether created in whole or in part
    by me, under the same open source license (unless I am
    permitted to submit under a different license), as indicated
    in the file; or

(c) The contribution was provided directly to me by some other
    person who certified (a), (b) or (c) and I have not modified
    it.

(d) I understand and agree that this project and the contribution
    are public and that a record of the contribution (including all
    personal information I submit with it, including my sign-off) is
    maintained indefinitely and may be redistributed consistent with
    this project or the open source license(s) involved.
```

### Sign Your Work
Add a `Signed-off-by` line to your commits:

```bash
git commit -s -m "Your commit message"
```

Or add manually:
```
feat: add new feature

Some description

Signed-off-by: Your Name <your.email@example.com>
```

## Getting Help

### Resources
- [Documentation](docs/)
- [API Documentation](http://localhost:8000/docs)
- [Discord Community](https://discord.gg/bootstrap-academy)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/awareness-platform)

### Contact
- General: hello@bootstrap-academy.com
- Security: security@bootstrap-academy.com
- Business: business@bootstrap-academy.com

## Recognition

Contributors are recognized in the following ways:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Special badges in our Discord community
- Invitation to contributor-only events

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (see LICENSE file).

---

Thank you for contributing to making cybersecurity awareness training better for everyone! 🛡️