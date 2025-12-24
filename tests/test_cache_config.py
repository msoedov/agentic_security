import os
from pathlib import Path

from agentic_security.cache_config import ensure_cache_dir


def test_ensure_cache_dir_creates_dir_and_sets_env(tmp_path, monkeypatch):
    monkeypatch.delenv("DISK_CACHE_DIR", raising=False)
    target_dir = tmp_path / "cache_to_disk"

    resolved = ensure_cache_dir(target_dir)

    assert resolved == target_dir
    assert resolved.is_dir()
    assert Path(os.environ["DISK_CACHE_DIR"]) == resolved


def test_ensure_cache_dir_respects_existing_env(tmp_path, monkeypatch):
    env_dir = tmp_path / "preconfigured"
    monkeypatch.setenv("DISK_CACHE_DIR", str(env_dir))

    resolved = ensure_cache_dir()

    assert resolved == env_dir
    assert resolved.exists()
