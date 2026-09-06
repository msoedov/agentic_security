"""Unit tests for CORS middleware configuration.

Verifies that the wildcard-origins + allow_credentials=True spec violation
(CORS spec §3.2, Fetch §4.7) has been removed.  Browsers silently strip
credentials when the response carries Access-Control-Allow-Origin: * paired
with Access-Control-Allow-Credentials: true, so the old config was both
broken and misleading.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

from agentic_security.middleware.cors import setup_cors


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

    def test_wildcard_origins_without_credentials(self):
        """allow_origins=['*'] must not be paired with allow_credentials=True.

        The combination is forbidden by the CORS spec and causes browsers to
        silently drop credentials on every cross-origin request.
        """
        app = FastAPI()
        setup_cors(app)
        opts = _get_cors_options(app)
        allow_origins = opts.get("allow_origins", [])
        allow_credentials = opts.get("allow_credentials", False)

        if "*" in allow_origins or allow_origins == ["*"]:
            assert not allow_credentials, (
                "allow_origins=['*'] with allow_credentials=True is invalid per "
                "the CORS spec — browsers reject it and credentials are silently dropped"
            )

    def test_cors_allows_cross_origin_requests(self):
        """Cross-origin preflight requests return a 200 with CORS headers."""
        app = FastAPI()

        @app.get("/probe")
        async def probe():
            return {"ok": True}

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
        assert "access-control-allow-origin" in response.headers

    def test_cors_no_credentials_header_with_wildcard(self):
        """With wildcard origins, the response must not include
        Access-Control-Allow-Credentials: true."""
        app = FastAPI()

        @app.get("/probe")
        async def probe():
            return {"ok": True}

        setup_cors(app)
        client = TestClient(app)
        response = client.get("/probe", headers={"Origin": "http://evil.example.com"})

        acao = response.headers.get("access-control-allow-origin", "")
        acac = response.headers.get("access-control-allow-credentials", "false")

        if acao == "*":
            assert acac.lower() != "true", (
                "Wildcard ACAO + ACAC:true is a spec violation (RFC 6454 §7.2, "
                "Fetch §4.7) and silently breaks credentialed cross-origin requests"
            )
