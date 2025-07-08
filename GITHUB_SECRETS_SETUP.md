# GitHub Secrets Configuration Guide

## Required Secrets for Deployment

To enable automated deployment via GitHub Actions, you need to configure the following secrets in your GitHub repository:

### 1. SSH_PRIVATE_KEY (Required)
The SSH private key for accessing the production server.

**Location**: `/mnt/e/Projects/AwarenessSchulungen/bootstrap-awareness private key.txt`

**Setup**:
1. Go to your GitHub repository
2. Navigate to Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Name: `SSH_PRIVATE_KEY`
5. Value: Copy the entire content of the private key file

### 2. DB_PASSWORD (Required)
Database password for PostgreSQL.

**Setup**:
1. Generate a strong password (e.g., using `openssl rand -base64 32`)
2. Add as GitHub secret:
   - Name: `DB_PASSWORD`
   - Value: Your generated password

### 3. SECRET_KEY (Required)
Application secret key for JWT tokens.

**Setup**:
1. Generate using: `openssl rand -hex 32`
2. Add as GitHub secret:
   - Name: `SECRET_KEY`
   - Value: Your generated key

### 4. EMAIL_PASSWORD (Required)
Email password for sending notifications.

**Setup**:
1. Add as GitHub secret:
   - Name: `EMAIL_PASSWORD`
   - Value: `5X58dee2u3ov6ffGTMBUjh6tjZFB3vU2qhGvyRC`

### 5. REDIS_PASSWORD (Required)
Redis password for caching.

**Setup**:
1. Generate using: `openssl rand -base64 32`
2. Add as GitHub secret:
   - Name: `REDIS_PASSWORD`
   - Value: Your generated password

## Quick Setup Script

Run this script to see all required values:

```bash
#!/bin/bash

echo "=== GitHub Secrets Values ==="
echo ""
echo "1. SSH_PRIVATE_KEY:"
echo "   Copy from: bootstrap-awareness private key.txt"
echo ""
echo "2. DB_PASSWORD:"
echo "   nTcd+XAQ+xUbUbNlU7MNr3rYUWKldLXnj6O/k633daY="
echo ""
echo "3. SECRET_KEY:"
echo "   8eb9afc6e39da58b95628f1505bf1107c7f9f0243990d7acd4ba23f82694b1e5"
echo ""
echo "4. EMAIL_PASSWORD:"
echo "   5X58dee2u3ov6ffGTMBUjh6tjZFB3vU2qhGvyRC"
echo ""
echo "5. REDIS_PASSWORD:"
echo "   redis_595e9ffc5e32e7fc6d8cbae32a9e610c"
echo ""
echo "Save these values and add them as GitHub secrets!"
```

## Verification

After adding all secrets:
1. Go to Settings → Secrets and variables → Actions
2. You should see:
   - SSH_PRIVATE_KEY
   - DB_PASSWORD
   - SECRET_KEY
   - EMAIL_PASSWORD
   - REDIS_PASSWORD

## Deployment

Once secrets are configured:
1. Push code to the `main` branch
2. GitHub Actions will automatically:
   - Run tests
   - Build Docker images
   - Deploy to production
   - Run health checks

## Troubleshooting

If deployment fails:
1. Check Actions tab for error logs
2. Verify all secrets are set correctly
3. Ensure server IP (83.228.205.20) is accessible
4. Check that SSH key has correct permissions

## Security Notes

- Never commit secrets to the repository
- Rotate secrets regularly
- Use strong, unique passwords
- Limit access to GitHub secrets to trusted team members