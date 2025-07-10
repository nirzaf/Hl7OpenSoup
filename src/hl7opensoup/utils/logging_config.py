"""
Logging configuration for HL7 OpenSoup.

This module sets up logging for the application with appropriate formatters,
handlers, and log levels.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    console_output: bool = True,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> None:
    """Set up logging configuration for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file. If None, uses default location.
        console_output: Whether to output logs to console
        max_file_size: Maximum size of log file before rotation
        backup_count: Number of backup log files to keep
    """
    # Create logs directory
    log_dir = Path.home() / ".hl7opensoup" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Default log file path
    if log_file is None:
        log_file = log_dir / "hl7opensoup.log"
    else:
        log_file = Path(log_file)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # File handler with rotation
    try:
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    except Exception as e:
        print(f"Warning: Could not set up file logging: {e}")
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info("Logging system initialized")
    logger.debug(f"Log level: {log_level}")
    logger.debug(f"Log file: {log_file}")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for the given name.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
