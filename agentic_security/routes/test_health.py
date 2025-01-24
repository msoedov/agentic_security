from fastapi.testclient import TestClient

from ..app import app


def test_health_check():
    """Test the health check endpoint."""
    client = TestClient(app)

    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
