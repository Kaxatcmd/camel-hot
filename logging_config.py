"""
Logging configuration for DJ Harmonic Analyzer.

Sets up structured logging across the application.
Usage:
    from logging_config import setup_logging, get_logger
    
    setup_logging()  # Call once on app startup
    logger = get_logger(__name__)
    logger.info("Application started")
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from config import LOG_LEVEL, LOG_FORMAT, LOG_FILE, LOG_MAX_BYTES, LOG_BACKUP_COUNT, get_logs_dir


def setup_logging(level: str = None) -> None:
    """
    Configure logging for the entire application.
    
    Creates both console and file handlers with appropriate formatting.
    Ensures all loggers in the application use consistent configuration.
    
    Args:
        level: Logging level as string (DEBUG, INFO, WARNING, ERROR, CRITICAL).
               If None, uses config.LOG_LEVEL.
    
    Example:
        setup_logging("DEBUG")  # Enable debug logging
        logger = get_logger(__name__)
        logger.debug("Debug message")
    """
    if level is None:
        level = LOG_LEVEL
    
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create logs directory
    logs_dir = get_logs_dir()
    log_file = logs_dir / LOG_FILE
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove any existing handlers to prevent duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT)
    
    # Console handler (always INFO or above, even in debug mode)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Reduce noise from external libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("matplotlib").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the given module name.
    
    Args:
        name: Module name, typically __name__
        
    Returns:
        logging.Logger configured for the application
        
    Example:
        logger = get_logger(__name__)
        logger.info("Processing track")
    """
    return logging.getLogger(name)


# Module-level logger for this config module itself
logger = get_logger(__name__)
