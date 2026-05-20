import io
import asyncio
import json
from datetime import datetime, timedelta
from threading import Event
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from agentic_security.routes import scan

# Dummy LLMSpec for success tests
class DummyLLMSpec:
    def __init__(self, spec_string):
        self.spec_string = spec_string
    async def verify(self):
        class DummyResponse:
            status_code = 200
            text = "verification succeeded"
            elapsed = timedelta(seconds=0.5)
        return DummyResponse()
    @classmethod
    def from_string(cls, spec_string):
        return DummyLLMSpec(spec_string)

# Dummy scan_router generator to simulate streaming responses
async def dummy_scan_router(request_factory, scan_parameters, tools_inbox, stop_event):
    for i in range(2):
        yield f"result {i}"

# Define a dummy Secrets class for testing purposes.
class DummySecrets:
    def __init__(self):
        self.secrets = {}

# Create FastAPI app for testing and include the scan router.
@pytest.fixture
def app():
    app = FastAPI()
    app.include_router(scan.router)
    return app

@pytest.fixture
def client(app):
    return TestClient(app)

@pytest.fixture(autouse=True)
def patch_dependencies(monkeypatch):
    # Patch LLMSpec used in the routes with our dummy implementation.
    monkeypatch.setattr(scan, "LLMSpec", DummyLLMSpec)
    # Patch fuzzer.scan_router to use our dummy scanning generator.
    monkeypatch.setattr(scan.fuzzer, "scan_router", dummy_scan_router)
    # Patch get_stop_event to return a dummy Event.
    dummy_event = Event()
    monkeypatch.setattr(scan, "get_stop_event", lambda: dummy_event)
    # Patch get_tools_inbox to return None.
    monkeypatch.setattr(scan, "get_tools_inbox", lambda: None)
    # Patch set_current_run to be a no-op.
    monkeypatch.setattr(scan, "set_current_run", lambda x: None)
    # Patch get_in_memory_secrets to return a DummySecrets instance.
    monkeypatch.setattr(scan, "get_in_memory_secrets", lambda: DummySecrets())
    # Ensure Scan.with_secrets is a no-op if not already implemented.
    if not hasattr(scan.Scan, "with_secrets"):
        monkeypatch.setattr(scan.Scan, "with_secrets", lambda self, secrets: None)

def test_verify_success(client):
    """Test /verify endpoint for a successful verification."""
    data = {"spec": "dummy"}
    response = client.post("/verify", json=data)
    res_json = response.json()
    assert response.status_code == 200
    assert res_json["status_code"] == 200
    assert res_json["body"] == "verification succeeded"
    assert "elapsed" in res_json
    assert "timestamp" in res_json

def test_verify_failure(client, monkeypatch):
    """Test /verify endpoint when verification fails."""
    class DummyLLMSpecFailure:
        def __init__(self, spec_string):
            self.spec_string = spec_string
        async def verify(self):
            raise Exception("verification error")
        @classmethod
        def from_string(cls, spec_string):
            return DummyLLMSpecFailure(spec_string)
    monkeypatch.setattr(scan, "LLMSpec", DummyLLMSpecFailure)
    data = {"spec": "bad"}
    response = client.post("/verify", json=data)
    assert response.status_code == 400
    assert "verification error" in response.text

def test_scan(client):
    """Test /scan endpoint to ensure streaming response works."""
    data = {"llmSpec": "dummy", "optimize": False, "maxBudget": 10, "enableMultiStepAttack": False}
    response = client.post("/scan", json=data)
    assert response.status_code == 200
    content = list(response.iter_lines())
    expected = ["result 0", "result 1"]
    assert content == expected

def test_stop_scan(client):
    """Test /stop endpoint to ensure scan stopping functionality."""
    dummy_event = scan.get_stop_event()
    dummy_event.clear()
    response = client.post("/stop")
    assert response.status_code == 200
    assert response.json() == {"status": "Scan stopped"}
    assert dummy_event.is_set()

def test_scan_csv(client):
    """Test /scan-csv endpoint with CSV file and llmSpec upload."""
    csv_content = b"col1,col2\nvalue1,value2"
    llm_spec_content = b"dummy"
    files = {
        "file": ("dummy.csv", csv_content, "text/csv"),
        "llmSpec": ("spec.txt", llm_spec_content, "text/plain"),
    }
    response = client.post(
        "/scan-csv",
        files=files,
        data={"optimize": "false", "maxBudget": "10", "enableMultiStepAttack": "false"},
    )
    assert response.status_code == 200
    content = list(response.iter_lines())
    expected = ["result 0", "result 1"]
    assert content == expected