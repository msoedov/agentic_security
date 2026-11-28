"""Block cross-origin browser calls to state-changing scan endpoints.

CORS alone does not stop simple POST requests (/stop, /scan-csv). This middleware
allows same-origin and explicitly allowlisted origins; non-browser clients without
an Origin header continue to work unchanged.
"""

from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from agentic_security.middleware.cors import get_cors_allow_origins

GUARDED_ROUTES: frozenset[tuple[str, str]] = frozenset(
    {
        ("/stop", "POST"),
        ("/scan-csv", "POST"),
        ("/verify", "POST"),
        ("/scan", "POST"),
    }
)


def _request_origin(request: Request) -> str | None:
    origin = request.headers.get("origin")
    if origin:
        return origin.rstrip("/")
    return None


def _same_origin(request: Request, origin: str) -> bool:
    host = request.headers.get("host")
    if not host:
        return False
    scheme = request.url.scheme
    return origin.rstrip("/") == f"{scheme}://{host}".rstrip("/")


class OriginGuardMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        route = (request.url.path, request.method.upper())
        if route not in GUARDED_ROUTES:
            return await call_next(request)

        origin = _request_origin(request)
        if origin is None:
            return await call_next(request)

        if _same_origin(request, origin):
            return await call_next(request)

        allowed_origins = {allowed.rstrip("/") for allowed in get_cors_allow_origins()}
        if origin.rstrip("/") in allowed_origins:
            return await call_next(request)

        return JSONResponse(status_code=403, content={"detail": "Origin not allowed"})
