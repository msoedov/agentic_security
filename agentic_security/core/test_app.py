import os

import pytest

from agentic_security.core.app import expand_secrets


@pytest.fixture(autouse=True)
def reset_globals():
    """
    Reset globals (_secrets, current_run, tools_inbox, stop_event) before each test.
    This ensures tests run in a clean state.
    """
    from agentic_security.core.app import _secrets, current_run, get_tools_inbox, get_stop_event
    _secrets.clear()
    current_run["spec"] = ""
    current_run["id"] = ""
    # Clear tools_inbox queue
    queue = get_tools_inbox()
    while not queue.empty():
        queue.get_nowait()
    # Reset stop_event if it is set
    event = get_stop_event()
    if event.is_set():
        event.clear()
def setup_env_vars():
    # Set up environment variables for testing
    os.environ["TEST_ENV_VAR"] = "test_value"


def test_expand_secrets_with_env_var():
    os.environ["TEST_ENV_VAR"] = "test_value"
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

import asyncio
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from agentic_security.core.app import create_app, get_tools_inbox, get_stop_event, get_current_run, set_current_run, get_secrets, set_secrets, expand_secrets

class DummyLLMSpec:
    """A dummy LLMSpec for testing purposes."""
    pass

def test_create_app():
    """Test that create_app returns a FastAPI app with ORJSONResponse."""
    app = create_app()
    assert isinstance(app, FastAPI)
    assert app.router.default_response_class == ORJSONResponse

def test_get_tools_inbox():
    """Test that get_tools_inbox returns a Queue instance."""
    queue = get_tools_inbox()
    from asyncio import Queue
    assert isinstance(queue, Queue)

def test_get_stop_event():
    """Test that get_stop_event returns an Event instance."""
    event = get_stop_event()
    from asyncio import Event
    assert isinstance(event, Event)

def test_get_current_run_initial():
    """Test that get_current_run returns the initial current run dictionary."""
    current = get_current_run()
    # The initial dictionary should have an empty spec and id.
    assert current["spec"] == ""
    assert current["id"] == ""

def test_set_current_run():
    """Test that set_current_run updates the current run with the dummy LLMSpec."""
    dummy_spec = DummyLLMSpec()
    updated = set_current_run(dummy_spec)
    assert updated["spec"] is dummy_spec
    # Ensure that the id is computed as hash(id(dummy_spec))
    expected_id = hash(id(dummy_spec))
    assert updated["id"] == expected_id

def test_get_and_set_secrets():
    """Test that set_secrets updates the secrets dictionary and get_secrets returns the updated values."""
    # Clear any previously set secrets
    secrets_before = get_secrets().copy()
    os.environ["MY_SECRET"] = "secret_value"
    new_secrets = {"key1": "$MY_SECRET", "key2": "plain"}
    updated = set_secrets(new_secrets)
    assert updated["key1"] == "secret_value"
    assert updated["key2"] == "plain"

def test_expand_secrets_multiple_keys():
    """Test expand_secrets with multiple keys, including one with an environment variable,
    one with a non-existent variable, and one that is plain."""
    os.environ["TEST_ENV_VAR"] = "test_value"
    secrets = {"env_key": "$TEST_ENV_VAR", "nonexistent_key": "$NON_EXISTENT", "plain_key": "value"}
    expand_secrets(secrets)
    assert secrets["env_key"] == "test_value"
    # For a non-existent environment variable, os.getenv returns None
    assert secrets["nonexistent_key"] is None
    # Plain values should not be changed.
    assert secrets["plain_key"] == "value"
def test_expand_secrets_with_space_after_dollar():
    """Test expand_secrets when the value has a dollar sign followed by a space.
    Since the value does not start strictly with "$", the secret remains unchanged.
    Also verifies that the stripping in expand_secrets (via strip("$"))
    will remove both dollar and any whitespace if the value actually started with '$'.
    """
    os.environ["SPACED_VAR"] = "spaced_value"
    secrets = {"key": "$ SPACED_VAR"}
    expand_secrets(secrets)
    # " $ SPACED_VAR" after strip("$") becomes " SPACED_VAR" which is not a valid env key so returns None.
    assert secrets["key"] is None

