#!/usr/bin/env python
"""
Test runner script for StockWise Django application.
This script provides easy ways to run different types of tests.
"""
import os
import sys
import subprocess
import argparse

def run_basic_tests():
    """Run basic functionality tests."""
    print("Running basic functionality tests...")
    result = subprocess.run([
        sys.executable, '-m', 'pytest', 
        'tests/test_basic.py', 
        '-v', 
        '--tb=short'
    ])
    return result.returncode

def run_model_tests():
    """Run model tests."""
    print("Running model tests...")
    result = subprocess.run([
        sys.executable, '-m', 'pytest', 
        'tests/test_models.py', 
        '-v', 
        '--tb=short'
    ])
    return result.returncode

def run_all_tests():
    """Run all tests with coverage."""
    print("Running all tests with coverage...")
    result = subprocess.run([
        sys.executable, '-m', 'pytest', 
        'tests/', 
        '-v', 
        '--tb=short',
        '--cov=core',
        '--cov-report=html',
        '--cov-report=term-missing'
    ])
    return result.returncode

def run_fast_tests():
    """Run only fast tests (skip slow ones)."""
    print("Running fast tests only...")
    result = subprocess.run([
        sys.executable, '-m', 'pytest', 
        'tests/', 
        '-v', 
        '--tb=short',
        '-m', 'not slow'
    ])
    return result.returncode

def run_specific_test(test_path):
    """Run a specific test file or test method."""
    print(f"Running specific test: {test_path}")
    result = subprocess.run([
        sys.executable, '-m', 'pytest', 
        test_path, 
        '-v', 
        '--tb=short'
    ])
    return result.returncode

def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(description='Run StockWise tests')
    parser.add_argument(
        '--type', 
        choices=['basic', 'models', 'all', 'fast', 'specific'],
        default='basic',
        help='Type of tests to run'
    )
    parser.add_argument(
        '--test', 
        help='Specific test file or method to run (used with --type specific)'
    )
    
    args = parser.parse_args()
    
    # Set Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stockwise_py.settings')
    
    if args.type == 'basic':
        return run_basic_tests()
    elif args.type == 'models':
        return run_model_tests()
    elif args.type == 'all':
        return run_all_tests()
    elif args.type == 'fast':
        return run_fast_tests()
    elif args.type == 'specific':
        if not args.test:
            print("Error: --test argument required when using --type specific")
            return 1
        return run_specific_test(args.test)
    else:
        print(f"Unknown test type: {args.type}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
