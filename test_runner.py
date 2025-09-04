#!/usr/bin/env python3
"""
Test runner script for UniFi Release Announcer.
Provides easy commands to run all tests at once.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> bool:
    """Run a command and return True if successful."""
    print(f"Running {description}...")
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ {description} passed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(e.stdout)
        print(e.stderr)
        return False


def main() -> None:
    """Run all tests and linting."""
    project_root = Path(__file__).parent

    # Change to project directory
    import os
    os.chdir(project_root)

    success = True

    # Run pytest
    success &= run_command(["python", "-m", "pytest", "-v"], "Tests")
    
    # Run ruff linting
    success &= run_command(["python", "-m", "ruff", "check", "."], 
                          "Ruff linting")
    
    # Run mypy type checking
    success &= run_command(["python", "-m", "mypy", "."], 
                          "MyPy type checking")

    if success:
        print("\n🎉 All checks passed!")
        sys.exit(0)
    else:
        print("\n💥 Some checks failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
