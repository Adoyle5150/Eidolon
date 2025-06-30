# eidolon_logger.py

"""
Eidolon - Logging Utility

Provides centralized, color-coded, toggleable logging for consistent debugging across all modules.
"""

import logging
import os
import sys

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False

# Default log level
DEFAULT_LEVEL = logging.DEBUG

# Create logger
logger = logging.getLogger("Eidolon")
logger.setLevel(DEFAULT_LEVEL)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(DEFAULT_LEVEL)

# Formatter with optional color support
class ColorFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: Fore.BLUE,
        logging.INFO: Fore.GREEN,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.RED + Style.BRIGHT,
    }

    def format(self, record):
        msg = super().format(record)
        if COLORAMA_AVAILABLE:
            color = self.COLORS.get(record.levelno, "")
            return f"{color}{msg}{Style.RESET_ALL}"
        else:
            return msg

formatter = ColorFormatter("[%(asctime)s] [%(levelname)s] %(message)s", "%H:%M:%S")
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Optional: Enable file logging
file_logging_enabled = False

def enable_file_logging(log_file="eidolon.log"):
    global file_logging_enabled
    if not file_logging_enabled:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(DEFAULT_LEVEL)
        file_handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S"))
        logger.addHandler(file_handler)
        file_logging_enabled = True
        logger.info(f"File logging enabled: {log_file}")

# Convenience functions
def debug(msg): logger.debug(msg)
def info(msg): logger.info(msg)
def warning(msg): logger.warning(msg)
def error(msg): logger.error(msg)
def critical(msg): logger.critical(msg)
