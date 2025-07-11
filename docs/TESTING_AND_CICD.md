# Comprehensive Testing and CI/CD Documentation

## Overview

This document outlines the comprehensive testing strategy and CI/CD pipeline implemented for the Awareness Schulungen platform. Our goal is to maintain **80%+ test coverage**, ensure **zero deployment failures**, and provide **automated rollback capabilities**.

## Table of Contents

1. [Testing Strategy](#testing-strategy)
2. [CI/CD Pipeline](#cicd-pipeline)
3. [Test Coverage Requirements](#test-coverage-requirements)
4. [Security Scanning](#security-scanning)
5. [Performance Testing](#performance-testing)
6. [Deployment Process](#deployment-process)
7. [Monitoring and Rollback](#monitoring-and-rollback)

## Testing Strategy

### Test Pyramid

```
         /\
        /E2E\        <- End-to-End Tests (10%)
       /______\
      /Integra-\     <- Integration Tests (30%)
     /  tion    \
    /____________\
   /    Unit      \  <- Unit Tests (60%)
  /________________\
```

### Backend Testing

#### Unit Tests
- **Location**: `backend/tests/unit/`
- **Coverage Target**: 80%+
- **Framework**: pytest
- **Key Files**:
  - `test_comprehensive_coverage.py` - Core business logic
  - `test_api_endpoints.py` - API endpoint validation
  - `test_auth_service.py` - Authentication flows
  - `test_business_logic.py` - Domain logic

```bash
# Run backend unit tests
cd backend
pytest tests/unit -v --cov=. --cov-report=html
```

#### Integration Tests
- **Location**: `backend/tests/api/`, `backend/tests/core/`
- **Database**: PostgreSQL test instance
- **Redis**: Test Redis instance
- **Key Tests**:
  - Database transactions
  - API endpoint integration
  - Authentication flows
  - Payment processing

```bash
# Run backend integration tests
cd backend
pytest tests/api tests/core -v
```

### Frontend Testing

#### Unit Tests
- **Location**: `frontend/src/**/*.test.ts`
- **Coverage Target**: 80%+
- **Framework**: Vitest
- **Key Files**:
  - `services/api.test.ts` - API service testing
  - `hooks/useAuth.test.ts` - Authentication hook
  - `components/**/*.test.tsx` - Component tests

```bash
# Run frontend unit tests
cd frontend
npm run test:coverage
```

#### E2E Tests
- **Location**: `frontend/tests/e2e/`
- **Framework**: Playwright
- **Browsers**: Chrome, Firefox, Safari
- **Key Tests**:
  - `smoke.spec.ts` - Critical user journeys
  - Authentication flows
  - Course enrollment
  - Payment processing

```bash
# Run E2E tests
cd frontend
npm run test:e2e
```

## CI/CD Pipeline

### CI Pipeline (`ci.yml`)

The enhanced CI pipeline includes:

1. **Code Quality Gate**
   - Path filtering for changed components
   - Determines which tests to run

2. **Backend Testing**
   - Linting (ruff, mypy)
   - Security scanning (bandit, safety)
   - Unit tests with coverage
   - Integration tests
   - Coverage enforcement (80%+)

3. **Frontend Testing**
   - Linting (ESLint)
   - Type checking (TypeScript)
   - Security audit (npm audit)
   - Unit tests with coverage
   - Accessibility tests
   - Bundle size analysis

4. **E2E Testing**
   - Multi-browser testing
   - Smoke tests
   - Video recording on failure

5. **Security Scanning**
   - Trivy filesystem scan
   - OWASP dependency check
   - GitLeaks secrets scanning
   - Container vulnerability scanning

6. **Performance Testing**
   - Load testing with k6
   - Stress testing
   - Performance metrics analysis

### CD Pipeline (`cd.yml`)

The enhanced CD pipeline includes:

1. **Pre-deployment Validation**
   - Version generation
   - Changelog creation
   - CI checks verification

2. **Staging Deployment**
   - Backup creation
   - Blue-green deployment
   - Database migration with transactions
   - Health checks
   - Validation tests
   - Performance validation

3. **Staging Approval Gate**
   - Manual approval required for production

4. **Production Deployment**
   - Comprehensive backup
   - Canary deployment (10% traffic)
   - Full rollout if canary succeeds
   - Health monitoring
   - Critical path testing

5. **Automated Rollback**
   - Triggers on deployment failure
   - Restores from backup
   - Verifies rollback success

6. **Post-deployment Monitoring**
   - 30-minute monitoring period
   - Error rate tracking
   - Response time monitoring
   - Automatic rollback on degradation

## Test Coverage Requirements

### Backend Coverage (80%+ Required)

```yaml
# pytest.ini configuration
--cov-fail-under=80
--cov=app
--cov=api
--cov=core
--cov=crud
--cov=models
--cov=schemas
--cov=services
```

### Frontend Coverage (80%+ Required)

```javascript
// vitest.config.ts
coverage: {
  enabled: true,
  reporter: ['text', 'json', 'html'],
  threshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    }
  }
}
```

## Security Scanning

### Tools Used

1. **Backend Security**
   - Bandit - Python security linting
   - Safety - Dependency vulnerability scanning
   - pip-audit - Package audit

2. **Frontend Security**
   - npm audit - Dependency vulnerabilities
   - ESLint security rules

3. **Infrastructure Security**
   - Trivy - Container and filesystem scanning
   - OWASP Dependency Check
   - GitLeaks - Secret detection

### Security Gates

- No HIGH or CRITICAL vulnerabilities in production
- All secrets in environment variables
- HTTPS enforcement
- Security headers validation

## Performance Testing

### Load Testing

**Script**: `infrastructure/tests/performance/load-test.js`

- Simulates normal user load
- Ramps up to 100 concurrent users
- Measures response times and error rates
- Validates SLA compliance

### Stress Testing

**Script**: `infrastructure/tests/performance/stress-test.js`

- Pushes system to breaking point
- Ramps up to 500 concurrent users
- Identifies system limits
- Measures resource usage

### Performance Criteria

- P95 response time < 500ms (load test)
- P99 response time < 1000ms (load test)
- Error rate < 0.1% (load test)
- System stable up to 300 users (stress test)

## Deployment Process

### Staging Deployment

1. **Backup Current State**
   ```bash
   docker-compose ps -q | xargs docker commit
   ```

2. **Run Migrations**
   ```python
   python infrastructure/scripts/safe-migration.py
   ```

3. **Blue-Green Deployment**
   - Start new containers alongside old
   - Health check new containers
   - Switch traffic to new containers
   - Remove old containers

4. **Validation**
   - Run staging validation tests
   - Check performance metrics
   - Verify all services healthy

### Production Deployment

1. **Comprehensive Backup**
   - Database dump
   - Volume backups
   - Image backups
   - Automated restore script

2. **Canary Deployment**
   - Deploy to 10% of traffic
   - Monitor for 5 minutes
   - Check error rates
   - Full deployment if successful

3. **Health Monitoring**
   - API health checks
   - Frontend availability
   - Database connectivity
   - Response time validation

## Monitoring and Rollback

### Health Checks

```bash
# API Health
curl https://bootstrap-awareness.de/api/v1/health

# Expected Response
{
  "status": "healthy",
  "database": "healthy",
  "redis": "healthy",
  "version": "1.0.0"
}
```

### Automated Rollback Triggers

1. **Deployment Failures**
   - Health check failures
   - Migration errors
   - Container startup issues

2. **Post-deployment Issues**
   - Error rate > 100/minute
   - Response time > 2 seconds
   - Critical service unavailable

### Rollback Process

```bash
# Automatic rollback script
cd /opt/awareness-platform/backups/${BACKUP_ID}
./restore.sh
```

## Running Tests Locally

### Backend Tests

```bash
# Install dependencies
cd backend
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test category
pytest -m unit
pytest -m integration
pytest -m security
```

### Frontend Tests

```bash
# Install dependencies
cd frontend
npm install

# Run unit tests
npm test

# Run with coverage
npm run test:coverage

# Run E2E tests
npm run test:e2e

# Run specific test file
npm test -- api.test.ts
```

### Performance Tests

```bash
# Install k6
brew install k6  # macOS
# or
sudo apt-get install k6  # Ubuntu

# Run load test
k6 run infrastructure/tests/performance/load-test.js

# Run stress test
k6 run infrastructure/tests/performance/stress-test.js
```

## Best Practices

1. **Write Tests First**
   - TDD for new features
   - Tests before fixing bugs

2. **Test Isolation**
   - Each test independent
   - Clean state between tests
   - Mock external dependencies

3. **Meaningful Assertions**
   - Test behavior, not implementation
   - Clear failure messages
   - One concept per test

4. **Performance**
   - Parallelize where possible
   - Use test databases
   - Clean up after tests

5. **Security**
   - Never commit secrets
   - Test authentication flows
   - Validate authorization

## Troubleshooting

### Common Issues

1. **Coverage Below Threshold**
   ```bash
   # Generate detailed coverage report
   pytest --cov=. --cov-report=html
   open htmlcov/index.html
   ```

2. **Flaky E2E Tests**
   - Check for timing issues
   - Add proper waits
   - Ensure clean test data

3. **CI Pipeline Failures**
   - Check logs in GitHub Actions
   - Run tests locally first
   - Verify environment variables

### Support

- **Documentation**: `/docs`
- **CI/CD Issues**: Check `.github/workflows/`
- **Test Issues**: Review test configuration files

## Metrics and Reporting

### Current Status
- Backend Coverage: Target 80%+
- Frontend Coverage: Target 80%+
- Deployment Success Rate: Target 100%
- Mean Time to Recovery: < 10 minutes

### Reports Location
- Coverage Reports: Generated in CI artifacts
- Performance Reports: `performance-analysis.html`
- Security Reports: Uploaded to GitHub Security tab

## Future Improvements

1. **Mutation Testing**
   - Validate test quality
   - Identify weak tests

2. **Contract Testing**
   - API contract validation
   - Frontend-Backend sync

3. **Chaos Engineering**
   - Failure injection
   - Resilience testing

4. **A/B Testing Infrastructure**
   - Feature flags
   - Gradual rollouts