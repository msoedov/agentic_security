import os

import pytest

from agentic_security.core import app as app_module
from agentic_security.core.app import expand_secrets, get_secrets, set_secrets


@pytest.fixture(autouse=True)
def setup_env_vars():
    # Set up environment variables for testing
    os.environ["TEST_ENV_VAR"] = "test_value"


def test_expand_secrets_with_env_var():
    secrets = {"secret_key": "$TEST_ENV_VAR"}
    expand_secrets(secrets)
    assert secrets["secret_key"] == "test_value"


def test_expand_secrets_without_env_var():
    secrets = {"secret_key": "$NON_EXISTENT_VAR"}
    expand_secrets(secrets)
    assert secrets["secret_key"] == ""


def test_expand_secrets_without_dollar_sign():
    secrets = {"secret_key": "plain_value"}
    expand_secrets(secrets)
    assert secrets["secret_key"] == "plain_value"


def test_set_secrets_repeated_calls_with_unset_env_vars(monkeypatch):
    monkeypatch.setattr(app_module, "_secrets", {})
    monkeypatch.delenv("NON_EXISTENT_VAR", raising=False)

    set_secrets({"missing": "$NON_EXISTENT_VAR"})
    set_secrets({"present": "$TEST_ENV_VAR"})

    assert get_secrets() == {
        "missing": "",
        "present": "test_value",
    }
