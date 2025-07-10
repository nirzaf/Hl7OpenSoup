#!/usr/bin/env python3
"""
Dependency installation script for HL7 OpenSoup.

This script installs all required dependencies for the application.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors."""
    print(f"\n{description}...")
    try:
        # Use list format for subprocess to handle spaces in paths properly
        if isinstance(command, str):
            # For Windows, use shell=True with proper quoting
            if os.name == 'nt':
                result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            else:
                result = subprocess.run(command.split(), check=True, capture_output=True, text=True)
        else:
            result = subprocess.run(command, check=True, capture_output=True, text=True)

        print(f"✓ {description} completed successfully")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed")
        print(f"Error: {e}")
        if e.stdout:
            print(f"stdout: {e.stdout}")
        if e.stderr:
            print(f"stderr: {e.stderr}")
        return False


def main():
    """Install dependencies."""
    project_root = Path(__file__).parent.parent
    requirements_file = project_root / "requirements.txt"
    
    print("HL7 OpenSoup - Dependency Installation")
    print("=" * 40)
    print(f"Project root: {project_root}")
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    
    # Check if requirements.txt exists
    if not requirements_file.exists():
        print(f"✗ Requirements file not found: {requirements_file}")
        sys.exit(1)
    
    # Upgrade pip first
    pip_upgrade_cmd = [sys.executable, "-m", "pip", "install", "--upgrade", "pip"]
    if not run_command(pip_upgrade_cmd, "Upgrading pip"):
        print("Warning: Failed to upgrade pip, continuing anyway...")

    # Install requirements
    install_cmd = [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)]
    if not run_command(install_cmd, "Installing requirements"):
        print("✗ Failed to install requirements")
        sys.exit(1)

    # Install package in development mode
    dev_install_cmd = [sys.executable, "-m", "pip", "install", "-e", "."]
    if not run_command(dev_install_cmd, "Installing package in development mode"):
        print("Warning: Failed to install package in development mode")
    
    print("\n" + "=" * 40)
    print("✓ Installation completed successfully!")
    print("\nYou can now run the application with:")
    print("  python scripts/run_dev.py")
    print("\nOr run tests with:")
    print("  python -m pytest tests/")


if __name__ == "__main__":
    main()
