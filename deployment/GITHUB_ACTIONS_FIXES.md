# GitHub Actions Deployment Fixes

## Summary of Issues Fixed

### 1. Docker Compose Filename Mismatch
**Issue**: The deploy.yml workflow was copying `docker-compose.prod.ghcr.yml` but the deployment script was referencing `docker-compose.yml`.
**Fix**: The deployment script (deploy-with-rollback.sh) correctly uses `docker-compose.prod.ghcr.yml`.

### 2. Missing GitHub Container Registry Login
**Issue**: The deployment workflow wasn't logging into GHCR before attempting to pull images.
**Fix**: Added Docker login step in deploy.yml before running the deployment script:
```yaml
ssh ubuntu@83.228.205.20 "echo '${{ secrets.GITHUB_TOKEN }}' | sudo docker login ghcr.io -u ${{ github.actor }} --password-stdin"
```

### 3. Duplicate Deployment Workflows
**Issue**: Both ci-cd.yml and deploy.yml were attempting to deploy to production, causing conflicts.
**Fix**: Removed the deployment step from ci-cd.yml and replaced it with a workflow trigger that calls deploy.yml:
```yaml
trigger-deployment:
  runs-on: ubuntu-latest
  needs: [build-and-push, e2e-tests]
  if: github.event_name == 'push' && github.ref == 'refs/heads/main'
  steps:
    - name: Trigger deployment workflow
      uses: actions/github-script@v7
      with:
        script: |
          await github.rest.actions.createWorkflowDispatch({
            owner: context.repo.owner,
            repo: context.repo.repo,
            workflow_id: 'deploy.yml',
            ref: 'main'
          });
```

### 4. Path Inconsistencies
**Issue**: ci-cd.yml referenced `/opt/awareness-platform` while deploy.yml uses `/opt/awareness`.
**Fix**: Consolidated on `/opt/awareness` as the standard deployment directory.

## Deployment Flow After Fixes

1. **CI/CD Pipeline (ci-cd.yml)**:
   - Runs tests (backend, frontend, e2e)
   - Builds and pushes Docker images to GHCR
   - Triggers deploy.yml workflow on success

2. **Deploy Workflow (deploy.yml)**:
   - Runs tests again for safety
   - Builds and pushes images (ensures latest)
   - Logs into GHCR on the server
   - Runs deploy-with-rollback.sh script
   - Performs health checks

3. **Deployment Script (deploy-with-rollback.sh)**:
   - Creates backup of current deployment
   - Pulls latest images from GHCR
   - Runs database migrations
   - Verifies deployment health
   - Supports automatic rollback on failure

## Required GitHub Secrets

Ensure these secrets are configured in the repository:
- `SSH_PRIVATE_KEY`: SSH key for server access
- `GITHUB_TOKEN`: Automatically provided by GitHub Actions
- `DB_PASSWORD`: Database password
- `SECRET_KEY`: Application secret key
- `EMAIL_PASSWORD`: Email service password
- `REDIS_PASSWORD`: Redis password

## Monitoring

- **deployment-monitor.yml**: Monitors deployment status and creates issues on failure
- **rollback.yml**: Manual rollback workflow for emergencies

## Next Steps

1. Commit these changes
2. Push to trigger the workflows
3. Monitor the Actions tab for any issues
4. Verify deployment on https://bootstrap-awareness.de