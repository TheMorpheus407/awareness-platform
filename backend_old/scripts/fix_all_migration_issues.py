#!/usr/bin/env python3
"""Comprehensive script to fix all migration issues."""

import os
import sys
import subprocess
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

def run_command(cmd, description):
    """Run a command and print the result."""
    print(f"\n{'=' * 60}")
    print(f"Running: {description}")
    print(f"Command: {cmd}")
    print('=' * 60)
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.stdout:
        print("Output:")
        print(result.stdout)
    
    if result.stderr:
        print("Errors/Warnings:")
        print(result.stderr)
    
    if result.returncode != 0:
        print(f"Command failed with return code: {result.returncode}")
        return False
    
    print("✓ Success")
    return True

def main():
    """Main function to fix all migration issues."""
    print("Fixing all migration issues...")
    
    # Change to backend directory
    os.chdir(backend_dir)
    
    # Step 1: Activate virtual environment and install dependencies
    if not run_command(
        "source venv/bin/activate && pip install -r requirements.txt",
        "Installing dependencies"
    ):
        print("Failed to install dependencies. Make sure venv exists.")
        return
    
    # Step 2: Run the fix migration types script
    if run_command(
        "source venv/bin/activate && python scripts/fix_migration_types.py",
        "Fixing migration enum types"
    ):
        print("✓ Fixed migration types")
    else:
        print("⚠ Could not fix migration types, continuing anyway...")
    
    # Step 3: Run migrations with alembic
    if run_command(
        "source venv/bin/activate && alembic upgrade head",
        "Running Alembic migrations"
    ):
        print("✓ Migrations applied successfully")
    else:
        print("❌ Migration failed")
        
        # Try to check current migration status
        run_command(
            "source venv/bin/activate && alembic current",
            "Checking current migration status"
        )
        
        # Try to check migration history
        run_command(
            "source venv/bin/activate && alembic history",
            "Checking migration history"
        )
    
    # Step 4: Verify database state
    if run_command(
        "source venv/bin/activate && python scripts/check_and_fix_enums.py",
        "Verifying enum types"
    ):
        print("✓ Enum types verified")
    else:
        print("⚠ Could not verify enum types")
    
    print("\n" + "=" * 60)
    print("Migration fix process completed!")
    print("=" * 60)

if __name__ == "__main__":
    main()