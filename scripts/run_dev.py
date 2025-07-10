#!/usr/bin/env python3
"""
Development runner script for HL7 OpenSoup.

This script sets up the development environment and runs the application
with appropriate debugging and development settings.
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
project_root = Path(__file__).parent.parent
src_dir = project_root / "src"
sys.path.insert(0, str(src_dir))

def main():
    """Run the application in development mode."""
    try:
        # Set development environment variables
        os.environ["HL7_OPENSOUP_DEV"] = "1"
        os.environ["HL7_OPENSOUP_LOG_LEVEL"] = "DEBUG"
        
        # Import and run the main application
        from hl7opensoup.main import main as app_main
        
        print("Starting HL7 OpenSoup in development mode...")
        print(f"Project root: {project_root}")
        print(f"Source directory: {src_dir}")
        
        app_main()
        
    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure all dependencies are installed:")
        print("pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
