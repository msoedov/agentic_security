"""Unit tests for CORS middleware configuration.

Verifies that cross-origin access is opt-in (issue #334): the previous
hard-coded ``allow_origins=["*"]`` exposed the unauthenticated ``/scan``,
``/scan-csv``, ``/stop`` and ``/verify`` endpoints to any web origin.

Policy under test:
- No credentials are ever allowed (CORS spec §3.2, Fetch §4.7).
- Allowed origins come from AGENTIC_SECURITY_CORS_ORIGINS; when unset, no
  cross-origin origin is permitted (safe default).
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

from agentic_security.middleware.cors import _resolve_allowed_origins, setup_cors


def _get_cors_options(app: FastAPI) -> dict:
    """Extract CORS middleware options from the app's middleware stack."""
    for middleware in app.user_middleware:
        if middleware.cls is CORSMiddleware:
            return middleware.kwargs
    return {}


class TestCorsSetup:
    """CORS middleware is configured correctly."""

    def test_cors_middleware_is_registered(self):
        """setup_cors adds CORSMiddleware to the app."""
        app = FastAPI()
        setup_cors(app)
        cls_names = [m.cls.__name__ for m in app.user_middleware]
        assert "CORSMiddleware" in cls_names

    def test_default_has_no_wildcard_origin(self):
        """By default (no env var) no cross-origin origin is allowed.

        This is the fix for #334: a wildcard origin must never be the default
        for an API that exposes unauthenticated scanning endpoints.
        """
        os.environ.pop("AGENTIC_SECURITY_CORS_ORIGINS", None)
        app = FastAPI()
        setup_cors(app)
        opts = _get_cors_options(app)
        allow_origins = opts.get("allow_origins", [])
        assert allow_origins == []
        assert opts.get("allow_credentials", True) is False

    def test_env_var_configures_explicit_origins(self):
        """AGENTIC_SECURITY_CORS_ORIGINS is parsed into the allow list."""
        os.environ["AGENTIC_SECURITY_CORS_ORIGINS"] = "https://app.example.com, https://dash.example.com"
        try:
            assert _resolve_allowed_origins() == [
                "https://app.example.com",
                "https://dash.example.com",
            ]
        finally:
            os.environ.pop("AGENTIC_SECURITY_CORS_ORIGINS", None)

    def test_disallowed_origin_gets_no_cors_header(self):
        """A non-allowed origin must not receive Access-Control-Allow-Origin."""
        os.environ.pop("AGENTIC_SECURITY_CORS_ORIGINS", None)
        app = FastAPI()

        @app.get("/probe")
        async def probe():
            return {"ok": True}

        setup_cors(app)
        client = TestClient(app)
        response = client.get("/probe", headers={"Origin": "http://evil.example.com"})
        assert "access-control-allow-origin" not in response.headers

    def test_allowed_origin_gets_cors_header(self):
        """An explicitly allowed origin receives Access-Control-Allow-Origin."""
        os.environ["AGENTIC_SECURITY_CORS_ORIGINS"] = "https://app.example.com"
        try:
            app = FastAPI()

            @app.get("/probe")
            async def probe():
                return {"ok": True}

            setup_cors(app)
            client = TestClient(app)
            response = client.get("/probe", headers={"Origin": "https://app.example.com"})
            assert response.headers.get("access-control-allow-origin") == "https://app.example.com"
            # Credentials must never be enabled alongside an origin allow list.
            assert response.headers.get("access-control-allow-credentials", "false").lower() != "true"
        finally:
            os.environ.pop("AGENTIC_SECURITY_CORS_ORIGINS", None)

    def test_no_credentials_header(self):
        """Credentials are never advertised, regardless of origin config."""
        app = FastAPI()

        @app.get("/probe")
        async def probe():
            return {"ok": True}

        setup_cors(app)
        client = TestClient(app)
        response = client.get("/probe", headers={"Origin": "http://evil.example.com"})
        assert response.headers.get("access-control-allow-credentials", "false").lower() != "true"
