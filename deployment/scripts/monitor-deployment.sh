#!/bin/bash

# Deployment Health Monitoring Script
# This script monitors the health of the deployed application and can trigger automatic rollback

set -euo pipefail

# Configuration
API_URL="https://bootstrap-awareness.de/api"
HEALTH_ENDPOINT="${API_URL}/health"
MONITORING_DURATION=300  # 5 minutes
CHECK_INTERVAL=30       # Check every 30 seconds
ERROR_THRESHOLD=3       # Number of consecutive failures before rollback
WEBHOOK_URL="${GITHUB_WEBHOOK_URL:-}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
consecutive_failures=0
total_checks=0
successful_checks=0

echo -e "${GREEN}Starting deployment monitoring...${NC}"
echo "Duration: ${MONITORING_DURATION}s, Check interval: ${CHECK_INTERVAL}s"
echo "Error threshold: ${ERROR_THRESHOLD} consecutive failures"
echo "----------------------------------------"

# Function to check health
check_health() {
    local response
    local http_code
    
    # Use curl with timeout
    response=$(curl -s -w "\n%{http_code}" --connect-timeout 5 --max-time 10 "${HEALTH_ENDPOINT}" 2>/dev/null || echo "000")
    http_code=$(echo "$response" | tail -n1)
    
    if [ "$http_code" = "200" ]; then
        return 0
    else
        return 1
    fi
}

# Function to trigger rollback via GitHub Actions
trigger_rollback() {
    local reason="$1"
    
    echo -e "${RED}CRITICAL: Triggering automatic rollback!${NC}"
    echo "Reason: $reason"
    
    if [ -n "$WEBHOOK_URL" ]; then
        # Trigger rollback workflow via webhook
        curl -X POST "$WEBHOOK_URL" \
            -H "Content-Type: application/json" \
            -d "{
                \"event_type\": \"rollback-deployment\",
                \"client_payload\": {
                    \"reason\": \"$reason\",
                    \"auto_rollback\": true
                }
            }"
    else
        echo "Warning: GITHUB_WEBHOOK_URL not set, cannot trigger automatic rollback"
        exit 1
    fi
}

# Function to check additional endpoints
check_critical_endpoints() {
    local endpoints=(
        "/docs"
        "/auth/status"
        "/companies"
    )
    
    local failed_endpoints=()
    
    for endpoint in "${endpoints[@]}"; do
        local full_url="${API_URL}${endpoint}"
        local http_code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 "$full_url" 2>/dev/null || echo "000")
        
        # Check for success (2xx) or expected auth failure (401)
        if [[ ! "$http_code" =~ ^(2[0-9]{2}|401)$ ]]; then
            failed_endpoints+=("$endpoint (HTTP $http_code)")
        fi
    done
    
    if [ ${#failed_endpoints[@]} -gt 0 ]; then
        echo -e "${YELLOW}Warning: Critical endpoints failing:${NC}"
        printf '%s\n' "${failed_endpoints[@]}"
        return 1
    fi
    
    return 0
}

# Main monitoring loop
start_time=$(date +%s)
end_time=$((start_time + MONITORING_DURATION))

while [ $(date +%s) -lt $end_time ]; do
    total_checks=$((total_checks + 1))
    
    echo -n "Check #${total_checks} at $(date '+%Y-%m-%d %H:%M:%S'): "
    
    if check_health; then
        echo -e "${GREEN}✓ Health check passed${NC}"
        consecutive_failures=0
        successful_checks=$((successful_checks + 1))
        
        # Also check critical endpoints
        if ! check_critical_endpoints; then
            consecutive_failures=$((consecutive_failures + 1))
        fi
    else
        echo -e "${RED}✗ Health check failed${NC}"
        consecutive_failures=$((consecutive_failures + 1))
    fi
    
    # Check if we've hit the error threshold
    if [ $consecutive_failures -ge $ERROR_THRESHOLD ]; then
        echo -e "${RED}ERROR THRESHOLD REACHED!${NC}"
        trigger_rollback "Health checks failed $consecutive_failures times consecutively"
        exit 1
    fi
    
    # Show current status
    success_rate=$((successful_checks * 100 / total_checks))
    echo "Status: Success rate: ${success_rate}%, Consecutive failures: ${consecutive_failures}/${ERROR_THRESHOLD}"
    echo "----------------------------------------"
    
    # Wait before next check (unless we're at the end)
    if [ $(date +%s) -lt $((end_time - CHECK_INTERVAL)) ]; then
        sleep $CHECK_INTERVAL
    else
        break
    fi
done

# Final report
echo -e "\n${GREEN}Monitoring completed!${NC}"
echo "Total checks: ${total_checks}"
echo "Successful checks: ${successful_checks}"
echo "Success rate: ${success_rate}%"

if [ $success_rate -lt 95 ]; then
    echo -e "${YELLOW}Warning: Success rate below 95%${NC}"
    exit 2
fi

echo -e "${GREEN}Deployment is healthy!${NC}"
exit 0