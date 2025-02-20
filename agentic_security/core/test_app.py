import os

import pytest

from agentic_security.core.app import expand_secrets


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
