"""Security utilities and validation for agentic_security."""

from functools import wraps
from collections.abc import Callable
from urllib.parse import urlparse
import hashlib
import hmac
import os
import re


class SecurityValidator:
    """Input validation and sanitization."""

    ALLOWED_URL_SCHEMES = {"http", "https"}
    MAX_URL_LENGTH = 2048
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

    @staticmethod
    def validate_url(url: str, allowed_hosts: list[str] | None = None) -> bool:
        """Validate URL for SSRF prevention."""
        if len(url) > SecurityValidator.MAX_URL_LENGTH:
            return False

        try:
            parsed = urlparse(url)

            if parsed.scheme not in SecurityValidator.ALLOWED_URL_SCHEMES:
                return False

            if not parsed.netloc:
                return False

            if parsed.netloc in ["localhost", "127.0.0.1", "0.0.0.0"]:
                return False

            if parsed.netloc.startswith("169.254."):
                return False

            if parsed.netloc.startswith("10.") or parsed.netloc.startswith("192.168."):
                return False

            if allowed_hosts and parsed.netloc not in allowed_hosts:
                return False

            return True
        except Exception:
            return False

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename to prevent path traversal."""
        filename = os.path.basename(filename)
        filename = re.sub(r"[^\w\s.-]", "", filename)
        filename = filename.strip()

        if not filename or filename in [".", ".."]:
            raise ValueError("Invalid filename")

        return filename

    @staticmethod
    def validate_file_size(size: int) -> bool:
        """Validate file size."""
        return 0 < size <= SecurityValidator.MAX_FILE_SIZE

    @staticmethod
    def validate_csv_content(content: str) -> bool:
        """Basic CSV validation."""
        if not content or len(content) > SecurityValidator.MAX_FILE_SIZE:
            return False

        lines = content.split("\n", 2)
        if not lines:
            return False

        return True


class SecretManager:
    """Secure secret handling."""

    @staticmethod
    def get_secret(key: str, default: str | None = None) -> str | None:
        """Get secret from environment."""
        value = os.getenv(key, default)
        if value and value.startswith("$"):
            env_key = value[1:]
            value = os.getenv(env_key, default)
        return value

    @staticmethod
    def hash_secret(secret: str, salt: str | None = None) -> str:
        """Hash a secret value."""
        if salt is None:
            salt = os.urandom(32).hex()

        hashed = hashlib.pbkdf2_hmac("sha256", secret.encode(), salt.encode(), 100000)
        return f"{salt}${hashed.hex()}"

    @staticmethod
    def verify_secret(secret: str, hashed: str) -> bool:
        """Verify a secret against its hash."""
        try:
            salt, expected = hashed.split("$", 1)
            actual = hashlib.pbkdf2_hmac(
                "sha256", secret.encode(), salt.encode(), 100000
            )
            return hmac.compare_digest(actual.hex(), expected)
        except Exception:
            return False


class RateLimiter:
    """Simple in-memory rate limiter."""

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = {}

    def is_allowed(self, key: str) -> bool:
        """Check if request is allowed."""
        import time

        now = time.time()

        if key not in self._requests:
            self._requests[key] = []

        self._requests[key] = [
            ts for ts in self._requests[key] if now - ts < self.window_seconds
        ]

        if len(self._requests[key]) >= self.max_requests:
            return False

        self._requests[key].append(now)
        return True

    def reset(self, key: str):
        """Reset rate limit for key."""
        self._requests.pop(key, None)


def require_auth(func: Callable) -> Callable:
    """Decorator to require authentication."""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        # TODO: Implement actual auth check
        # For now, check if API key is present
        api_key = kwargs.get("api_key") or os.getenv("API_KEY")
        if not api_key:
            from fastapi import HTTPException

            raise HTTPException(status_code=401, detail="Authentication required")
        return await func(*args, **kwargs)

    return wrapper


def sanitize_log_output(data: str | dict) -> str:
    """Remove sensitive data from logs."""
    if isinstance(data, dict):
        data = str(data)

    patterns = [
        (r'(api[_-]?key["\s:=]+)["\']?[\w-]+', r"\1***"),
        (r'(token["\s:=]+)["\']?[\w-]+', r"\1***"),
        (r'(password["\'\s:=]+)["\']?[\w-]+', r"\1***"),
        (r'(secret["\s:=]+)["\']?[\w-]+', r"\1***"),
        (r"Bearer\s+[\w-]+", "Bearer ***"),
    ]

    for pattern, replacement in patterns:
        data = re.sub(pattern, replacement, data, flags=re.IGNORECASE)

    return data
