import sys

from loguru import logger

# Define custom colors
BLUE = "#89CFF0"
BROWN = "#8B4513"  # Brown for DEBUG

# Define custom log level colors
logger.level("DEBUG", color=f"<fg {BROWN}>")
logger.level("INFO", color=f"<fg {BLUE}>")

# Define custom log format with aligned messages and colored levels
LOG_FORMAT = (
    "<level>{level:<8}</level> "  # Properly formatted and colored log level
    "<level>{message:<100}</level> "  # Left-aligned message for readability
    "<cyan>{file.name}</cyan>:<cyan>{line}</cyan>"  # File name and line number in cyan
)

# Remove default handlers and add a new one with custom formatting
logger.remove()
logger.add(sys.stdout, format=LOG_FORMAT, level="DEBUG", colorize=True)
