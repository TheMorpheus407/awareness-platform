# GitHub Actions Workflows

This directory contains the CI/CD workflows for the Cybersecurity Awareness Platform.

## Workflow Files

### ci-cd.yml
Main CI/CD pipeline that runs on push to main/develop branches and pull requests.
- Runs backend tests with PostgreSQL and Redis
- Runs frontend tests and builds
- Executes E2E tests
- Builds and pushes Docker images (on main branch)
- Deploys to production (on main branch)

### e2e-tests.yml
Dedicated E2E testing workflow with visual regression tests.
- Sets up full application stack
- Runs Playwright tests
- Captures screenshots and videos on failure
- Performs visual regression testing on PRs

### deploy.yml
Production deployment workflow.
- Builds Docker images
- Pushes to GitHub Container Registry
- Deploys to production server
- Runs database migrations
- Performs health checks with retry logic

### pr-checks.yml
Pull request validation checks.
- Code linting (Black, Flake8, ESLint)
- Type checking (mypy, TypeScript)
- Security scanning

### security-scan.yml
Security scanning workflow.
- Dependency vulnerability scanning
- Code security analysis

## Environment Variables

All workflows use consistent environment variables:

### Test Environment
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string  
- `SECRET_KEY`: Application secret key
- `FRONTEND_URL`: Frontend URL for CORS
- `BACKEND_URL`: Backend API URL
- `CORS_ORIGINS`: Allowed CORS origins
- `ENVIRONMENT`: Environment name (test/production)
- `EMAIL_FROM`: Sender email address
- `SMTP_*`: Email configuration

### Production Environment
Production secrets are stored in GitHub Secrets:
- `PRODUCTION_HOST`: Server hostname
- `PRODUCTION_USER`: SSH username
- `PRODUCTION_SSH_KEY`: SSH private key
- `PRODUCTION_DATABASE_URL`: Production database URL
- `PRODUCTION_SECRET_KEY`: Production secret key
- `DB_PASSWORD`: Database password
- `EMAIL_PASSWORD`: SMTP password

## Database Migration Handling

All workflows handle PostgreSQL enum type conflicts using:
1. `fix_migration_types.py` or `ci_migration_fix.py` to clean up existing types
2. Retry logic for migration execution (3 attempts)
3. Proper error handling and logging

## Testing

Run the validation script to check workflow configuration:
```bash
./.github/scripts/validate-workflows.sh
```

## Best Practices

1. Always include all required environment variables
2. Use retry logic for network operations
3. Handle errors gracefully with proper logging
4. Install `pytest-asyncio` for async test support
5. Use consistent database names across workflows
6. Keep workflows DRY by using shared configuration