import os

import pytest

from agentic_security.core.app import expand_secrets


@pytest.fixture(autouse=True)
def setup_env_vars():
    # Set up environment variables for testing
    os.environ["TEST_ENV_VAR"] = "test_value"

@pytest.fixture(autouse=True)
def reset_globals():
    """Reset global state between tests."""
    from agentic_security.core.app import current_run, _secrets, tools_inbox, get_stop_event
    # Reset current_run to initial empty state.
    current_run["spec"] = ""
    current_run["id"] = ""
    # Clear _secrets.
    _secrets.clear()
    # Drain the tools_inbox queue.
    while not tools_inbox.empty():
        try:
            tools_inbox.get_nowait()
        except Exception:
            break
    # Ensure stop_event is cleared.
    get_stop_event().clear()
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

def test_create_app():
    """Test that FastAPI app is created with ORJSONResponse as the default response class."""
    from fastapi.responses import ORJSONResponse
    from agentic_security.core.app import create_app
    app = create_app()
    assert app is not None
    # Add a dummy route to verify that ORJSONResponse is used as the default response class
    @app.get("/dummy")
    def dummy():
        return {"message": "dummy"}
    # Retrieve the dummy route from the application's routes
    dummy_route = next((route for route in app.routes if getattr(route, 'path', None) == "/dummy"), None)
    assert dummy_route is not None
    # Assert that the route's default response class is ORJSONResponse
    from fastapi.responses import ORJSONResponse
    assert dummy_route.response_class == ORJSONResponse

def test_get_tools_inbox():
    """Test that the global tools inbox is a Queue and works as expected."""
    from asyncio import Queue
    from agentic_security.core.app import get_tools_inbox, tools_inbox
    inbox = get_tools_inbox()
    assert isinstance(inbox, Queue)
    # Test that the returned inbox is the same global instance.
    assert inbox is tools_inbox
    # Enqueue and then dequeue a message.
    inbox.put_nowait("test_message")
    assert inbox.get_nowait() == "test_message"

def test_get_stop_event():
    """Test that the global stop event is returned correctly and can be set and cleared."""
    from asyncio import Event
    from agentic_security.core.app import get_stop_event, stop_event
    event = get_stop_event()
    assert isinstance(event, Event)
    event.set()
    # Verify that the global stop event is set.
    assert stop_event.is_set()
    event.clear()
    assert not stop_event.is_set()

def test_current_run_initial_and_set():
    """Test getting and setting of the global current_run variable."""
    from agentic_security.core.app import get_current_run, set_current_run
    # Because global state might be mutated by other tests, we focus on the update logic.
    class DummyLLMSpec:
        pass
    dummy_spec = DummyLLMSpec()
    updated_run = set_current_run(dummy_spec)
    assert updated_run["spec"] is dummy_spec
    assert updated_run["id"] == hash(id(dummy_spec))

def test_get_and_set_secrets():
    """Test that secrets are set and retrieved correctly, including environment variable expansion."""
    from agentic_security.core.app import get_secrets, set_secrets
    import os
    # Set up an environment variable for expansion.
    os.environ["NEW_SECRET"] = "secret_value"
    new_secrets = {"plain": "value", "env": "$NEW_SECRET"}
    set_secrets(new_secrets)
    secrets = get_secrets()
    assert secrets["plain"] == "value"
    assert secrets["env"] == "secret_value"

def test_set_secrets_update():
    """Test that setting secrets multiple times updates the secrets without losing existing keys."""
    from agentic_security.core.app import get_secrets, set_secrets
    import os
    # Initialize secrets with a plain value.
    set_secrets({"key1": "initial"})
    # Update key1 with an environment variable and add key2.
    os.environ["KEY1"] = "updated_value"
    set_secrets({"key1": "$KEY1", "key2": "new_value"})
    secrets = get_secrets()
    assert secrets["key1"] == "updated_value"
    assert secrets["key2"] == "new_value"
