#!/bin/bash
# Script to validate GitHub Actions workflow configurations

set -e

echo "=== GitHub Actions Workflow Validation ==="
echo

# Check if required files exist
echo "Checking for required workflow files..."
REQUIRED_WORKFLOWS=(
    ".github/workflows/ci-cd.yml"
    ".github/workflows/e2e-tests.yml"
    ".github/workflows/deploy.yml"
    ".github/workflows/pr-checks.yml"
    ".github/workflows/security-scan.yml"
)

for workflow in "${REQUIRED_WORKFLOWS[@]}"; do
    if [ -f "$workflow" ]; then
        echo "✓ Found: $workflow"
    else
        echo "✗ Missing: $workflow"
        exit 1
    fi
done

echo
echo "Checking for required environment variables in workflows..."

# Function to check environment variables in a workflow
check_env_vars() {
    local file=$1
    local required_vars=$2
    
    echo "Checking $file..."
    
    for var in $required_vars; do
        if grep -q "$var" "$file"; then
            echo "  ✓ $var"
        else
            echo "  ✗ Missing: $var"
            MISSING_VARS=true
        fi
    done
}

# Required environment variables for backend tests
BACKEND_TEST_VARS="DATABASE_URL REDIS_URL SECRET_KEY FRONTEND_URL ENVIRONMENT CORS_ORIGINS EMAIL_FROM SMTP_FROM_EMAIL"

# Check CI/CD workflow
check_env_vars ".github/workflows/ci-cd.yml" "$BACKEND_TEST_VARS"

# Check E2E tests workflow
check_env_vars ".github/workflows/e2e-tests.yml" "$BACKEND_TEST_VARS BACKEND_URL"

echo
echo "Checking for database migration handling..."

# Check for migration retry logic
for workflow in ".github/workflows/ci-cd.yml" ".github/workflows/e2e-tests.yml"; do
    if grep -q "retry_count" "$workflow"; then
        echo "✓ $workflow has migration retry logic"
    else
        echo "✗ $workflow missing migration retry logic"
    fi
done

echo
echo "Checking for proper error handling..."

# Check for proper error handling patterns
for workflow in "${REQUIRED_WORKFLOWS[@]}"; do
    if grep -q "|| exit 1\||| echo" "$workflow"; then
        echo "✓ $workflow has error handling"
    else
        echo "⚠ $workflow may lack proper error handling"
    fi
done

echo
echo "Checking for pytest-asyncio installation..."

# Check if pytest-asyncio is installed in test workflows
for workflow in ".github/workflows/ci-cd.yml" ".github/workflows/e2e-tests.yml"; do
    if grep -q "pytest-asyncio" "$workflow"; then
        echo "✓ $workflow installs pytest-asyncio"
    else
        echo "✗ $workflow missing pytest-asyncio installation"
    fi
done

echo
echo "Checking for duplicate workflow files..."

# Check for duplicates in subdirectories
if [ -d "cybersecurity-platform/.github/workflows" ]; then
    echo "✗ Found duplicate workflows in cybersecurity-platform/.github/workflows"
    echo "  Please remove to avoid confusion"
else
    echo "✓ No duplicate workflow directories found"
fi

echo
echo "=== Validation Complete ==="

if [ "$MISSING_VARS" = true ]; then
    echo "⚠ Some environment variables are missing. Please review and update workflows."
    exit 1
else
    echo "✓ All checks passed!"
fi