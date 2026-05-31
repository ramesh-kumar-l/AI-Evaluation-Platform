"""Sliding-window rate limiter middleware.

Active only when ``AEP_API_AUTH_ENABLED=true``. Each API key (or IP for unauthenticated
requests) is limited to ``AEP_RATE_LIMIT_PER_MINUTE`` requests per 60-second window.
Uses an in-process deque — no Redis required for offline-first deployments.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.core.config import get_settings

# shared across requests within the process lifetime
_windows: dict[str, deque[float]] = defaultdict(deque)

_PASS_THROUGH_PATHS = {"/health", "/ready"}


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        settings = get_settings()
        if not settings.api_auth_enabled:
            return await call_next(request)

        if request.url.path in _PASS_THROUGH_PATHS:
            return await call_next(request)

        bucket = (
            request.headers.get("x-api-key")
            or (request.client.host if request.client else "anon")
        )
        window = _windows[bucket]
        now = time.monotonic()
        limit = settings.rate_limit_per_minute

        while window and now - window[0] > 60.0:
            window.popleft()

        if len(window) >= limit:
            return Response(
                content='{"detail":"Rate limit exceeded — try again later"}',
                status_code=429,
                media_type="application/json",
                headers={"Retry-After": "60"},
            )

        window.append(now)
        return await call_next(request)
