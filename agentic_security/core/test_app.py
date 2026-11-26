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
    assert secrets["secret_key"] is None


def test_expand_secrets_without_dollar_sign():
    secrets = {"secret_key": "plain_value"}
    expand_secrets(secrets)
    assert secrets["secret_key"] == "plain_value"


def test_expand_secrets_skips_none_and_non_string_values():
    secrets = {"missing": None, "count": 42, "env": "$TEST_ENV_VAR"}
    expand_secrets(secrets)
    assert secrets == {"missing": None, "count": 42, "env": "test_value"}


def test_set_secrets_repeated_calls_with_unset_and_dollar_values(monkeypatch):
    monkeypatch.setattr(app_module, "_secrets", {})
    monkeypatch.delenv("NON_EXISTENT_VAR", raising=False)
    monkeypatch.setenv("DOLLAR_SECRET", "$literal_token_value")
    monkeypatch.delenv("literal_token_value", raising=False)

    set_secrets({"missing": "$NON_EXISTENT_VAR", "token": "$DOLLAR_SECRET"})
    set_secrets({"present": "$TEST_ENV_VAR"})

    assert get_secrets() == {
        "missing": None,
        "token": "$literal_token_value",
        "present": "test_value",
    }
