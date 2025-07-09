#!/usr/bin/env python3
"""Fix two_factor_* field names to totp_* in test files."""

import os


def fix_2fa_fields_in_file(filepath):
    """Fix 2FA field references in a single file."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Replace two_factor_* with totp_*
    replacements = [
        ('two_factor_secret', 'totp_secret'),
        ('two_factor_enabled', 'totp_enabled'),
        ('two_fa_secret', 'totp_secret'),
        ('two_fa_enabled', 'totp_enabled'),
    ]
    
    modified = content
    for old, new in replacements:
        modified = modified.replace(old, new)
    
    # Write back if modified
    if modified != content:
        with open(filepath, 'w') as f:
            f.write(modified)
        print(f"Fixed 2FA fields in {filepath}")
        return True
    return False


def main():
    """Fix 2FA fields in all test files."""
    # Find all test files
    test_files = []
    for root, dirs, files in os.walk("tests"):
        for file in files:
            if file.endswith(".py"):
                test_files.append(os.path.join(root, file))
    
    fixed_count = 0
    for filepath in test_files:
        if fix_2fa_fields_in_file(filepath):
            fixed_count += 1
    
    print(f"\nFixed {fixed_count} files")


if __name__ == "__main__":
    main()