import os

import pytest
from cache_to_disk import delete_old_disk_caches
from agentic_security.logutils import logger


def pytest_runtest_setup(item):
    if "slow" in item.keywords and not os.getenv("RUN_SLOW_TESTS"):
        pytest.skip("Skipping slow test")


@pytest.fixture(autouse=True, scope="session")
def setup_delete_old_disk_caches():
    logger.info("delete_old_disk_caches")
    delete_old_disk_caches()
