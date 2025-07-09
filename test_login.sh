#!/bin/bash

echo "Testing login with admin credentials..."
echo "========================================="

# Test login endpoint
response=$(curl -s -X POST https://bootstrap-awareness.de/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@bootstrap-awareness.de&password=SecureAdminPassword123!" \
  -w "\n\nHTTP Status: %{http_code}\n")

echo "Response:"
echo "$response" | head -n -2

# Extract HTTP status
http_status=$(echo "$response" | tail -n 1 | grep -oE '[0-9]+')

echo ""
echo "========================================="

# Check if login was successful
if echo "$response" | grep -q "access_token"; then
    echo "✅ Login successful! Tokens received."
    
    # Extract access token
    access_token=$(echo "$response" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    
    if [ ! -z "$access_token" ]; then
        echo ""
        echo "Testing authenticated endpoint..."
        echo "========================================="
        
        # Test with token
        user_response=$(curl -s -X GET https://bootstrap-awareness.de/api/users/me \
          -H "Authorization: Bearer $access_token" \
          -w "\n\nHTTP Status: %{http_code}\n")
        
        echo "User info response:"
        echo "$user_response"
    fi
else
    echo "❌ Login failed. HTTP Status: $http_status"
    echo ""
    echo "Possible reasons:"
    echo "1. Admin user doesn't exist yet"
    echo "2. Wrong credentials"
    echo "3. Server/database issue"
    
    # Try to get more details
    echo ""
    echo "Testing if API is accessible..."
    health_check=$(curl -s -X GET https://bootstrap-awareness.de/api/health \
      -w "\n\nHTTP Status: %{http_code}\n")
    echo "Health check response:"
    echo "$health_check"
fi