#!/bin/bash
# Continuous health monitoring script

while true; do
    echo "=== Health Check $(date) ==="
    
    # Check API
    API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://bootstrap-awareness.de/api/health)
    if [ "$API_STATUS" = "200" ]; then
        echo "✅ API: OK"
    else
        echo "❌ API: Failed (HTTP $API_STATUS)"
    fi
    
    # Check Frontend
    FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://bootstrap-awareness.de)
    if [ "$FRONTEND_STATUS" = "200" ]; then
        echo "✅ Frontend: OK"
    else
        echo "❌ Frontend: Failed (HTTP $FRONTEND_STATUS)"
    fi
    
    # Check SSL
    SSL_CHECK=$(echo | openssl s_client -servername bootstrap-awareness.de -connect bootstrap-awareness.de:443 2>/dev/null | grep "Verify return code: 0")
    if [ -n "$SSL_CHECK" ]; then
        echo "✅ SSL: Valid"
    else
        echo "❌ SSL: Invalid"
    fi
    
    echo
    sleep 60
done