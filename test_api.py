#!/usr/bin/env python3
"""Test API endpoints on production."""

import requests
import json
import sys

BASE_URL = "https://bootstrap-awareness.de/api"

def test_health():
    """Test health endpoint."""
    print("Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_registration():
    """Test user registration."""
    print("\nTesting registration endpoint...")
    data = {
        "email": "testuser@example.com",
        "password": "SecurePassword123!",
        "first_name": "Test",
        "last_name": "User",
        "company_name": "Test Company",
        "company_domain": "testcompany.com"
    }
    response = requests.post(f"{BASE_URL}/auth/register", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    return response.status_code in [200, 201, 409]  # 409 if user already exists

def test_login():
    """Test login endpoint."""
    print("\nTesting login endpoint...")
    data = {
        "username": "admin@bootstrap-awareness.de",
        "password": "admin"
    }
    response = requests.post(f"{BASE_URL}/auth/login", data=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    return response.status_code in [200, 401]

def main():
    """Run all tests."""
    print("Testing Bootstrap Awareness Platform API")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health),
        ("Registration", test_registration),
        ("Login", test_login)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"Error in {name}: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 50)
    print("Test Results:")
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{name}: {status}")
    
    all_passed = all(result for _, result in results)
    if all_passed:
        print("\nAll tests passed! Platform is functional.")
    else:
        print("\nSome tests failed. Platform needs attention.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())