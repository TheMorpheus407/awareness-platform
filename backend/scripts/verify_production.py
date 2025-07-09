#!/usr/bin/env python3
"""Verify production is working properly."""

import requests
import json
from datetime import datetime

BASE_URL = "https://bootstrap-awareness.de"

def check_endpoint(name, url, method="GET", data=None, headers=None):
    """Check an endpoint and return status."""
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, data=data, headers=headers)
        else:
            response = requests.request(method, url, data=data, headers=headers)
        
        print(f"{name}: {response.status_code}")
        if response.status_code >= 200 and response.status_code < 300:
            print(f"  ✓ Success")
            if response.headers.get('content-type', '').startswith('application/json'):
                print(f"  Response: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"  ✗ Failed")
            print(f"  Response: {response.text[:200]}")
        return response.status_code
    except Exception as e:
        print(f"{name}: ERROR - {e}")
        return 0

print("=" * 60)
print("BOOTSTRAP AWARENESS PLATFORM - PRODUCTION VERIFICATION")
print(f"Time: {datetime.now()}")
print("=" * 60)
print()

# Check main endpoints
print("1. CHECKING MAIN ENDPOINTS:")
print("-" * 30)
check_endpoint("Frontend", BASE_URL)
check_endpoint("API Health", f"{BASE_URL}/api/health")
check_endpoint("API Root", f"{BASE_URL}/api/")

print("\n2. CHECKING AUTHENTICATION:")
print("-" * 30)
# Try form login
form_data = {
    "username": "admin@bootstrap-awareness.de",
    "password": "SecureAdminPassword123!"
}
headers = {"Content-Type": "application/x-www-form-urlencoded"}
status = check_endpoint("Login (Form)", f"{BASE_URL}/api/auth/login", "POST", form_data, headers)

print("\n3. CHECKING CORS:")
print("-" * 30)
# Check OPTIONS for CORS
options_headers = {
    "Origin": "https://bootstrap-awareness.de",
    "Access-Control-Request-Method": "GET",
    "Access-Control-Request-Headers": "Content-Type"
}
response = requests.options(f"{BASE_URL}/api/health", headers=options_headers)
print(f"OPTIONS request: {response.status_code}")
cors_headers = {k.lower(): v for k, v in response.headers.items()}
if 'access-control-allow-origin' in cors_headers:
    print(f"  ✓ CORS enabled: {cors_headers['access-control-allow-origin']}")
else:
    print("  ✗ CORS not properly configured")

print("\n4. CHECKING SECURITY HEADERS:")
print("-" * 30)
response = requests.get(f"{BASE_URL}/api/health")
security_headers = ['x-content-type-options', 'x-frame-options', 'strict-transport-security']
for header in security_headers:
    if header in response.headers:
        print(f"  ✓ {header}: {response.headers[header]}")
    else:
        print(f"  ✗ {header}: Missing")

print("\n" + "=" * 60)
print("VERIFICATION COMPLETE")
print("=" * 60)