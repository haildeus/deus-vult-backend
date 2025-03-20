import logging
import sys


def setup_logging():
    """Configure root logger for the entire project"""
    logger = logging.getLogger("athena")
    logger.setLevel(logging.INFO)

    # Prevent duplicate handlers
    if logger.hasHandlers():
        logger.handlers.clear()

    # Console handler with simple format
    console_handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("%(levelname)s - %(message)s")
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    return logger


# Initialize immediately when imported
logger = setup_logging()
