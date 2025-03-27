import logging
import sys


def setup_logging(name: str = "shared-components"):
    """Configure root logger for the entire project"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Prevent duplicate handlers
    if logger.hasHandlers():
        logger.handlers.clear()

    # Console handler with simple format
    console_handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("%(levelname)s - %(message)s")
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    return logger


logger = setup_logging()
