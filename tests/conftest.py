import os

import pytest


def pytest_runtest_setup(item):
    if "slow" in item.keywords and not os.getenv("RUN_SLOW_TESTS"):
        pytest.skip("Skipping slow test")
