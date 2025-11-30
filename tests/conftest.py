import os
import warnings

import pytest
from cache_to_disk import delete_old_disk_caches
from sklearn.exceptions import InconsistentVersionWarning

from agentic_security.logutils import logger

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
    logger.info("delete_old_disk_caches")
    delete_old_disk_caches()
