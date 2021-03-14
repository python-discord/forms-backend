"""
Patch the uvicorn, watchgod, and global loggers.
"""
import logging
import sys
from logging import handlers
from pathlib import Path

from backend import constants

# Setup constants
LOGGING_LEVEL = logging.INFO if constants.PRODUCTION else logging.DEBUG
FORMATTER = logging.Formatter("%(asctime)s | %(name)s | %(levelname)s | %(message)s")

# Setup the project logger
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(FORMATTER)

logger = logging.getLogger("backend")
logger.setLevel(LOGGING_LEVEL)
logger.addHandler(handler)

# Format uvicorn logging
try:
    logging.getLogger("uvicorn").handlers[0].setFormatter(FORMATTER)
except KeyError:
    logger.warning("Could not patch uvicorn logger, continuing.")

# Add file handlers for local development
if constants.LOG_FILES:
    # Setup uvicorn handler
    uvicorn_log = Path("logs", ".uvicorn.log")
    uvicorn_log.parent.mkdir(exist_ok=True)
    # Store two copies of 100KB Files
    uvicorn_handler = handlers.RotatingFileHandler(uvicorn_log, maxBytes=100000, backupCount=1)
    uvicorn_handler.setFormatter(FORMATTER)

    # Setup app handler
    backend_log = Path("logs", ".backend.log")
    file_handler = logging.FileHandler(backend_log)
    file_handler.setFormatter(FORMATTER)

    # Add all handlers
    logging.getLogger("uvicorn").addHandler(uvicorn_handler)
    logger.addHandler(file_handler)
