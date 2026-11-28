import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def _resolve_allowed_origins() -> list[str]:
    """Resolve the list of CORS-allowed origins from the environment.

    The previous behaviour hard-coded ``["*"]``, which exposed the
    unauthenticated ``/scan``, ``/scan-csv``, ``/stop`` and ``/verify``
    endpoints to any web origin (issue #334): a malicious site could drive
    those endpoints from a victim's browser.

    Origins are now opt-in. Set ``AGENTIC_SECURITY_CORS_ORIGINS`` to a
    comma-separated list of trusted origins (e.g. your front-end URL). When
    the variable is unset or empty, no cross-origin origin is allowed, which
    is the safe default for a server-side scanning API.
    """
    raw = os.environ.get("AGENTIC_SECURITY_CORS_ORIGINS", "").strip()
    if not raw:
        return []
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def setup_cors(app: FastAPI):
    origins = _resolve_allowed_origins()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["*"],  # Allows all methods
        allow_headers=["*"],  # Allows all headers
        allow_credentials=False,
    )
