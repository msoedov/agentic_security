import asyncio
from datetime import timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Import the router to test from our original code
from agentic_security.routes.scan import router

# Define a dummy specification for testing the /verify endpoint
class DummySpecification:
    async def verify(self):
        class DummyResponse:
            status_code = 200
            text = "OK"
            elapsed = timedelta(seconds=0.5)
        return DummyResponse()

def dummy_from_string(spec_str):
    # For testing, we simply return our dummy specification
    return DummySpecification()

# Create a FastAPI app and include the router under test
app = FastAPI()
app.include_router(router)

@pytest.fixture(autouse=True)
def override_dependencies(monkeypatch):
    """
    Override dependencies in the scan module for testing purposes.
    This includes plugging in a dummy stop event, dummy tools inbox,
    patching LLMSpec.from_string, and replacing fuzzer.scan_router with a dummy async generator.
    """
    # Override get_stop_event to return an asyncio.Event
    monkeypatch.setattr("agentic_security.routes.scan.get_stop_event", lambda: asyncio.Event())

    # Override get_tools_inbox to return None (or a dummy value)
    monkeypatch.setattr("agentic_security.routes.scan.get_tools_inbox", lambda: None)

    # Patch LLMSpec.from_string to use our dummy specification
    from agentic_security.http_spec import LLMSpec
    monkeypatch.setattr(LLMSpec, "from_string", staticmethod(dummy_from_string))

    # Patch fuzzer.scan_router to return a dummy asynchronous generator
    async def dummy_scan_router(*args, **kwargs):
        # Yield several dummy results
        for i in range(3):
            yield f"test_result_{i}"
    DummyFuzzer = type("DummyFuzzer", (), {"scan_router": dummy_scan_router})
    monkeypatch.setattr("agentic_security.routes.scan.fuzzer", DummyFuzzer)
    yield

def test_verify_endpoint():
    """Test the /verify endpoint returns the expected dummy response."""
    payload = {"spec": "dummy_spec"}
    client = TestClient(app)
    response = client.post("/verify", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status_code"] == 200
    assert data["body"] == "OK"
    assert "elapsed" in data
    assert "timestamp" in data

def test_stop_scan_endpoint():
    """Test that the /stop endpoint returns a success message."""
    client = TestClient(app)
    response = client.post("/stop")
    assert response.status_code == 200
    data = response.json()
    assert data == {"status": "Scan stopped"}

def test_scan_endpoint():
    """Test the /scan endpoint returns a streaming response with dummy scan results."""
    payload = {
        "llmSpec": "dummy_spec",
        "optimize": False,
        "maxBudget": 1000,
        "enableMultiStepAttack": False,
    }
    client = TestClient(app)
    with client.stream("POST", "/scan", json=payload) as response:
        assert response.status_code == 200
        # Read all chunks from the streaming response
        content = b"".join(response.iter_bytes())
        # Check that the dummy scan results are present in the output
        for i in range(3):
            assert f"test_result_{i}".encode("utf-8") in content