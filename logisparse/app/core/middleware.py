import time
import uuid
from collections import defaultdict, deque
from collections.abc import Callable

from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.logging import request_id_context


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        token = request_id_context.set(request_id)
        start = time.perf_counter()

        try:
            response = await call_next(request)
        finally:
            request_id_context.reset(token)

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{time.perf_counter() - start:.4f}"
        return response


class InMemoryRateLimitMiddleware(BaseHTTPMiddleware):
    """Small single-process limiter for MVP abuse protection.

    Use a reverse proxy or managed edge limiter once traffic runs across multiple
    API replicas.
    """

    def __init__(self, app) -> None:  # type: ignore[no-untyped-def]
        super().__init__(app)
        self.requests: defaultdict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.url.path in {"/health", "/ready"}:
            return await call_next(request)

        now = time.monotonic()
        client_ip = request.client.host if request.client else "unknown"
        window = self.requests[client_ip]

        while window and now - window[0] > settings.RATE_LIMIT_WINDOW_SECONDS:
            window.popleft()

        if len(window) >= settings.RATE_LIMIT_REQUESTS:
            return Response(
                content='{"detail":"Rate limit exceeded"}',
                media_type="application/json",
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        window.append(now)
        return await call_next(request)
