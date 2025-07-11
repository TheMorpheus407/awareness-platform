#!/usr/bin/env python3
"""
Comprehensive test runner for the Awareness Platform backend.
Provides various test execution modes and reporting options.
"""

import sys
import subprocess
import argparse
from pathlib import Path

def run_command(cmd, check=True):
    """Run a command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    
    if check and result.returncode != 0:
        sys.exit(result.returncode)
    
    return result

def main():
    parser = argparse.ArgumentParser(description="Run backend tests with various options")
    parser.add_argument("--unit", action="store_true", help="Run only unit tests")
    parser.add_argument("--integration", action="store_true", help="Run only integration tests")
    parser.add_argument("--critical", action="store_true", help="Run only critical tests")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--html", action="store_true", help="Generate HTML coverage report")
    parser.add_argument("--security", action="store_true", help="Run security tests")
    parser.add_argument("--performance", action="store_true", help="Run performance tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--quick", action="store_true", help="Quick test run (skip slow tests)")
    parser.add_argument("--fail-fast", "-x", action="store_true", help="Stop on first failure")
    parser.add_argument("--parallel", "-n", type=int, help="Run tests in parallel with N workers")
    parser.add_argument("tests", nargs="*", help="Specific test files or directories to run")
    
    args = parser.parse_args()
    
    # Base pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Add test selection
    if args.unit:
        cmd.extend(["-m", "unit"])
    elif args.integration:
        cmd.extend(["-m", "integration"])
    elif args.critical:
        cmd.extend(["-m", "critical"])
    elif args.security:
        cmd.extend(["-m", "security"])
    elif args.quick:
        cmd.extend(["-m", "not slow"])
    
    # Add coverage options
    if args.coverage:
        cmd.extend(["--cov=app", "--cov-report=term-missing"])
        if args.html:
            cmd.append("--cov-report=html")
    
    # Add other options
    if args.verbose:
        cmd.append("-vv")
    
    if args.fail_fast:
        cmd.append("-x")
    
    if args.parallel:
        cmd.extend(["-n", str(args.parallel)])
    
    # Add specific test paths
    if args.tests:
        cmd.extend(args.tests)
    else:
        cmd.append("tests/")
    
    # Run linting first if not running specific tests
    if not args.tests:
        print("\n=== Running Code Quality Checks ===")
        lint_cmd = ["python", "-m", "flake8", "app", "tests", "--max-line-length=100", "--ignore=E203,W503"]
        lint_result = run_command(lint_cmd, check=False)
        
        if lint_result.returncode != 0:
            print("\nWarning: Linting issues found. Please fix them.")
    
    # Run type checking
    if not args.tests and not args.quick:
        print("\n=== Running Type Checks ===")
        mypy_cmd = ["python", "-m", "mypy", "app", "--ignore-missing-imports"]
        run_command(mypy_cmd, check=False)
    
    # Run the tests
    print("\n=== Running Tests ===")
    test_result = run_command(cmd, check=False)
    
    # Generate test report
    if args.coverage and test_result.returncode == 0:
        print("\n=== Coverage Summary ===")
        cov_cmd = ["python", "-m", "coverage", "report", "--skip-covered", "--show-missing"]
        run_command(cov_cmd, check=False)
        
        if args.html:
            print("\nHTML coverage report generated in htmlcov/index.html")
    
    # Run security scan if requested
    if args.security and test_result.returncode == 0:
        print("\n=== Running Security Scan ===")
        bandit_cmd = ["python", "-m", "bandit", "-r", "app", "-ll"]
        run_command(bandit_cmd, check=False)
    
    # Performance analysis if requested
    if args.performance and test_result.returncode == 0:
        print("\n=== Running Performance Analysis ===")
        perf_cmd = ["python", "-m", "pytest", "--durations=10", "tests/"]
        run_command(perf_cmd, check=False)
    
    sys.exit(test_result.returncode)

if __name__ == "__main__":
    main()