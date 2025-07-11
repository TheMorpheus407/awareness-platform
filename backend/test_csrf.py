#!/usr/bin/env python3
"""
Test script for CSRF protection implementation.
"""

import asyncio
import httpx
import json
from urllib.parse import urljoin

BASE_URL = "http://localhost:8000"


async def test_csrf_protection():
    """Test CSRF protection implementation."""
    async with httpx.AsyncClient() as client:
        print("Testing CSRF Protection Implementation\n" + "=" * 50)
        
        # Test 1: Get CSRF token
        print("\n1. Testing CSRF token endpoint...")
        try:
            response = await client.get(urljoin(BASE_URL, "/api/v1/auth/csrf-token"))
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                csrf_token = data.get("csrf_token")
                print(f"   CSRF Token: {csrf_token[:20]}...")
                print(f"   Header Name: {data.get('header_name')}")
                print(f"   Cookie Name: {data.get('cookie_name')}")
                print("   ✓ CSRF token endpoint working")
                
                # Check if cookie was set
                csrf_cookie = response.cookies.get("csrf_token")
                if csrf_cookie:
                    print(f"   ✓ CSRF cookie set: {csrf_cookie[:20]}...")
                else:
                    print("   ✗ CSRF cookie not found")
            else:
                print(f"   ✗ Failed to get CSRF token: {response.text}")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        
        # Test 2: Test GET request (should not require CSRF)
        print("\n2. Testing GET request (no CSRF required)...")
        try:
            response = await client.get(urljoin(BASE_URL, "/api/health"))
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print("   ✓ GET request successful without CSRF token")
            else:
                print(f"   ✗ GET request failed: {response.text}")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        
        # Test 3: Test POST without CSRF token (should fail)
        print("\n3. Testing POST request without CSRF token...")
        try:
            response = await client.post(
                urljoin(BASE_URL, "/api/v1/users/test"),
                json={"test": "data"}
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 403:
                print("   ✓ POST request correctly rejected without CSRF token")
                error_detail = response.json().get("detail", "")
                print(f"   Error: {error_detail}")
            else:
                print(f"   ✗ POST request should have been rejected: {response.text}")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        
        # Test 4: Get CSRF token and test POST with token
        print("\n4. Testing POST request with CSRF token...")
        try:
            # First get CSRF token
            token_response = await client.get(urljoin(BASE_URL, "/api/v1/auth/csrf-token"))
            if token_response.status_code == 200:
                csrf_data = token_response.json()
                csrf_token = csrf_data.get("csrf_token")
                
                # Now test POST with CSRF token
                headers = {"X-CSRF-Token": csrf_token}
                cookies = token_response.cookies
                
                response = await client.post(
                    urljoin(BASE_URL, "/api/v1/users/test"),
                    json={"test": "data"},
                    headers=headers,
                    cookies=cookies
                )
                print(f"   Status: {response.status_code}")
                if response.status_code != 403:
                    print("   ✓ POST request with CSRF token processed")
                else:
                    print(f"   ✗ POST request rejected even with CSRF token: {response.text}")
            else:
                print("   ✗ Failed to get CSRF token for test")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        
        # Test 5: Test excluded paths (login should work without CSRF)
        print("\n5. Testing excluded path (login)...")
        try:
            response = await client.post(
                urljoin(BASE_URL, "/api/v1/auth/login"),
                data={"username": "test@example.com", "password": "wrongpassword"}
            )
            print(f"   Status: {response.status_code}")
            if response.status_code != 403:
                print("   ✓ Login endpoint accessible without CSRF token")
            else:
                print("   ✗ Login endpoint should not require CSRF token")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        
        print("\n" + "=" * 50)
        print("CSRF Protection Test Complete")


if __name__ == "__main__":
    asyncio.run(test_csrf_protection())