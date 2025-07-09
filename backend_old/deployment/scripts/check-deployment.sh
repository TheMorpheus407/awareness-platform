#!/bin/bash
# Quick deployment verification script

echo "=== Deployment Status Check ==="
echo

# Check API health
echo "1. Checking API Health..."
API_RESPONSE=$(curl -s -w "\n%{http_code}" https://bootstrap-awareness.de/api/health 2>/dev/null)
HTTP_CODE=$(echo "$API_RESPONSE" | tail -1)
BODY=$(echo "$API_RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ API is healthy"
    echo "Response: $BODY"
else
    echo "❌ API health check failed (HTTP $HTTP_CODE)"
fi
echo

# Check frontend
echo "2. Checking Frontend..."
FRONTEND_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://bootstrap-awareness.de 2>/dev/null)
if [ "$FRONTEND_CODE" = "200" ] || [ "$FRONTEND_CODE" = "304" ]; then
    echo "✅ Frontend is accessible (HTTP $FRONTEND_CODE)"
else
    echo "❌ Frontend check failed (HTTP $FRONTEND_CODE)"
fi
echo

# Check SSL certificate
echo "3. Checking SSL Certificate..."
CERT_INFO=$(echo | openssl s_client -servername bootstrap-awareness.de -connect bootstrap-awareness.de:443 2>/dev/null | openssl x509 -noout -dates 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "✅ SSL certificate is valid"
    echo "$CERT_INFO"
else
    echo "❌ SSL certificate check failed"
fi
echo

# Check GitHub Actions status
echo "4. Latest GitHub Actions Status..."
LATEST_RUN=$(curl -s https://api.github.com/repos/TheMorpheus407/awareness-platform/actions/runs?per_page=1 | jq -r '.workflow_runs[0] | "Name: \(.name)\nStatus: \(.status)\nConclusion: \(.conclusion)\nCreated: \(.created_at)"')
echo "$LATEST_RUN"
echo

echo "=== Check Complete ===