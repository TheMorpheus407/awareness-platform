#!/bin/bash

echo "=== Cybersecurity Awareness Platform Login Diagnostics ==="
echo ""

# 1. Check if API is accessible
echo "1. Checking API health..."
health_response=$(curl -s -X GET https://bootstrap-awareness.de/api/health -w "\nHTTP_STATUS:%{http_code}")
health_status=$(echo "$health_response" | grep HTTP_STATUS | cut -d: -f2)
health_body=$(echo "$health_response" | grep -v HTTP_STATUS)

echo "Health check status: $health_status"
echo "Response: $health_body"
echo ""

# 2. Test login endpoint with verbose error handling
echo "2. Testing login endpoint..."
login_response=$(curl -s -X POST https://bootstrap-awareness.de/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@bootstrap-awareness.de&password=SecureAdminPassword123!" \
  -w "\nHTTP_STATUS:%{http_code}" \
  -v 2>&1)

login_status=$(echo "$login_response" | grep HTTP_STATUS | tail -1 | cut -d: -f2)
login_body=$(echo "$login_response" | grep -v HTTP_STATUS | grep -v "^[*<>]" | tail -1)

echo "Login status: $login_status"
echo "Response: $login_body"
echo ""

# 3. Check if login endpoint exists
echo "3. Checking if login endpoint exists..."
options_response=$(curl -s -X OPTIONS https://bootstrap-awareness.de/api/auth/login -w "\nHTTP_STATUS:%{http_code}")
options_status=$(echo "$options_response" | grep HTTP_STATUS | cut -d: -f2)
echo "OPTIONS request status: $options_status"
echo ""

# 4. Test with different content types
echo "4. Testing with JSON content type..."
json_response=$(curl -s -X POST https://bootstrap-awareness.de/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin@bootstrap-awareness.de","password":"SecureAdminPassword123!"}' \
  -w "\nHTTP_STATUS:%{http_code}")

json_status=$(echo "$json_response" | grep HTTP_STATUS | cut -d: -f2)
json_body=$(echo "$json_response" | grep -v HTTP_STATUS)

echo "JSON login status: $json_status"
echo "Response: $json_body"
echo ""

# 5. Check API documentation
echo "5. Checking for API documentation..."
docs_response=$(curl -s -X GET https://bootstrap-awareness.de/api/docs -w "\nHTTP_STATUS:%{http_code}")
docs_status=$(echo "$docs_response" | grep HTTP_STATUS | cut -d: -f2)
echo "API docs status: $docs_status"

if [ "$docs_status" = "200" ]; then
    echo "API documentation is available at: https://bootstrap-awareness.de/api/docs"
fi
echo ""

# Summary
echo "=== Summary ==="
if [ "$health_status" = "200" ]; then
    echo "✅ API is accessible and healthy"
else
    echo "❌ API health check failed"
fi

if [ "$login_status" = "200" ] || [ "$login_status" = "201" ]; then
    echo "✅ Login successful"
elif [ "$login_status" = "401" ] || [ "$login_status" = "403" ]; then
    echo "❌ Authentication failed - admin user may not exist or wrong credentials"
elif [ "$login_status" = "500" ]; then
    echo "❌ Internal server error - check backend logs"
elif [ "$login_status" = "404" ]; then
    echo "❌ Login endpoint not found - check API routing"
else
    echo "❌ Unexpected status: $login_status"
fi

echo ""
echo "Next steps:"
echo "1. SSH to your server and check backend logs: docker logs awareness-backend --tail 50"
echo "2. Run the admin creation script on the server (see admin_setup_instructions.md)"
echo "3. Verify database connectivity: docker exec awareness-backend python -c \"from db.session import SessionLocal; print('DB OK')\""