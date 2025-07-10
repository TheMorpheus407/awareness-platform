#!/bin/bash

# Pre-deployment checklist script
# Ensures all prerequisites are met before deployment

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Results tracking
CHECKS_PASSED=0
CHECKS_FAILED=0
WARNINGS=0

echo -e "${BLUE}=== Pre-Deployment Checklist ===${NC}"
echo "Running comprehensive checks before deployment..."
echo ""

# Function to run a check
run_check() {
    local check_name="$1"
    local check_command="$2"
    local is_critical="${3:-true}"
    
    echo -n "Checking: $check_name... "
    
    if eval "$check_command" &>/dev/null; then
        echo -e "${GREEN}✓ PASSED${NC}"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
        return 0
    else
        if [ "$is_critical" = "true" ]; then
            echo -e "${RED}✗ FAILED (CRITICAL)${NC}"
            CHECKS_FAILED=$((CHECKS_FAILED + 1))
            return 1
        else
            echo -e "${YELLOW}⚠ WARNING${NC}"
            WARNINGS=$((WARNINGS + 1))
            return 0
        fi
    fi
}

# 1. Check Git status
echo -e "${BLUE}1. Git Repository Checks${NC}"
run_check "Clean working directory" "git diff --quiet && git diff --cached --quiet" false
run_check "On main branch" "[[ $(git branch --show-current) == 'main' ]]" true
run_check "Up to date with origin" "git fetch && git status | grep -q 'Your branch is up to date'" true

# 2. Check CI/CD status
echo -e "\n${BLUE}2. CI/CD Pipeline Checks${NC}"
if command -v gh &> /dev/null; then
    run_check "Latest CI/CD workflow passed" "gh run list --workflow=ci-cd.yml --branch=main --limit=1 --json conclusion | jq -r '.[0].conclusion' | grep -q 'success'" true
    run_check "No active deployments" "! gh run list --workflow=deploy.yml --status=in_progress --json status | jq -r '.[].status' | grep -q 'in_progress'" true
else
    echo -e "${YELLOW}⚠ GitHub CLI not installed, skipping workflow checks${NC}"
    WARNINGS=$((WARNINGS + 1))
fi

# 3. Check Docker images
echo -e "\n${BLUE}3. Docker Image Checks${NC}"
run_check "Backend image exists" "docker images | grep -q 'awareness.*backend'" true
run_check "Frontend image exists" "docker images | grep -q 'awareness.*frontend'" true
run_check "Docker daemon running" "docker info" true

# 4. Check environment files
echo -e "\n${BLUE}4. Environment Configuration Checks${NC}"
run_check ".env.production template exists" "[[ -f deployment/.env.production.template ]]" true
run_check "Docker Compose production file exists" "[[ -f docker-compose.prod.ghcr.yml ]]" true
run_check "Deployment scripts exist" "[[ -f deployment/scripts/deploy-production.sh ]]" true

# 5. Check required secrets (can't check values, just existence of files)
echo -e "\n${BLUE}5. Configuration File Checks${NC}"
run_check "Nginx configuration exists" "[[ -f deployment/nginx/sites-enabled/awareness-platform.conf ]]" false
run_check "SSL certificates configured" "grep -q 'ssl_certificate' deployment/nginx/sites-enabled/awareness-platform.conf" false

# 6. Check database migrations
echo -e "\n${BLUE}6. Database Migration Checks${NC}"
run_check "Alembic configuration exists" "[[ -f backend/alembic.ini ]]" true
run_check "Migration directory exists" "[[ -d backend/alembic/versions ]]" true
run_check "No pending migrations locally" "cd backend && alembic check &>/dev/null" false

# 7. Check test coverage
echo -e "\n${BLUE}7. Test Coverage Checks${NC}"
if [ -f backend/coverage.xml ]; then
    coverage_percent=$(python3 -c "import xml.etree.ElementTree as ET; tree = ET.parse('backend/coverage.xml'); root = tree.getroot(); print(int(float(root.get('line-rate', '0')) * 100))" 2>/dev/null || echo "0")
    if [ "$coverage_percent" -ge 60 ]; then
        echo -e "Backend coverage: ${GREEN}${coverage_percent}%${NC} ✓"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    else
        echo -e "Backend coverage: ${YELLOW}${coverage_percent}%${NC} (below 60% threshold) ⚠"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo -e "${YELLOW}⚠ No backend coverage report found${NC}"
    WARNINGS=$((WARNINGS + 1))
fi

# 8. Check resource availability
echo -e "\n${BLUE}8. System Resource Checks${NC}"
run_check "Sufficient disk space (>5GB)" "[[ $(df -BG / | awk 'NR==2 {print $4}' | sed 's/G//') -gt 5 ]]" true
run_check "Docker disk space available" "[[ $(docker system df | grep 'Images' | awk '{print $4}' | sed 's/GB//') -lt 50 ]]" false

# 9. Security checks
echo -e "\n${BLUE}9. Security Checks${NC}"
run_check "No hardcoded secrets in code" "! grep -r 'password.*=.*[\"'\''][^\"'\'']*[\"'\'']' --include='*.py' --include='*.js' --include='*.ts' backend/ frontend/ 2>/dev/null | grep -v -E '(test|example|dummy|placeholder)'" true
run_check "Environment variables not committed" "! git ls-files | grep -E '\.env$|\.env\.production$'" true

# Summary
echo -e "\n${BLUE}=== Pre-Deployment Check Summary ===${NC}"
echo -e "Checks passed: ${GREEN}${CHECKS_PASSED}${NC}"
echo -e "Checks failed: ${RED}${CHECKS_FAILED}${NC}"
echo -e "Warnings: ${YELLOW}${WARNINGS}${NC}"

if [ $CHECKS_FAILED -gt 0 ]; then
    echo -e "\n${RED}❌ DEPLOYMENT BLOCKED: Critical checks failed!${NC}"
    echo "Please fix the failed checks before proceeding with deployment."
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo -e "\n${YELLOW}⚠️  PROCEED WITH CAUTION: Some warnings detected${NC}"
    echo "Review the warnings and ensure they won't impact deployment."
    exit 0
else
    echo -e "\n${GREEN}✅ ALL CHECKS PASSED: Ready for deployment!${NC}"
    exit 0
fi