def test_set_secrets_update_existing():
    """Test that set_secrets updates an existing secret and retains previously set keys."""
    os.environ["VAR1"] = "value1"
    os.environ["VAR2"] = "value2"
    result_first = set_secrets({"a": "$VAR1", "b": "b_val"})
    assert result_first["a"] == "value1"
    # Change VAR1 in environment and update secret "a", and add secret "c"
    os.environ["VAR1"] = "new_value1"
    result_second = set_secrets({"a": "$VAR1", "c": "$VAR2"})
    assert result_second["a"] == "new_value1"
    assert result_second["b"] == "b_val"
    assert result_second["c"] == "value2"

def test_tools_inbox_state():
    """Test that get_tools_inbox returns the same queue instance 
    and that the queue state persists across multiple calls.
    """
    from asyncio import Queue
    inbox1 = get_tools_inbox()
    inbox1.put_nowait("message")
    inbox2 = get_tools_inbox()
    # inbox2 should contain the "message" from inbox1
    msg = inbox2.get_nowait()
    assert msg == "message"

def test_stop_event_state():
    """Test that stop_event can be set and cleared, and its state persists."""
    event = get_stop_event()
    # Initially the event should not be set
    assert not event.is_set()
    event.set()
    assert event.is_set()
    event.clear()
    assert not event.is_set()

def test_set_current_run_returns_global_dict():
    """Test that set_current_run returns the same global current_run dictionary
    as returned by get_current_run.
    """
    dummy_spec = DummyLLMSpec()
    updated = set_current_run(dummy_spec)
    current = get_current_run()
    assert updated is current
def test_get_secrets_initial():
    """Test that get_secrets returns an empty dictionary initially."""
    assert get_secrets() == {}

def test_set_secrets_empty():
    """Test that setting an empty secrets dictionary does not modify existing secrets."""
    # first set initial secrets
    initial = {"key": "value"}
    set_secrets(initial)
    # update with an empty dict – the existing keys remain
    result = set_secrets({})
    assert result == initial

def test_update_current_run_twice():
    """Test updating current run twice with different LLMSpec values."""
    dummy1 = DummyLLMSpec()
    dummy2 = DummyLLMSpec()
    set_current_run(dummy1)
    first = get_current_run().copy()
    set_current_run(dummy2)
    second = get_current_run().copy()
    # first update should hold dummy1, second should hold dummy2
    assert first["spec"] is dummy1
    assert second["spec"] is dummy2
    # Ensure that id has changed (using hash(id(dummy_spec)))
    assert first["id"] != second["id"]

def test_expand_secrets_trailing_whitespace():
    """Test expand_secrets when the secret value has trailing whitespace after the dollar sign.
    The trailing whitespace remains after stripping only the dollar sign, so the looked-up environment variable key will not match.
    """
    os.environ["TRIM_TEST"] = "trimmed"
    secrets = {"key": "$TRIM_TEST "}
    expand_secrets(secrets)
    # Since "TRIM_TEST " (with trailing space) is not set in the environment, the secret should be None.
    assert secrets["key"] is None
def test_expand_secrets_empty_dict():
    """Test expand_secrets with an empty dictionary does nothing."""
    secrets = {}
    expand_secrets(secrets)
    assert secrets == {}

def test_expand_secrets_with_non_string_value():
    """Test that expand_secrets raises an AttributeError when a secret value is not a string."""
    secrets = {"key": 123}
    with pytest.raises(AttributeError):
        expand_secrets(secrets)

def test_expand_secrets_multiple_dollar_signs():
    """Test expand_secrets with a value that contains multiple leading dollar signs.
    The extra dollar signs are removed by the strip method.
    """
    os.environ["MULTI_DOLLAR_VAR"] = "multi_value"
    secrets = {"key": "$$MULTI_DOLLAR_VAR"}
    expand_secrets(secrets)
    # After stripping, "$$MULTI_DOLLAR_VAR".strip("$") returns "MULTI_DOLLAR_VAR"
    assert secrets["key"] == "multi_value"