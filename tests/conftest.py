import os
import warnings
from pathlib import Path

import pytest
from sklearn.exceptions import InconsistentVersionWarning

from agentic_security.cache_config import ensure_cache_dir
from agentic_security.logutils import logger

CACHE_DIR = ensure_cache_dir(Path(__file__).parent / ".cache_to_disk")

from cache_to_disk import delete_old_disk_caches  # noqa: E402  # isort: skip

# Silence noisy third-party warnings that do not impact test behavior
warnings.filterwarnings("ignore", category=InconsistentVersionWarning)
try:
    from langchain_core._api import LangChainDeprecationWarning

    warnings.filterwarnings("ignore", category=LangChainDeprecationWarning)
except Exception:  # pragma: no cover - fallback for older langchain versions
    warnings.filterwarnings(
        "ignore",
        category=DeprecationWarning,
        module=r"langchain\\.agents",
        message=r".*langchain_core.pydantic_v1.*",
    )


def pytest_runtest_setup(item):
    if "slow" in item.keywords and not os.getenv("RUN_SLOW_TESTS"):
        pytest.skip("Skipping slow test")


@pytest.fixture(autouse=True, scope="session")
def setup_delete_old_disk_caches():
    logger.info("delete_old_disk_caches at %s", CACHE_DIR)
    try:
        delete_old_disk_caches()
    except PermissionError:
        logger.warning("Skipping cache cleanup due to permissions for %s", CACHE_DIR)
    except OSError as exc:
        logger.warning("Skipping cache cleanup due to OS error: %s", exc)
