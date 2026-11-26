import logging
import logging.config
import re
import time
from collections.abc import Callable, Coroutine
from functools import wraps
from os import getenv
from typing import Any, ParamSpec, TypeVar

LOGGER_NAME = None

MASK = "***"

# Users hand the scanner URLs and HTTP specs that carry credentials, and
# httpx errors repeat the full URL. Mask secret-looking values before any
# record reaches a handler:
#   ?api_key=...  &token=...  &client_secret=...  &password=...
#   scheme://user:pass@host/...   scheme://token@host/...
#   Authorization: Bearer/Basic/Token/ApiKey ...   x-api-key: ...
#   sk-..., sk-ant-..., hf_..., AKIA... shaped keys anywhere in the text
_SECRET_PATTERNS = (
    re.compile(
        r"([?&][^=&\s#\"'<>]*(?:key|token|secret|password)[^=&\s#\"'<>]*=)"
        r"[^&\s#\"'<>]+",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b([a-zA-Z][a-zA-Z0-9+.-]{0,15}://)[^\s/?#\"'<>,]+(?=@[^\s/?#\"'<>,@])"
    ),
    re.compile(r"(\bBearer\s+)[A-Za-z0-9._~+/=-]{8,}", re.IGNORECASE),
    re.compile(
        r"(\b(?:x-api-key|api-key|authorization)[\"']?\s*[:=]\s*[\"']?"
        r"(?!Bearer\b)(?:(?:Basic|Token|ApiKey|Api-Key)[ \t]+)?)"
        r"[^\s\"',}]{8,}",
        re.IGNORECASE,
    ),
    re.compile(r"()\b(?:sk-(?:ant-|proj-)?|hf_|AKIA)[A-Za-z0-9_-]{12,}"),
)


def redact(text: str) -> str:
    """Mask credential-looking values in ``text``."""
    for pattern in _SECRET_PATTERNS:
        text = pattern.sub(lambda m: m.group(1) + MASK, text)
    return text


class RedactSecrets(logging.Filter):
    """Rewrite each record so no secret reaches the handler."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            message = record.getMessage()
        except Exception:
            return True  # a malformed record is logging's problem, not ours
        cleaned = redact(message)
        if cleaned != message:
            record.msg, record.args = cleaned, None
        if record.exc_info and not record.exc_text:
            record.exc_text = logging.Formatter().formatException(record.exc_info)
        if record.exc_text:
            record.exc_text = redact(record.exc_text)
        if record.stack_info:
            record.stack_info = redact(record.stack_info)
        return True


LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "redact_secrets": {"()": RedactSecrets},
    },
    "formatters": {
        "rich": {"format": "%(message)s", "datefmt": "[%X]"},
    },
    "handlers": {
        "rich": {
            "class": "rich.logging.RichHandler",
            "level": "INFO",
            "formatter": "rich",
            "filters": ["redact_secrets"],
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
        "httpx": {  # Disable httpx logging
            "level": "WARNING",  # Suppress DEBUG and INFO messages from httpx
            "handlers": [],
            "propagate": False,
        },
        "httpcore": {  # Logs full request lines at DEBUG
            "level": "WARNING",
            "handlers": [],
            "propagate": False,
        },
        "uvicorn.access": {  # Disable uvicorn.access logging
            "level": "WARNING",  # Suppress DEBUG and INFO messages from uvicorn.access
            "handlers": [],
            "propagate": False,
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


# Define generic type variables for return type and parameters
R = TypeVar("R")
P = ParamSpec("P")


def time_execution_sync(
    additional_text: str = "",
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.debug(
                f"{additional_text} Execution time: {execution_time:.2f} seconds"
            )
            return result

        return wrapper

    return decorator


def time_execution_async(
    additional_text: str = "",
) -> Callable[
    [Callable[P, Coroutine[Any, Any, R]]], Callable[P, Coroutine[Any, Any, R]]
]:
    def decorator(
        func: Callable[P, Coroutine[Any, Any, R]],
    ) -> Callable[P, Coroutine[Any, Any, R]]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            start_time = time.time()
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.debug(
                f"{additional_text} Execution time: {execution_time:.2f} seconds"
            )
            return result

        return wrapper

    return decorator
