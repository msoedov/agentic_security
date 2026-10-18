from datetime import timedelta

import httpx
import pytest
from fastapi.testclient import TestClient

from agentic_security.app import app
from agentic_security.http_spec import LLMSpec

client = TestClient(app)

SPEC = 'POST https://llm.example/v1\nContent-Type: application/json\n\n{"prompt": "<<PROMPT>>"}'


# The UI shows any 5xx from /verify as "server crashed". A broken target or a
# bad spec is user input, so it must come back as 400 with a readable reason (#149).
@pytest.mark.parametrize(
    "upstream_status,expected_status",
    [(200, 200), (401, 400), (404, 400), (500, 400), (503, 400)],
)
def test_verify_maps_upstream_errors_to_400(
    monkeypatch, upstream_status, expected_status
):
    async def fake_verify(self):
        r = httpx.Response(upstream_status, text="upstream body")
        r.elapsed = timedelta(seconds=0.1)
        return r

    monkeypatch.setattr(LLMSpec, "verify", fake_verify)
    r = client.post("/verify", json={"spec": SPEC})
    assert r.status_code == expected_status
    if expected_status == 400:
        assert (
            r.json()["detail"]
            == f"Upstream returned HTTP {upstream_status}: upstream body"
        )


@pytest.mark.parametrize("spec", ["POST /relative/path\n\n{}", "not a spec at all"])
def test_verify_invalid_spec_is_400(spec):
    assert client.post("/verify", json={"spec": spec}).status_code == 400
