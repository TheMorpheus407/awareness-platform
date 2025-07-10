# Quality Gates Configuration

## Overview

This project uses comprehensive quality gates to ensure code quality, security, and maintainability. The quality checks are enforced via GitHub Actions on every pull request and push to main branches.

## Current Quality Checks

### 1. Backend Quality Checks
- **Type Checking**: MyPy with strict mode
- **Code Style**: Flake8 with 88-character line limit
- **Security**: Bandit for vulnerability scanning
- **Complexity**: Radon for cyclomatic complexity analysis

### 2. Frontend Quality Checks
- **Type Checking**: TypeScript in strict mode
- **Linting**: ESLint with comprehensive rules
- **Dead Code**: ts-prune for unused exports detection

### 3. Security Checks
- **Secret Detection**: detect-secrets with baseline comparison
- **License Compliance**: Automated license scanning for all dependencies

### 4. Test Coverage
- **Backend**: Minimum 70% coverage required
- **Frontend**: Minimum 60% coverage required (branches, functions, lines, statements)
- **Coverage Reports**: Automatically generated and uploaded as artifacts

## SonarCloud Integration (Optional)

SonarCloud provides advanced code quality metrics and can be enabled by following these steps:

### Setup Instructions

1. **Create SonarCloud Project**
   - Go to [SonarCloud](https://sonarcloud.io)
   - Create a new project with key: `awareness-platform`
   - Add the project to organization: `awareness`

2. **Generate Token**
   - In SonarCloud, go to Account > Security
   - Generate a new token with name: `GitHub Actions`
   - Copy the token value

3. **Add GitHub Secret**
   - In GitHub repository settings, go to Secrets and Variables > Actions
   - Add new secret named `SONAR_TOKEN` with the token value

4. **Enable in Workflow**
   - Edit `.github/workflows/quality-gates.yml`
   - Uncomment the SonarCloud job section
   - Commit and push the changes

### Alternative: Local Coverage

If you don't want to use SonarCloud, the workflow includes a local coverage enforcement job that:
- Runs tests with coverage for both backend and frontend
- Enforces minimum coverage thresholds
- Generates coverage reports as artifacts
- Comments coverage summary on pull requests

## Running Quality Checks Locally

### Backend
```bash
cd backend

# Type checking
mypy . --ignore-missing-imports --strict

# Code style
flake8 . --max-line-length=88 --extend-ignore=E203

# Security
bandit -r . -ll

# Complexity
radon cc . -a -nb

# Coverage
pytest --cov=. --cov-report=xml --cov-report=term-missing --cov-fail-under=70
```

### Frontend
```bash
cd frontend

# Type checking
npm run type-check

# Linting
npm run lint

# Dead code detection
npx ts-prune

# Coverage
npm run test:coverage
```

### Secret Detection
```bash
# Install detect-secrets
pip install detect-secrets

# Run scan
detect-secrets scan --baseline .secrets.baseline
```

## Configuration Files

- **Backend**: See `backend/setup.cfg` and `backend/pyproject.toml`
- **Frontend**: See `frontend/.eslintrc.json` and `frontend/tsconfig.json`
- **SonarCloud**: See `sonar-project.properties`
- **Workflows**: See `.github/workflows/quality-gates.yml`

## Troubleshooting

### Workflow Failures

1. **Type Errors**: Fix TypeScript/MyPy errors in your code
2. **Linting Issues**: Run auto-fix locally: `npm run lint:fix` or `black .`
3. **Coverage Too Low**: Add more tests to increase coverage
4. **Security Issues**: Review and fix flagged security vulnerabilities

### SonarCloud Issues

1. **Project Not Found**: Ensure project exists in SonarCloud with correct key
2. **Authentication Failed**: Check SONAR_TOKEN secret is correctly set
3. **Quality Gate Failed**: Review SonarCloud dashboard for specific issues

## Contributing

When contributing to this project:
1. Run all quality checks locally before pushing
2. Ensure your changes don't reduce code coverage
3. Fix any linting or type errors
4. Review security scan results
5. Update tests as needed

For questions or issues with quality gates, please open a GitHub issue.