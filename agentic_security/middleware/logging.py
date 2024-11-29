from fastapi import Request
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware


class LogNon200ResponsesMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
        except Exception as e:
            logger.exception("Yikes")
            raise e
        if response.status_code != 200:
            logger.error(
                f"{request.method} {request.url} - Status code: {response.status_code}"
            )
        return response
