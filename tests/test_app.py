import pytest
import asyncio
from fastapi import FastAPI
from asyncio import Queue, Event
from agentic_security.core.app import create_app, get_tools_inbox, get_stop_event, get_current_run, set_current_run

class TestApp:
    """Test suite for agentic_security.core.app module."""

    def test_create_app(self):
        """Test that create_app returns a FastAPI instance."""
        app = create_app()
        assert isinstance(app, FastAPI)

    @pytest.mark.asyncio
    async def test_get_tools_inbox(self):
        """Test that get_tools_inbox returns the global Queue instance."""
        queue1 = get_tools_inbox()
        await queue1.put("test item")
        queue2 = get_tools_inbox()
        result = queue2.get_nowait()
        assert result == "test item"

    def test_get_stop_event(self):
        """Test that get_stop_event returns the global Event instance and is not set initially."""
        event = get_stop_event()
        assert isinstance(event, Event)
        assert not event.is_set()

    def test_current_run_initial(self):
        """Test that get_current_run returns the global current_run with default values initially."""
        run = get_current_run()
        # Default values should be empty strings
        assert run["spec"] == ""
        assert run["id"] == ""

    def test_set_current_run(self):
        """Test that set_current_run correctly updates current_run."""
        spec = "test run"
        result = set_current_run(spec)
        expected_id = hash(id(spec))
        # Verify that spec is set correctly
        assert result["spec"] == spec
        assert result["id"] == expected_id

    def test_current_run_after_set(self):
        """Test that get_current_run returns the updated current_run after set_current_run is called."""
        spec = "another test run"
        set_current_run(spec)
        current = get_current_run()
        assert current["spec"] == spec
        assert current["id"] == hash(id(spec))
    def test_tools_inbox_same_instance(self):
        """Test that get_tools_inbox returns the same Queue instance by default."""
        queue1 = get_tools_inbox()
        queue2 = get_tools_inbox()
        assert queue1 is queue2

    def test_stop_event_set(self):
        """Test that setting the stop event is reflected in subsequent calls."""
        event = get_stop_event()
        event.set()  # set the global event
        # Now, subsequent calls should return the same event which is set.
        event2 = get_stop_event()
        assert event2.is_set()

    def test_set_current_run_with_none(self):
        """Test that set_current_run handles None as a valid input and updates current_run accordingly."""
        result = set_current_run(None)
        expected_id = hash(id(None))
        assert result["spec"] is None
        assert result["id"] == expected_id

    def test_multiple_current_run_assignments(self):
        """Test multiple assignments to current_run to ensure it always updates correctly."""
        first_spec = "first run"
        result1 = set_current_run(first_spec)
        expected_id1 = hash(id(first_spec))
        assert result1["spec"] == first_spec
        assert result1["id"] == expected_id1

        second_spec = "second run"
        result2 = set_current_run(second_spec)
        expected_id2 = hash(id(second_spec))
        assert result2["spec"] == second_spec
        assert result2["id"] == expected_id2

        current = get_current_run()
        # The current_run should reflect the latest assignment.
        assert current["spec"] == second_spec
        assert current["id"] == expected_id2
    @pytest.mark.asyncio
    async def test_empty_tools_inbox_exception(self):
        """Test that calling get_nowait on an empty tools_inbox raises QueueEmpty."""
        from asyncio import QueueEmpty
        queue = get_tools_inbox()
        # Clear any existing items in the queue
        while True:
            try:
                queue.get_nowait()
            except QueueEmpty:
                break
        with pytest.raises(QueueEmpty):
            queue.get_nowait()

    def test_set_current_run_with_dict(self):
        """Test that set_current_run correctly handles a dictionary input as spec."""
        spec = {"key": "value"}
        result = set_current_run(spec)
        expected_id = hash(id(spec))
        assert result["spec"] == spec
        assert result["id"] == expected_id
    @pytest.mark.asyncio
    async def test_stop_event_wait(self):
        """Test that waiting on the stop event returns once the event is set."""
        event = get_stop_event()
        event.clear()  # ensure event is not set
        async def waiter():
            await event.wait()
            return True
        waiter_task = asyncio.create_task(waiter())
        # Wait a moment to ensure the waiter is pending
        await asyncio.sleep(0.1)
        assert not waiter_task.done()
        event.set()
        result = await waiter_task
        assert result is True

    def test_set_current_run_with_int(self):
        """Test that set_current_run handles an integer input as spec."""
        spec = 12345
        result = set_current_run(spec)
        expected_id = hash(id(spec))
        assert result["spec"] == spec
        assert result["id"] == expected_id

    def test_create_app_routes(self):
        """Test that create_app returns a FastAPI instance with default routes available."""
        app = create_app()
        paths = [route.path for route in app.routes]
        # Check that the default OpenAPI route exists
        assert "/openapi.json" in paths

    @pytest.mark.asyncio
    async def test_tools_inbox_async_put_get_order(self):
        """Test that tools_inbox preserves order when items are added and retrieved asynchronously."""
        queue = get_tools_inbox()
        # Clear any existing items in the queue
        from asyncio import QueueEmpty
        while True:
            try:
                queue.get_nowait()
            except QueueEmpty:
                break
        items = ["first", "second", "third"]
        for item in items:
            await queue.put(item)
        result_items = []
        for _ in items:
            result_items.append(await queue.get())
        assert result_items == items