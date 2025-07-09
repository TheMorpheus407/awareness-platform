#!/usr/bin/env python3
"""Fix is_verified to email_verified in test files."""

import os


def fix_verified_field_in_file(filepath):
    """Fix is_verified field references in a single file."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Replace is_verified with email_verified
    modified = content.replace('is_verified=', 'email_verified=')
    modified = modified.replace('user.is_verified', 'user.email_verified')
    modified = modified.replace('"is_verified"', '"email_verified"')
    modified = modified.replace("'is_verified'", "'email_verified'")
    
    # Write back if modified
    if modified != content:
        with open(filepath, 'w') as f:
            f.write(modified)
        print(f"Fixed verified field in {filepath}")
        return True
    return False


def main():
    """Fix verified field in all test files."""
    test_files = [
        "tests/api/routes/test_auth.py",
        "tests/api/test_users.py",
        "tests/models/test_user.py"
    ]
    
    fixed_count = 0
    for filepath in test_files:
        if os.path.exists(filepath):
            if fix_verified_field_in_file(filepath):
                fixed_count += 1
    
    print(f"\nFixed {fixed_count} files")


if __name__ == "__main__":
    main()