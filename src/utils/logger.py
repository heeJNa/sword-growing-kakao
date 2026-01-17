"""Logging utility for the macro application"""
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# Log directory
LOG_DIR = Path.home() / ".sword-macro" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Current log file
_current_log_file: Optional[Path] = None


def get_log_file() -> Path:
    """Get current log file path"""
    global _current_log_file
    if _current_log_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        _current_log_file = LOG_DIR / f"macro_{timestamp}.log"
    return _current_log_file


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with file and console handlers.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Only configure if not already configured
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        # Prevent propagation to parent loggers (avoid duplicate logs)
        logger.propagate = False

        # File handler - DEBUG level (모든 로그)
        log_file = get_log_file()
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

        # Console handler - INFO level (중요 로그만)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            "%(levelname)s: %(message)s"
        )
        console_handler.setFormatter(console_format)
        logger.addHandler(console_handler)

    return logger


def log_to_file(message: str, level: str = "INFO") -> None:
    """
    Quick utility to log a message directly.

    Args:
        message: Log message
        level: Log level (DEBUG, INFO, WARNING, ERROR)
    """
    logger = get_logger("quick")
    log_func = getattr(logger, level.lower(), logger.info)
    log_func(message)
