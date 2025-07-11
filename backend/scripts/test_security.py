#!/usr/bin/env python3
"""Test script to verify security headers and features."""

import asyncio
import httpx
import json
from typing import Dict, List
from datetime import datetime


class SecurityTester:
    """Test security features of the application."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(follow_redirects=False)
        self.results = []
    
    async def test_security_headers(self):
        """Test if security headers are properly set."""
        print("\n🔒 Testing Security Headers...")
        
        response = await self.client.get(f"{self.base_url}/")
        
        required_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": None,  # Just check existence
            "Permissions-Policy": None,
            "Cross-Origin-Embedder-Policy": "require-corp",
            "Cross-Origin-Opener-Policy": "same-origin",
            "Cross-Origin-Resource-Policy": "same-origin",
        }
        
        passed = 0
        failed = 0
        
        for header, expected_value in required_headers.items():
            actual_value = response.headers.get(header)
            
            if actual_value:
                if expected_value is None or actual_value == expected_value:
                    print(f"  ✅ {header}: {actual_value[:50]}{'...' if len(actual_value) > 50 else ''}")
                    passed += 1
                else:
                    print(f"  ❌ {header}: Expected '{expected_value}', got '{actual_value}'")
                    failed += 1
            else:
                print(f"  ❌ {header}: Missing")
                failed += 1
        
        self.results.append({
            "test": "Security Headers",
            "passed": passed,
            "failed": failed,
            "total": len(required_headers)
        })
    
    async def test_csrf_protection(self):
        """Test CSRF protection."""
        print("\n🛡️  Testing CSRF Protection...")
        
        # Get CSRF token
        response = await self.client.get(f"{self.base_url}/api/v1/auth/csrf-token")
        
        if response.status_code == 200:
            print("  ✅ CSRF token endpoint accessible")
            
            # Check if token is in cookies
            csrf_cookie = response.cookies.get("csrf_token")
            if csrf_cookie:
                print("  ✅ CSRF token cookie set")
            else:
                print("  ❌ CSRF token cookie not set")
            
            # Test POST without CSRF token
            response = await self.client.post(
                f"{self.base_url}/api/v1/auth/login",
                json={"username": "test@example.com", "password": "test"}
            )
            
            if response.status_code == 403 and "CSRF" in response.text:
                print("  ✅ POST request blocked without CSRF token")
            else:
                print("  ⚠️  POST request not blocked (might be excluded endpoint)")
        else:
            print("  ❌ CSRF token endpoint not accessible")
    
    async def test_rate_limiting(self):
        """Test rate limiting."""
        print("\n⏱️  Testing Rate Limiting...")
        
        # Make multiple rapid requests
        endpoint = f"{self.base_url}/api/v1/auth/login"
        request_count = 0
        rate_limited = False
        
        for i in range(20):
            response = await self.client.post(
                endpoint,
                json={"username": f"test{i}@example.com", "password": "wrong"}
            )
            
            request_count += 1
            
            if response.status_code == 429:
                rate_limited = True
                print(f"  ✅ Rate limited after {request_count} requests")
                
                # Check rate limit headers
                retry_after = response.headers.get("Retry-After")
                rate_limit_remaining = response.headers.get("X-RateLimit-Remaining")
                
                if retry_after:
                    print(f"  ✅ Retry-After header: {retry_after}")
                if rate_limit_remaining:
                    print(f"  ✅ X-RateLimit-Remaining header: {rate_limit_remaining}")
                break
        
        if not rate_limited:
            print(f"  ⚠️  Not rate limited after {request_count} requests")
    
    async def test_input_validation(self):
        """Test input validation and sanitization."""
        print("\n🔍 Testing Input Validation...")
        
        # Test XSS attempts
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "'><script>alert(String.fromCharCode(88,83,83))</script>",
        ]
        
        for payload in xss_payloads:
            response = await self.client.post(
                f"{self.base_url}/api/v1/auth/register",
                json={
                    "email": "test@example.com",
                    "password": "Test123!",
                    "full_name": payload
                }
            )
            
            if response.status_code >= 400:
                print(f"  ✅ XSS payload blocked: {payload[:30]}...")
            else:
                print(f"  ❌ XSS payload not blocked: {payload[:30]}...")
        
        # Test SQL injection attempts
        sql_payloads = [
            "' OR '1'='1",
            "1; DROP TABLE users--",
            "admin'--",
            "1' UNION SELECT NULL--",
        ]
        
        for payload in sql_payloads:
            response = await self.client.post(
                f"{self.base_url}/api/v1/auth/login",
                json={
                    "username": payload,
                    "password": "test"
                }
            )
            
            if response.status_code >= 400 and "injection" not in response.text.lower():
                print(f"  ✅ SQL injection payload handled safely: {payload[:30]}...")
            else:
                print(f"  ⚠️  Check SQL injection handling: {payload[:30]}...")
    
    async def test_authentication_security(self):
        """Test authentication security features."""
        print("\n🔐 Testing Authentication Security...")
        
        # Test password requirements
        weak_passwords = [
            "123456",
            "password",
            "test",
            "qwerty123",
        ]
        
        for password in weak_passwords:
            response = await self.client.post(
                f"{self.base_url}/api/v1/auth/register",
                json={
                    "email": f"test{password}@example.com",
                    "password": password,
                    "full_name": "Test User"
                }
            )
            
            if response.status_code >= 400:
                print(f"  ✅ Weak password rejected: {password}")
            else:
                print(f"  ❌ Weak password accepted: {password}")
    
    async def generate_report(self):
        """Generate security test report."""
        print("\n📊 Security Test Report")
        print("=" * 50)
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"Target: {self.base_url}")
        print("\nResults:")
        
        total_passed = sum(r["passed"] for r in self.results if "passed" in r)
        total_failed = sum(r["failed"] for r in self.results if "failed" in r)
        
        for result in self.results:
            if "passed" in result:
                print(f"\n{result['test']}:")
                print(f"  Passed: {result['passed']}/{result['total']}")
                if result["failed"] > 0:
                    print(f"  Failed: {result['failed']}/{result['total']}")
        
        print(f"\nOverall: {total_passed} passed, {total_failed} failed")
        
        # Save detailed report
        report = {
            "timestamp": datetime.now().isoformat(),
            "target": self.base_url,
            "results": self.results,
            "summary": {
                "total_passed": total_passed,
                "total_failed": total_failed
            }
        }
        
        with open("security_test_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print("\nDetailed report saved to: security_test_report.json")
    
    async def run_all_tests(self):
        """Run all security tests."""
        print("🚀 Starting Security Tests...")
        
        try:
            await self.test_security_headers()
            await self.test_csrf_protection()
            await self.test_rate_limiting()
            await self.test_input_validation()
            await self.test_authentication_security()
        finally:
            await self.client.aclose()
        
        await self.generate_report()


async def main():
    """Run security tests."""
    import sys
    
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    tester = SecurityTester(base_url)
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())