#!/usr/bin/env python3
"""
Test runner for the skills repository

This script discovers and runs all unit tests in the repository.
It provides a summary of test results and identifies any failures.

Usage:
    python run_tests.py                    # Run all tests
    python run_tests.py --verbose          # Run with verbose output
    python run_tests.py --pattern "test_*" # Run tests matching pattern
"""

import sys
import unittest
import argparse
from pathlib import Path


def find_test_modules(root_dir, pattern="test_*.py"):
    """
    Find all test modules in the repository.

    Args:
        root_dir: Root directory to search
        pattern: Glob pattern for test files

    Returns:
        List of test file paths
    """
    root = Path(root_dir)
    test_files = []

    # Search for test files in common locations
    search_patterns = [
        f"skills/*/scripts/{pattern}",
        f"skills/*/core/{pattern}",
        f"skills/*/*/{pattern}",
    ]

    for search_pattern in search_patterns:
        test_files.extend(root.glob(search_pattern))

    return sorted(set(test_files))


def run_tests(test_files, verbosity=1):
    """
    Run the discovered test files.

    Args:
        test_files: List of test file paths
        verbosity: Verbosity level (0=quiet, 1=normal, 2=verbose)

    Returns:
        TestResult object
    """
    # Create test loader
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add tests from each file
    for test_file in test_files:
        # Add parent directory to path so imports work
        parent_dir = str(test_file.parent)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)

        # Load tests from the module
        try:
            module_name = test_file.stem
            spec = __import__(module_name)
            tests = loader.loadTestsFromModule(spec)
            suite.addTests(tests)
        except Exception as e:
            print(f"Warning: Could not load tests from {test_file}: {e}")

    # Run tests
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Run all unit tests in the skills repository"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Run tests with verbose output"
    )
    parser.add_argument(
        "--pattern", "-p",
        default="test_*.py",
        help="Pattern for test file names (default: test_*.py)"
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Root directory to search for tests (default: current directory)"
    )

    args = parser.parse_args()

    # Set verbosity level
    verbosity = 2 if args.verbose else 1

    # Find test files
    print(f"Searching for tests matching '{args.pattern}'...")
    test_files = find_test_modules(args.root, args.pattern)

    if not test_files:
        print("No test files found!")
        return 1

    print(f"Found {len(test_files)} test file(s):\n")
    for test_file in test_files:
        print(f"  - {test_file.relative_to(args.root)}")
    print()

    # Run tests
    result = run_tests(test_files, verbosity)

    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print()

    # Return appropriate exit code
    if result.wasSuccessful():
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
