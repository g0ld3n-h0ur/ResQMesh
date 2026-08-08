"""
app/middleware/logging.py

Structured request / response logging middleware.

Logs every HTTP request with:
  - HTTP method and URL path
  - Response status code
  - Elapsed time in milliseconds
  - Client host IP

Log records are emitted at INFO level so they are visible in all
non-production log configurations without polluting DEBUG output.
"""

import logging
import time

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

logger = logging.getLogger("app.access")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """ASGI middleware that logs structured access log entries for each request."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start_time = time.perf_counter()

        response: Response = await call_next(request)

        elapsed_ms = (time.perf_counter() - start_time) * 1_000

        logger.info(
            "%(method)s %(path)s %(status)s %(elapsed).2fms %(client)s",
            {
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "elapsed": elapsed_ms,
                "client": request.client.host if request.client else "unknown",
            },
        )

        return response
