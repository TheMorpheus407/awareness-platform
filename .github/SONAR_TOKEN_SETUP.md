# SonarCloud Token Setup

## Issue
The Quality Gates workflow is failing because the `SONAR_TOKEN` environment variable is missing.

## Solution
You need to add the `SONAR_TOKEN` secret to your GitHub repository settings.

### Steps to fix:

1. **Get a SonarCloud token:**
   - Go to https://sonarcloud.io/
   - Log in with your GitHub account
   - Go to My Account > Security > Generate Tokens
   - Generate a new token and copy it

2. **Add the token to GitHub:**
   - Go to your repository on GitHub
   - Navigate to Settings > Secrets and variables > Actions
   - Click "New repository secret"
   - Name: `SONAR_TOKEN`
   - Value: Paste the token from SonarCloud
   - Click "Add secret"

3. **Alternative: Disable SonarCloud (if not needed)**
   If you don't need SonarCloud analysis, you can comment out or remove the SonarCloud scan step in `.github/workflows/quality-gates.yml`

## Verification
After adding the secret, re-run the failed workflow to verify it works correctly.