"""Request timing middleware — logs request duration and method/path."""

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class RequestTimingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, slow_threshold_ms: float = 1000.0) -> None:
        super().__init__(app)
        self.slow_threshold_ms = slow_threshold_ms

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start = time.monotonic()

        response = await call_next(request)

        duration_ms = (time.monotonic() - start) * 1000
        request_id = getattr(request.state, "request_id", "unknown")

        log_fn = logger.warning if duration_ms > self.slow_threshold_ms else logger.info
        log_fn(
            "%s %s -> %s (%.1fms) [req=%s]",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            request_id,
        )

        return response
