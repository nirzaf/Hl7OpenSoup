#!/usr/bin/env python3
"""
Main entry point for HL7 OpenSoup application.

This module initializes and starts the PyQt6 application with the main window.
"""

import sys
import os
import logging
from pathlib import Path

# Add the src directory to the Python path
src_dir = Path(__file__).parent.parent
sys.path.insert(0, str(src_dir))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QDir
from PyQt6.QtGui import QIcon

from hl7opensoup.ui.main_window import MainWindow
from hl7opensoup.ui.hl7_soup_style import apply_hl7_soup_style
from hl7opensoup.utils.logging_config import setup_logging
from hl7opensoup.config.app_config import AppConfig


def setup_application():
    """Set up the QApplication with proper configuration."""
    # Enable high DPI scaling (for PyQt6, this is automatic)
    # Only set these if they exist (for compatibility)
    try:
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    except AttributeError:
        pass  # Not available in this PyQt6 version

    app = QApplication(sys.argv)
    app.setApplicationName("HL7 OpenSoup")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("HL7 OpenSoup")
    app.setOrganizationDomain("hl7opensoup.com")

    # Apply HL7 Soup styling
    apply_hl7_soup_style(app)

    # Set application icon
    icon_path = Path(__file__).parent / "resources" / "app_icon.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    return app


def main():
    """Main entry point for the application."""
    try:
        # Set up logging
        setup_logging()
        logger = logging.getLogger(__name__)
        logger.info("Starting HL7 OpenSoup application...")
        
        # Load application configuration
        config = AppConfig()
        
        # Create and configure the application
        app = setup_application()
        
        # Create and show the main window
        main_window = MainWindow(config)
        main_window.show()
        
        logger.info("Application started successfully")
        
        # Start the event loop
        sys.exit(app.exec())
        
    except Exception as e:
        logging.error(f"Failed to start application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
