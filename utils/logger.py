"""
Logging configuration for BindClicker.

Creates a rotating file logger + console handler.
Each module should use:
    from utils.logger import get_logger
    logger = get_logger(__name__)
"""

import logging
import os
from logging.handlers import RotatingFileHandler

from utils.constants import (
    LOG_BACKUP_COUNT,
    LOG_DATE_FORMAT,
    LOG_FILE,
    LOG_FORMAT,
    LOG_MAX_BYTES,
    LOGS_DIR,
)

_ROOT_LOGGER_NAME = "bindclicker"
_configured = False


def setup_logging() -> None:
    """Initialise the root application logger (call once at startup)."""
    global _configured
    if _configured:
        return

    os.makedirs(LOGS_DIR, exist_ok=True)

    root = logging.getLogger(_ROOT_LOGGER_NAME)
    root.setLevel(logging.DEBUG)

    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

    # --- File handler (rotating) ---
    fh = RotatingFileHandler(
        LOG_FILE,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    root.addHandler(fh)

    # --- Console handler ---
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    root.addHandler(ch)

    _configured = True
    root.info("Logging initialised – file: %s", LOG_FILE)


def get_logger(name: str) -> logging.Logger:
    """Return a child logger under the application root.

    Usage:
        logger = get_logger(__name__)   # e.g. "bindclicker.core.recorder"
    """
    if not _configured:
        setup_logging()

    # Strip the project package prefix so the hierarchy stays clean
    if name.startswith("bindClicker."):
        name = name[len("bindClicker."):]

    return logging.getLogger(f"{_ROOT_LOGGER_NAME}.{name}")
