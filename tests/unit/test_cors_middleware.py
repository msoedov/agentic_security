"""Tests for CORS allowlist configuration (agentic_security #334)."""

import os
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

from agentic_security.middleware.cors import get_cors_allow_origins, setup_cors


def _get_cors_options(app: FastAPI) -> dict:
    for middleware in app.user_middleware:
        if middleware.cls is CORSMiddleware:
            return middleware.kwargs
    return {}


class TestCorsSetup:
    def test_default_allowlist_is_empty(self):
        with patch.dict(os.environ, {}, clear=True):
            with patch(
                "agentic_security.middleware.cors.settings_var",
                return_value=[],
            ):
                assert get_cors_allow_origins() == []

    def test_env_override_parses_comma_separated_origins(self):
        with patch.dict(
            os.environ,
            {
                "AGENTIC_SECURITY_CORS_ORIGINS": "http://localhost:3000, http://127.0.0.1:3000"
            },
            clear=True,
        ):
            assert get_cors_allow_origins() == [
                "http://localhost:3000",
                "http://127.0.0.1:3000",
            ]

    def test_cors_middleware_uses_allowlist_without_credentials(self):
        app = FastAPI()
        with patch(
            "agentic_security.middleware.cors.get_cors_allow_origins",
            return_value=["http://localhost:3000"],
        ):
            setup_cors(app)
        opts = _get_cors_options(app)
        assert opts["allow_origins"] == ["http://localhost:3000"]
        assert opts["allow_credentials"] is False

    def test_preflight_from_allowlisted_origin_succeeds(self):
        app = FastAPI()

        @app.get("/probe")
        async def probe():
            return {"ok": True}

        with patch(
            "agentic_security.middleware.cors.get_cors_allow_origins",
            return_value=["http://localhost:3000"],
        ):
            setup_cors(app)

        client = TestClient(app, raise_server_exceptions=True)
        response = client.options(
            "/probe",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.status_code == 200
        assert (
            response.headers.get("access-control-allow-origin")
            == "http://localhost:3000"
        )

    def test_preflight_from_foreign_origin_is_rejected_with_empty_allowlist(self):
        app = FastAPI()

        @app.get("/probe")
        async def probe():
            return {"ok": True}

        with patch(
            "agentic_security.middleware.cors.get_cors_allow_origins",
            return_value=[],
        ):
            setup_cors(app)

        client = TestClient(app, raise_server_exceptions=True)
        response = client.options(
            "/probe",
            headers={
                "Origin": "http://evil.example.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.status_code == 400
