# Development Workflow Guide

## Overview
This document outlines the development workflow for the Cybersecurity Awareness Platform, including environment setup, development practices, and deployment procedures.

## Table of Contents
1. [Environment Setup](#environment-setup)
2. [Development Flow](#development-flow)
3. [Branch Strategy](#branch-strategy)
4. [Testing Strategy](#testing-strategy)
5. [Code Review Process](#code-review-process)
6. [Deployment Process](#deployment-process)
7. [Troubleshooting](#troubleshooting)

## Environment Setup

### Prerequisites Checklist
- [ ] Git 2.34+
- [ ] Docker Desktop (latest)
- [ ] Python 3.11+
- [ ] Node.js 20+ and npm 10+
- [ ] PostgreSQL client tools
- [ ] Redis client tools
- [ ] VS Code or PyCharm
- [ ] Postman or similar API testing tool

### Initial Setup

#### 1. Repository Setup
```bash
# Clone the repository
git clone git@github.com:bootstrap-academy/AwarenessSchulungen.git
cd AwarenessSchulungen

# Set up git hooks
cp scripts/pre-commit .git/hooks/
chmod +x .git/hooks/pre-commit

# Configure git
git config user.name "Your Name"
git config user.email "your.email@bootstrap-academy.com"
```

#### 2. Environment Configuration
```bash
# Create environment files
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Edit each .env file with appropriate values
```

#### 3. Docker Development Environment
```bash
# Build and start all services
docker-compose -f docker-compose.dev.yml up -d

# Verify all services are running
docker-compose -f docker-compose.dev.yml ps

# Check logs if needed
docker-compose -f docker-compose.dev.yml logs -f [service-name]
```

#### 4. Database Setup
```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Seed development data
docker-compose exec backend python scripts/seed_data.py

# Create superuser account
docker-compose exec backend python scripts/create_superuser.py
```

#### 5. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### IDE Configuration

#### VS Code
Install recommended extensions:
- Python
- Pylance
- Black Formatter
- ESLint
- Prettier
- GitLens
- Docker
- Thunder Client (API testing)

Settings (`.vscode/settings.json`):
```json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": ["--line-length", "100"],
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[typescriptreact]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```

#### PyCharm
1. Set Python interpreter to virtual environment
2. Enable Black formatter
3. Configure ESLint for TypeScript
4. Set up Docker integration
5. Configure database connections

## Development Flow

### Daily Workflow

#### 1. Start Your Day
```bash
# Update your local repository
git checkout develop
git pull origin develop

# Update dependencies if needed
cd backend && pip install -r requirements.txt
cd ../frontend && npm install

# Start services
docker-compose -f docker-compose.dev.yml up -d
```

#### 2. Create Feature Branch
```bash
# Create branch from develop
git checkout -b feature/ISSUE-123-feature-description

# Or for bugfix
git checkout -b bugfix/ISSUE-456-bug-description
```

#### 3. Development Cycle
1. **Write Tests First (TDD)**
   ```python
   # backend/tests/test_new_feature.py
   def test_new_feature_should_work():
       # Arrange
       # Act
       # Assert
       assert False  # Make it fail first
   ```

2. **Implement Feature**
   - Write minimal code to pass tests
   - Refactor for clarity and performance
   - Add logging and error handling

3. **Run Tests Locally**
   ```bash
   # Backend
   cd backend
   pytest tests/test_new_feature.py -v
   
   # Frontend
   cd frontend
   npm test -- --watch
   ```

4. **Commit Regularly**
   ```bash
   git add .
   git commit -m "feat(module): implement feature
   
   - Add detailed description
   - Explain why this change is needed
   
   Refs #123"
   ```

#### 4. Before Push Checklist
- [ ] All tests pass
- [ ] Code is formatted (black/prettier)
- [ ] Linting passes (flake8/eslint)
- [ ] Documentation updated
- [ ] No console.log or print statements
- [ ] No commented out code
- [ ] Security considerations addressed

#### 5. Push and Create PR
```bash
git push origin feature/ISSUE-123-feature-description
# Create PR on GitHub
```

### Working with Different Components

#### Backend Development
```bash
# Run backend in watch mode
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Access API docs
open http://localhost:8000/docs

# Run specific tests
pytest tests/path/to/test.py::TestClass::test_method -v

# Check test coverage
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

#### Frontend Development
```bash
# Start development server
cd frontend
npm run dev

# Run tests in watch mode
npm test -- --watch

# Build for production
npm run build

# Analyze bundle size
npm run analyze
```

#### Database Operations
```bash
# Access database
docker-compose exec postgres psql -U postgres -d awareness_platform

# Create new migration
cd backend
alembic revision -m "add_new_table"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Branch Strategy

### Branch Types
- `main` - Production code
- `develop` - Integration branch
- `feature/*` - New features
- `bugfix/*` - Bug fixes
- `hotfix/*` - Urgent production fixes
- `release/*` - Release preparation
- `chore/*` - Maintenance tasks

### Branch Rules
1. Never commit directly to `main` or `develop`
2. Always create PR for code review
3. Keep branches up-to-date with develop
4. Delete branches after merge
5. Use descriptive branch names

### Git Flow Example
```bash
# Start new feature
git checkout develop
git pull origin develop
git checkout -b feature/add-user-notifications

# Work on feature
# ... make changes ...
git add .
git commit -m "feat(notifications): add email notification service"

# Keep branch updated
git fetch origin
git rebase origin/develop

# Push feature
git push origin feature/add-user-notifications

# After PR approval and merge
git checkout develop
git pull origin develop
git branch -d feature/add-user-notifications
```

## Testing Strategy

### Test Levels
1. **Unit Tests** - Test individual functions/components
2. **Integration Tests** - Test component interactions
3. **E2E Tests** - Test complete user flows
4. **Performance Tests** - Test load and response times
5. **Security Tests** - Test vulnerabilities

### Backend Testing
```python
# Example test structure
import pytest
from fastapi.testclient import TestClient
from app.main import app

class TestUserAPI:
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self, client):
        # Login and return auth headers
        pass
    
    def test_create_user(self, client, auth_headers):
        response = client.post(
            "/api/v1/users",
            json={"email": "test@example.com", "password": "SecurePass123!"},
            headers=auth_headers
        )
        assert response.status_code == 201
        assert response.json()["email"] == "test@example.com"
```

### Frontend Testing
```typescript
// Example component test
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { UserList } from './UserList';

describe('UserList', () => {
  it('should filter users by search term', async () => {
    render(<UserList />);
    
    const searchInput = screen.getByPlaceholderText(/search users/i);
    await userEvent.type(searchInput, 'john');
    
    await waitFor(() => {
      expect(screen.getByText(/john doe/i)).toBeInTheDocument();
      expect(screen.queryByText(/jane smith/i)).not.toBeInTheDocument();
    });
  });
});
```

### Test Coverage Requirements
- Backend: Minimum 80% coverage
- Frontend: Minimum 75% coverage
- Critical paths: 100% coverage

## Code Review Process

### Reviewer Checklist
- [ ] Code follows project standards
- [ ] Tests are comprehensive
- [ ] No security vulnerabilities
- [ ] Performance considerations addressed
- [ ] Documentation is clear
- [ ] Error handling is appropriate
- [ ] Logging is sufficient
- [ ] No unnecessary complexity

### Review Workflow
1. **Automated Checks** - CI runs tests, linting, security scans
2. **Peer Review** - At least one approval required
3. **Feedback Loop** - Address comments and re-request review
4. **Final Approval** - Maintainer approves and merges

### Review Best Practices
- Review promptly (within 24 hours)
- Be constructive and specific
- Suggest improvements, don't just criticize
- Consider the bigger picture
- Test the changes locally if needed

## Deployment Process

### Development Deployment
Automatic deployment on push to develop branch:
```yaml
# .github/workflows/deploy-dev.yml
on:
  push:
    branches: [develop]
```

### Staging Deployment
1. Create release branch
   ```bash
   git checkout -b release/v1.2.0 develop
   ```
2. Update version numbers
3. Run full test suite
4. Deploy to staging
5. Perform QA testing

### Production Deployment
1. Merge release branch to main
2. Tag release
   ```bash
   git tag -a v1.2.0 -m "Release version 1.2.0"
   git push origin v1.2.0
   ```
3. Automated deployment triggered
4. Monitor deployment
5. Verify production

### Rollback Procedure
```bash
# Quick rollback to previous version
./scripts/rollback.sh v1.1.0

# Or using Docker
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build
```

## Troubleshooting

### Common Issues

#### Docker Issues
```bash
# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Clean up Docker
docker system prune -a --volumes
```

#### Database Issues
```bash
# Reset database
docker-compose exec postgres psql -U postgres -c "DROP DATABASE awareness_platform;"
docker-compose exec postgres psql -U postgres -c "CREATE DATABASE awareness_platform;"
docker-compose exec backend alembic upgrade head
```

#### Node/npm Issues
```bash
# Clear npm cache
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

#### Python/pip Issues
```bash
# Recreate virtual environment
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Debug Mode

#### Backend Debugging
```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use VS Code debugger with launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["main:app", "--reload"],
      "jinja": true
    }
  ]
}
```

#### Frontend Debugging
```typescript
// Add debugger statement
debugger;

// Or use Chrome DevTools
// Or VS Code debugger with Chrome extension
```

### Getting Help
1. Check documentation
2. Search existing issues
3. Ask in #dev-help Slack channel
4. Create detailed issue with reproduction steps

## Continuous Improvement

### Performance Monitoring
- Monitor API response times
- Track frontend bundle size
- Profile database queries
- Review error logs regularly

### Code Quality Metrics
- Maintain test coverage above thresholds
- Keep cyclomatic complexity low
- Reduce code duplication
- Regular dependency updates

### Regular Maintenance
- Weekly dependency updates
- Monthly security audits
- Quarterly performance reviews
- Annual architecture reviews

---

Remember: Good development practices lead to maintainable code and happy developers!