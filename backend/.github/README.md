# GitHub Actions Workflows

This directory contains the CI/CD pipeline configuration for the Awareness Platform.

## Workflows

### 1. CI/CD Pipeline (`ci-cd.yml`)
Main pipeline that runs on every push to main branch and pull requests.

**Jobs:**
- **backend-tests**: Runs Python tests with pytest, coverage reporting
- **frontend-tests**: Runs TypeScript checks, linting, and unit tests
- **e2e-tests**: Runs Playwright E2E tests against a full stack
- **build-and-push**: Builds and pushes Docker images to GitHub Container Registry
- **deploy**: Deploys to production server (only on main branch)

### 2. Pull Request Checks (`pr-checks.yml`)
Additional checks that run on pull requests.

**Jobs:**
- **lint-and-format**: Checks code formatting with Black, Flake8, ESLint
- **security-scan**: Runs Trivy security scanner
- **test-migrations**: Tests database migrations up and down

### 3. Security Scan (`security-scan.yml`)
Scheduled security scans that run weekly.

**Features:**
- Trivy vulnerability scanning
- CodeQL analysis
- Secret detection with TruffleHog
- Results uploaded to GitHub Security tab

## Required Secrets

Configure these in repository settings:

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `PRODUCTION_HOST` | Production server IP | `83.228.205.20` |
| `PRODUCTION_USER` | SSH user for deployment | `root` |
| `PRODUCTION_SSH_KEY` | Private SSH key for deployment | Content of private key file |
| `PRODUCTION_DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `PRODUCTION_SECRET_KEY` | Django secret key | Random 32-byte hex string |

## Setup Instructions

1. Add required secrets to repository:
   ```bash
   gh secret set PRODUCTION_HOST --body "83.228.205.20"
   gh secret set PRODUCTION_USER --body "root"
   gh secret set PRODUCTION_SSH_KEY < "path/to/private/key"
   gh secret set PRODUCTION_DATABASE_URL --body "postgresql://..."
   gh secret set PRODUCTION_SECRET_KEY --body "$(openssl rand -hex 32)"
   ```

2. Ensure production server has:
   - Docker and Docker Compose installed
   - Repository cloned to `/opt/awareness-platform`
   - Proper directory permissions

3. Test deployment manually first:
   ```bash
   ssh user@server
   cd /opt/awareness-platform
   ./deployment/scripts/deploy-production.sh
   ```

## Workflow Features

- **Caching**: Dependencies cached for faster builds
- **Matrix Testing**: Tests run on multiple Python/Node versions
- **Parallel Jobs**: Tests run concurrently where possible
- **Artifact Upload**: Test reports and coverage saved
- **Health Checks**: Deployment verified before completion
- **Rollback**: Automatic rollback on deployment failure
- **Security**: Vulnerability scanning and secret detection

## Local Testing

Test workflows locally using [act](https://github.com/nektos/act):

```bash
# Test CI workflow
act -j backend-tests

# Test with secrets
act -j deploy --secret-file .secrets
```

## Monitoring

- Check workflow runs: https://github.com/TheMorpheus407/awareness-platform/actions
- View security alerts: https://github.com/TheMorpheus407/awareness-platform/security
- Coverage reports: Uploaded to CodeCov after each run