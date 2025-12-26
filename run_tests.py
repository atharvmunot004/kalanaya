#!/usr/bin/env python
"""Test runner script for Kalanaya project."""

import sys
import subprocess
from pathlib import Path

def run_tests(test_type="all", verbose=True):
    """
    Run tests using pytest.
    
    Args:
        test_type: Type of tests to run ("unit", "e2e", "all")
        verbose: Whether to run in verbose mode
    """
    project_root = Path(__file__).parent
    
    # Build pytest command
    cmd = [sys.executable, "-m", "pytest"]
    
    if verbose:
        cmd.append("-v")
    
    # Add coverage if available
    try:
        import pytest_cov
        cmd.extend(["--cov=src", "--cov-report=term-missing", "--cov-report=html"])
    except ImportError:
        print("Warning: pytest-cov not installed, skipping coverage report")
    
    # Select test files based on type
    if test_type == "unit":
        cmd.extend([
            "tests/pipeline/",
            "tests/actions/",
            "tests/router/",
            "tests/utils/"
        ])
    elif test_type == "e2e":
        cmd.append("tests/test_e2e.py")
    elif test_type == "all":
        cmd.append("tests/")
    else:
        print(f"Unknown test type: {test_type}")
        print("Available types: unit, e2e, all")
        return 1
    
    print(f"Running {test_type} tests...")
    print(f"Command: {' '.join(cmd)}")
    print("=" * 80)
    
    # Run tests
    result = subprocess.run(cmd, cwd=project_root)
    
    return result.returncode


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run tests for Kalanaya")
    parser.add_argument(
        "--type",
        choices=["unit", "e2e", "all"],
        default="all",
        help="Type of tests to run"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Run in quiet mode"
    )
    
    args = parser.parse_args()
    
    exit_code = run_tests(test_type=args.type, verbose=not args.quiet)
    sys.exit(exit_code)

