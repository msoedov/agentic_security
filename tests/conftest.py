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


# ── isolation from the developer's machine ──
#
# A developer with real keys exported must not make paid API calls by running
# the unit suite. Every *_API_KEY that is set gets swapped for a placeholder
# (keys that are unset stay unset, so "missing key" tests keep working).
# Tests that really need the network and a key opt in with @pytest.mark.live.

PLACEHOLDER_API_KEY = "sk-test-placeholder-not-a-real-key"


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "live: uses real API keys from the environment (opt-in)"
    )


@pytest.fixture(autouse=True)
def _no_real_api_keys(request, monkeypatch):
    if request.node.get_closest_marker("live"):
        yield
        return
    for name in list(os.environ):
        if name.endswith("_API_KEY") and os.environ[name]:
            monkeypatch.setenv(name, PLACEHOLDER_API_KEY)
    yield


@pytest.fixture
def fake_llm_api():
    """A running localhost OpenAI/Anthropic stand-in (tests/fakes/fake_llm_api.py)."""
    from tests.fakes.fake_llm_api import FakeLLMServer

    server = FakeLLMServer().start()
    yield server
    server.stop()
