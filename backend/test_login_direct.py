#!/usr/bin/env python3
"""Direct test of login functionality"""
import requests
import json

# Test different login formats
print("Testing login endpoint...")

# Test 1: OAuth2 form format
print("\n1. Testing OAuth2 form format:")
response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    data={
        "username": "admin@bootstrap-academy.com",
        "password": "admin123"
    }
)
print(f"Status: {response.status_code}")
print(f"Response: {response.text[:200]}")

# Test 2: JSON format
print("\n2. Testing JSON format:")
response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    json={
        "email": "admin@bootstrap-academy.com",
        "password": "admin123"
    },
    headers={"Content-Type": "application/json"}
)
print(f"Status: {response.status_code}")
print(f"Response: {response.text[:200]}")

# Test 3: Check available endpoints
print("\n3. Checking available endpoints:")
response = requests.get("http://localhost:8000/api/docs")
if response.status_code == 200:
    print("API docs available at: http://localhost:8000/api/docs")
else:
    print("API docs not available")

# Test 4: Check root
print("\n4. Checking root endpoint:")
response = requests.get("http://localhost:8000/")
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")

# Test 5: Check if there's a different auth endpoint
print("\n5. Checking for auth endpoints:")
for endpoint in ["/api/auth/login", "/auth/login", "/api/v1/auth/login", "/api/login"]:
    response = requests.options(f"http://localhost:8000{endpoint}")
    print(f"{endpoint}: {response.status_code}")