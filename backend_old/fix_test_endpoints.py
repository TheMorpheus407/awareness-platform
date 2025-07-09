#!/usr/bin/env python3
"""Fix API endpoint URLs in test files to include /v1 prefix."""

import os
import re
from pathlib import Path


def fix_endpoints_in_file(filepath):
    """Fix API endpoints in a single file."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # List of patterns to replace
    replacements = [
        # Auth endpoints
        (r'"/api/auth/login"', '"/api/v1/auth/login"'),
        (r'"/api/auth/register"', '"/api/v1/auth/register"'),
        (r'"/api/auth/refresh"', '"/api/v1/auth/refresh"'),
        (r'"/api/auth/logout"', '"/api/v1/auth/logout"'),
        (r'"/api/auth/me"', '"/api/v1/auth/me"'),
        (r'"/api/auth/change-password"', '"/api/v1/auth/change-password"'),
        
        # Email verification
        (r'"/api/auth/email/verify"', '"/api/v1/auth/email/verify"'),
        (r'"/api/auth/email/resend"', '"/api/v1/auth/email/resend"'),
        (r'"/api/auth/email/send-verification"', '"/api/v1/auth/email/send-verification"'),
        
        # Password reset
        (r'"/api/auth/password/reset-request"', '"/api/v1/auth/password/reset-request"'),
        (r'"/api/auth/password/reset"', '"/api/v1/auth/password/reset"'),
        (r'"/api/auth/password/verify-token"', '"/api/v1/auth/password/verify-token"'),
        
        # 2FA endpoints
        (r'"/api/auth/2fa/setup"', '"/api/v1/auth/2fa/setup"'),
        (r'"/api/auth/2fa/verify"', '"/api/v1/auth/2fa/verify"'),
        (r'"/api/auth/2fa/login"', '"/api/v1/auth/2fa/login"'),
        (r'"/api/auth/2fa/disable"', '"/api/v1/auth/2fa/disable"'),
        (r'"/api/auth/2fa/backup-codes"', '"/api/v1/auth/2fa/backup-codes"'),
        
        # Users endpoints
        (r'"/api/users"', '"/api/v1/users"'),
        (r'"/api/users/"', '"/api/v1/users/"'),
        (r'f"/api/users/{', 'f"/api/v1/users/{'),
        
        # Companies endpoints  
        (r'"/api/companies"', '"/api/v1/companies"'),
        (r'"/api/companies/"', '"/api/v1/companies/"'),
        (r'f"/api/companies/{', 'f"/api/v1/companies/{'),
        
        # Health endpoints (already done but just in case)
        (r'"/api/health"', '"/api/v1/health"'),
        (r'"/api/health/db"', '"/api/v1/health/db"'),
    ]
    
    # Apply replacements
    modified = False
    for pattern, replacement in replacements:
        if pattern.strip('"') in content:
            content = content.replace(pattern.strip('"'), replacement.strip('"'))
            modified = True
    
    # Write back if modified
    if modified:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Fixed endpoints in {filepath}")
        return True
    return False


def main():
    """Fix endpoints in all test files."""
    test_files = [
        "tests/api/routes/test_auth.py",
        "tests/api/routes/test_email_verification.py", 
        "tests/api/routes/test_password_reset.py",
        "tests/api/routes/test_two_factor.py",
        "tests/api/test_auth.py",
        "tests/api/test_companies.py",
        "tests/api/test_users.py",
        "tests/test_health.py",
    ]
    
    fixed_count = 0
    for filepath in test_files:
        if os.path.exists(filepath):
            if fix_endpoints_in_file(filepath):
                fixed_count += 1
    
    print(f"\nFixed {fixed_count} files")


if __name__ == "__main__":
    main()