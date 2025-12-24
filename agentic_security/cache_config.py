"""Utilities to keep cache-to-disk storage in a writable, predictable location."""

from __future__ import annotations

import os
from pathlib import Path


def ensure_cache_dir(base_dir: Path | None = None) -> Path:
    """Ensure ``DISK_CACHE_DIR`` points to a writable directory and create it if needed."""
    env_var = "DISK_CACHE_DIR"
    configured_path = os.environ.get(env_var) or os.environ.get(
        "AGENTIC_SECURITY_CACHE_DIR"
    )
    cache_dir = Path(
        configured_path or base_dir or Path.cwd() / ".cache" / "agentic_security"
    ).expanduser()
    cache_dir.mkdir(parents=True, exist_ok=True)
    os.environ[env_var] = str(cache_dir)
    return cache_dir


__all__ = ["ensure_cache_dir"]