def test_get_current_run_initial_value():
    """Test that the global current_run returns empty values initially."""
    from agentic_security.core.app import get_current_run
    run = get_current_run()
    # Since reset_globals fixture runs before each test, the initial values should be empty.
    assert run["spec"] == ""
    assert run["id"] == ""

def test_expand_secrets_with_whitespace():
    """Test expand_secrets when the secret value has extra whitespace after the dollar sign."""
    from agentic_security.core.app import expand_secrets
    # Provide a secret with extra whitespace after '$'; lookup will likely fail.
    secrets = {"secret_key": "$   NON_EXISTENT_VAR"}
    expand_secrets(secrets)
    # os.getenv("   NON_EXISTENT_VAR") returns None, so the secret value should be None.
    assert secrets["secret_key"] is None

def test_set_secrets_empty():
    """Test that setting secrets with an empty dictionary does not change the global secrets."""
    from agentic_security.core.app import get_secrets, set_secrets
    # First, set a secret.
    set_secrets({"key": "value"})
    secrets_before = get_secrets().copy()
    # Then call set_secrets with an empty dict; expect no change to the existing secrets.
    set_secrets({})
    secrets_after = get_secrets()
    assert secrets_after == secrets_before
def test_expand_secrets_empty_dict():
    """Test that calling expand_secrets with an empty dictionary does not change it and does not error."""
    from agentic_security.core.app import expand_secrets
    secrets = {}
    expand_secrets(secrets)
    assert secrets == {}

def test_expand_secrets_env_empty():
    """Test expand_secrets with an environment variable that exists but has an empty string as value."""
    from agentic_security.core.app import expand_secrets
    os.environ["EMPTY_VAR"] = ""
    secrets = {"secret_key": "$EMPTY_VAR"}
    expand_secrets(secrets)
    assert secrets["secret_key"] == ""

def test_get_tools_inbox_multiple_messages():
    """Test that the global tools_inbox queue correctly handles multiple messages in FIFO order."""
    from asyncio import Queue
    from agentic_security.core.app import get_tools_inbox, tools_inbox
    inbox = get_tools_inbox()
    # Enqueue multiple messages.
    messages = ["first", "second", "third"]
    for msg in messages:
        inbox.put_nowait(msg)
    # Dequeue the messages and test the order.
    for expected_msg in messages:
        assert inbox.get_nowait() == expected_msg

def test_get_stop_event_multiple_calls():
    """Test that get_stop_event returns the same global event instance across multiple calls and that its modify operations are consistent."""
    from asyncio import Event
    from agentic_security.core.app import get_stop_event, stop_event
    event1 = get_stop_event()
    event2 = get_stop_event()
    # They should be the same instance.
    assert event1 is event2 is stop_event
    # Set the event using event1 and check that event2 is set.
    event1.set()
    assert event2.is_set()
    # Now clear using event2 and verify both are cleared.
    event2.clear()
    assert not event1.is_set()

def test_create_app_with_testclient():
    """
    Test that the FastAPI app created with create_app() works with TestClient,
    returns a valid HTTP response, and uses ORJSONResponse as the default response class.
    """
    from fastapi.testclient import TestClient
    from agentic_security.core.app import create_app
    app = create_app()
    @app.get("/hello")
    def hello():
        return {"hello": "world"}

    client = TestClient(app)
    response = client.get("/hello")
    assert response.status_code == 200
    # ORJSONResponse should produce a response with application/json content-type.
    assert "application/json" in response.headers["content-type"]

def test_get_current_run_mutability():
    """
    Test that modifying the dictionary returned by get_current_run directly affects the global state.
    """
    from agentic_security.core.app import get_current_run
    cr = get_current_run()
    cr["spec"] = "modified"
    cr["id"] = 12345
    # Verify that subsequent calls reflect the change (i.e., the dictionaries are the same reference).
    cr2 = get_current_run()
    assert cr2["spec"] == "modified"
    assert cr2["id"] == 12345