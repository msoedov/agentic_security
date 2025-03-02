import pytest
import os


def pytest_runtest_setup(item):
    if "slow" in item.keywords and not os.getenv("RUN_SLOW_TESTS"):
        pytest.skip("Skipping slow test")
