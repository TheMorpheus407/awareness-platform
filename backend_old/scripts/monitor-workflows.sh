#!/bin/bash

echo "🚀 Monitoring GitHub Actions Workflows..."
echo "=================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check workflow status
check_workflows() {
    echo -e "\n📊 Current Workflow Status:"
    echo "-------------------------"
    
    # Get all workflow runs
    gh run list --limit=10 --json status,name,conclusion,workflowName,createdAt | \
    jq -r '.[] | "\(.status)\t\(.conclusion // "running")\t\(.workflowName)\t\(.name)"' | \
    while IFS=$'\t' read -r status conclusion workflow name; do
        case "$status" in
            "completed")
                if [ "$conclusion" = "success" ]; then
                    echo -e "${GREEN}✅ $workflow - $name${NC}"
                else
                    echo -e "${RED}❌ $workflow - $name (${conclusion})${NC}"
                fi
                ;;
            "in_progress")
                echo -e "${YELLOW}🔄 $workflow - $name${NC}"
                ;;
            "queued")
                echo -e "⏳ $workflow - $name"
                ;;
            *)
                echo "❓ $workflow - $name ($status)"
                ;;
        esac
    done
}

# Main monitoring loop
while true; do
    clear
    echo "🚀 GitHub Actions Workflow Monitor"
    echo "=================================="
    echo "Repository: TheMorpheus407/awareness-platform"
    echo "Time: $(date)"
    
    check_workflows
    
    # Check if CI/CD pipeline is complete
    ci_status=$(gh run list --workflow=ci-cd.yml --limit=1 --json status,conclusion | jq -r '.[0] | "\(.status):\(.conclusion // "running")"')
    
    echo -e "\n📌 CI/CD Pipeline Status: $ci_status"
    
    if [[ "$ci_status" == "completed:success" ]]; then
        echo -e "\n${GREEN}🎉 CI/CD Pipeline completed successfully!${NC}"
        echo "Deployment should be triggered automatically."
        break
    elif [[ "$ci_status" == "completed:failure" ]]; then
        echo -e "\n${RED}❌ CI/CD Pipeline failed!${NC}"
        echo "Check the logs for details: gh run view"
        break
    fi
    
    echo -e "\nPress Ctrl+C to stop monitoring..."
    sleep 30
done