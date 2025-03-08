# import sys

# from loguru import logger

# # Define custom colors
# BLUE = "#89CFF0"
# BROWN = "#8B4513"  # Brown for DEBUG

# # Define custom log level colors
# logger.level("DEBUG", color=f"<fg {BROWN}>")
# logger.level("INFO", color=f"<fg {BLUE}>")

# # Define custom log format with aligned messages and colored levels
# LOG_FORMAT = (
#     "<level>{level:<8}</level> "  # Properly formatted and colored log level
#     "<level>{message:<100}</level> "  # Left-aligned message for readability
#     "<cyan>{file.name}</cyan>:<cyan>{line}</cyan>"  # File name and line number in cyan
# )

# # Remove default handlers and add a new one with custom formatting
# logger.remove()
# logger.add(sys.stdout, format=LOG_FORMAT, level="DEBUG", colorize=True)
import logging
import logging.config
from os import getenv


LOGGER_NAME = None

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "rich": {"format": "%(message)s", "datefmt": "[%X]"},
    },
    "handlers": {
        "rich": {
            "class": "rich.logging.RichHandler",
            "level": "INFO",
            "formatter": "rich",
            "show_time": False,
            "rich_tracebacks": False,
            "show_path": lambda: True if getenv("API_RUNTIME") == "dev" else False,
            "tracebacks_show_locals": False,
        },
    },
    "loggers": {
        "": {  # Root logger configuration
            "level": "INFO",
            "handlers": ["rich"],
            "propagate": True,
        },
    },
}


def configure_logging():
    # Apply the dictionary configuration
    logging.config.dictConfig(LOGGING_CONFIG)

    # Get and return the logger
    logger = logging.getLogger(LOGGER_NAME)
    return logger


logger: logging.Logger = configure_logging()


def set_log_level_to_debug():
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.DEBUG)
    # Update handler level as well
    for handler in logger.handlers:
        handler.setLevel(logging.DEBUG)


def set_log_level_to_info():
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)
    # Update handler level as well
    for handler in logger.handlers:
        handler.setLevel(logging.INFO)


# Set initial log level
set_log_level_to_info()
