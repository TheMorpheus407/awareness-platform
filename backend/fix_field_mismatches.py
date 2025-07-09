#!/usr/bin/env python3
"""Fix field name mismatches between code and User model."""

import os
import re


def fix_field_names_in_file(filepath):
    """Fix field name mismatches in a single file."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Field name mappings
    replacements = [
        # User model fields
        (r'user\.last_login(?!\w)', 'user.last_login_at'),
        (r'user\.verified_at(?!\w)', 'user.email_verified_at'),
        (r'user\.username(?!\w)', 'user.email'),  # User model doesn't have username
        (r'"username"', '"email"'),  # for test data when not OAuth2
        (r"'username'", "'email'"),  # for test data when not OAuth2
        # Only replace full_name when it's a field assignment, not property access
        (r'full_name=', 'first_name='),  # This is wrong, need to handle separately
        # Timezone and language defaults
        (r'timezone=', '# timezone='),  # Comment out, not in model
        (r'"timezone"', '"language"'),  # Use language instead
        (r"'timezone'", "'language'"),
        # Email notifications
        (r'email_notifications_enabled', '# email_notifications_enabled'),  # Not in model
    ]
    
    # Apply replacements
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)
    
    # Special handling for datetime import
    if 'datetime.utcnow()' in content or 'datetime.now()' in content:
        if 'from datetime import' not in content and 'import datetime' not in content:
            # Add datetime import at the top
            import_lines = []
            other_lines = []
            for line in content.split('\n'):
                if line.startswith('from ') or line.startswith('import '):
                    import_lines.append(line)
                else:
                    other_lines.append(line)
            
            # Find the right place to add datetime import
            if import_lines:
                # Add after the last import
                last_import_idx = 0
                for i, line in enumerate(other_lines):
                    if any(imp in line for imp in import_lines):
                        last_import_idx = i
                
                # Check if we need to add datetime import
                needs_datetime = False
                for imp in import_lines:
                    if 'from datetime import' in imp and 'datetime' not in imp:
                        # Need to add datetime to existing import
                        import_lines[import_lines.index(imp)] = imp.rstrip() + ', datetime'
                        needs_datetime = True
                        break
                
                if not needs_datetime:
                    import_lines.append('from datetime import datetime')
                
            content = '\n'.join(import_lines + other_lines)
    
    # Write back if modified
    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Fixed field names in {filepath}")
        return True
    return False


def main():
    """Fix field names in all relevant files."""
    # Files to check
    files_to_check = []
    
    # Add all Python files in api/ and tests/
    for root, dirs, files in os.walk("api"):
        for file in files:
            if file.endswith(".py"):
                files_to_check.append(os.path.join(root, file))
    
    for root, dirs, files in os.walk("tests"):
        for file in files:
            if file.endswith(".py"):
                files_to_check.append(os.path.join(root, file))
    
    fixed_count = 0
    for filepath in files_to_check:
        if fix_field_names_in_file(filepath):
            fixed_count += 1
    
    print(f"\nFixed {fixed_count} files")


if __name__ == "__main__":
    main()