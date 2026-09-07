from unittest.mock import AsyncMock, patch

import httpx
from fastapi.testclient import TestClient

from agentic_security.app import app

client = TestClient(app)

MINIMAL_SPEC = """POST http://127.0.0.1:8080/v1/chat/completions HTTP/1.1
Content-Type: application/json

{"model":"test","messages":[{"role":"user","content":"{{prompt}}"}]}
"""


def test_verify_maps_upstream_5xx_to_client_error():
    upstream = httpx.Response(500, text="model unavailable")

    with patch(
        "agentic_security.routes.scan.LLMSpec.verify",
        new=AsyncMock(return_value=upstream),
    ):
        response = client.post("/verify", json={"spec": MINIMAL_SPEC})

    assert response.status_code == 400
    assert "Upstream verification failed with HTTP 500" in response.json()["detail"]
