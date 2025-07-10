"""
Basic setup tests for HL7 OpenSoup.

These tests verify that the basic application setup and imports work correctly.
"""

import sys
import pytest
from pathlib import Path

# Add src to path for testing
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))


def test_package_imports():
    """Test that all main packages can be imported."""
    import hl7opensoup
    import hl7opensoup.config
    import hl7opensoup.utils
    import hl7opensoup.ui
    import hl7opensoup.core
    import hl7opensoup.models
    
    assert hl7opensoup.__version__ == "1.0.0"


def test_config_creation():
    """Test that AppConfig can be created."""
    from hl7opensoup.config.app_config import AppConfig
    
    config = AppConfig()
    assert config is not None
    assert config.get('application.theme') == 'default'
    assert config.get('hl7.default_version') == '2.5'


def test_logging_setup():
    """Test that logging can be set up."""
    from hl7opensoup.utils.logging_config import setup_logging, get_logger
    
    setup_logging(log_level="DEBUG", console_output=False)
    logger = get_logger(__name__)
    assert logger is not None
    
    # Test logging
    logger.info("Test log message")


@pytest.mark.skip(reason="Requires PyQt6 and display")
def test_main_window_creation():
    """Test that MainWindow can be created (requires PyQt6)."""
    from PyQt6.QtWidgets import QApplication
    from hl7opensoup.config.app_config import AppConfig
    from hl7opensoup.ui.main_window import MainWindow
    
    app = QApplication([])
    config = AppConfig()
    window = MainWindow(config)
    
    assert window is not None
    assert window.windowTitle() == "HL7 OpenSoup - Advanced HL7 Viewer and Editor"
    
    app.quit()


if __name__ == "__main__":
    pytest.main([__file__])
