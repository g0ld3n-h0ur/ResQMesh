"""
app/middleware/rate_limit.py

Lightweight in-memory rate limiter for a small set of abuse-prone public
endpoints (login, public SOS submission). Not distributed/production-grade —
counters live in process memory and reset on restart — but enough to stop
naive brute-force/flood scripts during a demo.
"""

import time
from collections import defaultdict, deque

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

# path -> (max requests, window in seconds)
_LIMITED_PATHS: dict[str, tuple[int, int]] = {
    "/api/v1/auth/login": (10, 60),
    "/api/v1/reports/emergency": (5, 60),
}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Fixed-window per-IP rate limit on a small allowlist of routes."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self._hits: dict[tuple[str, str], deque] = defaultdict(deque)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        limit = _LIMITED_PATHS.get(request.url.path)
        if limit is None:
            return await call_next(request)

        max_requests, window_seconds = limit
        client_ip = request.client.host if request.client else "unknown"
        key = (client_ip, request.url.path)

        now = time.monotonic()
        hits = self._hits[key]
        while hits and now - hits[0] > window_seconds:
            hits.popleft()

        if len(hits) >= max_requests:
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "message": "Too many requests. Please slow down and try again shortly.",
                    "data": None,
                },
            )

        hits.append(now)
        return await call_next(request)
