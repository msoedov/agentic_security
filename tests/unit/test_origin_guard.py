"""Tests for OriginGuardMiddleware (agentic_security #334)."""

from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from agentic_security.middleware.origin_guard import OriginGuardMiddleware


def _app_with_guard() -> FastAPI:
    app = FastAPI()
    app.add_middleware(OriginGuardMiddleware)

    @app.post("/stop")
    async def stop_scan():
        return {"status": "Scan stopped"}

    @app.post("/scan-csv")
    async def scan_csv():
        return {"status": "ok"}

    @app.get("/health")
    async def health():
        return {"ok": True}

    return app


class TestOriginGuardMiddleware:
    def test_allows_requests_without_origin_header(self):
        client = TestClient(_app_with_guard())
        assert client.post("/stop").status_code == 200

    def test_blocks_foreign_origin_on_simple_post(self):
        client = TestClient(_app_with_guard())
        response = client.post(
            "/stop",
            headers={"Origin": "http://evil.example.com"},
        )
        assert response.status_code == 403

    def test_allows_same_origin_post(self):
        client = TestClient(_app_with_guard(), base_url="http://testserver")
        response = client.post(
            "/stop",
            headers={"Origin": "http://testserver"},
        )
        assert response.status_code == 200

    def test_allows_explicitly_allowlisted_origin(self):
        app = _app_with_guard()
        with patch(
            "agentic_security.middleware.origin_guard.get_cors_allow_origins",
            return_value=["http://localhost:3000"],
        ):
            client = TestClient(app)
            response = client.post(
                "/scan-csv",
                headers={"Origin": "http://localhost:3000"},
            )
        assert response.status_code == 200

    def test_does_not_guard_unlisted_routes(self):
        client = TestClient(_app_with_guard())
        response = client.get(
            "/health",
            headers={"Origin": "http://evil.example.com"},
        )
        assert response.status_code == 200
