import httpx
import pytest

from agentic_security.mcp import main as mcp_main


class MockResponse:
    def __init__(self, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self.payload = payload
        self.text = text
        self.request = httpx.Request("GET", "http://testserver")

    def json(self):
        if isinstance(self.payload, Exception):
            raise self.payload
        return self.payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                f"{self.status_code} error",
                request=self.request,
                response=self,
            )


class MockAsyncClient:
    def __init__(self, response=None, exc=None):
        self.response = response
        self.exc = exc
        self.calls = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False

    async def request(self, method, url, json=None):
        self.calls.append((method, url, json))
        if self.exc:
            raise self.exc
        return self.response


def use_client(monkeypatch, client):
    monkeypatch.setattr(mcp_main.httpx, "AsyncClient", lambda: client)
    return client


@pytest.mark.asyncio
async def test_verify_llm_returns_backend_json(monkeypatch):
    client = use_client(
        monkeypatch, MockAsyncClient(MockResponse(payload={"ok": True}))
    )

    result = await mcp_main.verify_llm("openai:gpt-4")

    assert result == {"ok": True}
    assert client.calls == [
        (
            "POST",
            "http://0.0.0.0:8718/verify",
            {"spec": "openai:gpt-4"},
        )
    ]


@pytest.mark.asyncio
async def test_start_scan_returns_http_status_error(monkeypatch):
    response = MockResponse(status_code=503, payload={"detail": "backend unavailable"})
    use_client(monkeypatch, MockAsyncClient(response))

    result = await mcp_main.start_scan("openai:gpt-4", 10)

    assert result["error"]["type"] == "http_status"
    assert result["error"]["status_code"] == 503
    assert result["error"]["response"] == {"detail": "backend unavailable"}


@pytest.mark.asyncio
async def test_get_data_config_returns_request_error(monkeypatch):
    request = httpx.Request("GET", "http://0.0.0.0:8718/v1/data-config")
    error = httpx.ConnectError("connection refused", request=request)
    use_client(monkeypatch, MockAsyncClient(exc=error))

    result = await mcp_main.get_data_config()

    assert result["error"]["type"] == "request"
    assert "connection refused" in result["error"]["message"]


@pytest.mark.asyncio
async def test_get_spec_templates_returns_invalid_json_error(monkeypatch):
    response = MockResponse(payload=ValueError("bad json"))
    use_client(monkeypatch, MockAsyncClient(response))

    result = await mcp_main.get_spec_templates()

    assert result["error"]["type"] == "invalid_json"
    assert "bad json" in result["error"]["message"]
