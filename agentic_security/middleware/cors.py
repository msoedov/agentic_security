import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agentic_security.config import settings_var

logger = logging.getLogger(__name__)


def get_cors_allow_origins() -> list[str]:
    """Return configured browser origins allowed to call the local scanner API."""
    env_val = os.getenv("AGENTIC_SECURITY_CORS_ORIGINS")
    if env_val is not None:
        origins = [origin.strip() for origin in env_val.split(",") if origin.strip()]
    else:
        configured = settings_var("server.cors_allow_origins", [])
        origins = list(configured) if configured else []

    if "*" in origins:
        logger.warning(
            "server.cors_allow_origins includes '*' — any web origin can drive "
            "unauthenticated /scan and /verify against the local scanner"
        )
    return origins


def setup_cors(app: FastAPI) -> None:
    origins = get_cors_allow_origins()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
