from fastapi.testclient import TestClient

from agentic_security.app import app

client = TestClient(app)


def test_verify_relative_url_returns_400_not_500():
    """A relative-URL spec should fail parsing with a clean 400, not an
    uncaught 500. See https://github.com/msoedov/agentic_security/issues/149.
    """
    spec = "POST /chat HTTP/2\nHost: promptairlines.com\nContent-Type: application/json\n\n{}"
    response = client.post("/verify", json={"spec": spec})
    assert response.status_code == 400
    assert "Failed to parse HTTP spec" in response.json()["detail"]
