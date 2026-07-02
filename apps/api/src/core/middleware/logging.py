"""Structured JSON logging middleware.

Replaces plain-text log lines with JSON-formatted records when
LEARNHOUSE_LOG_FORMAT=json (the production default). Each line
includes timestamp, level, request_id, method, path, status, duration,
and service name — ready for ingestion by Loki, DataDog, or any
JSON-aware log aggregator.
"""

import json
import logging
import os
import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


def _should_use_json() -> bool:
    fmt = os.environ.get("LEARNHOUSE_LOG_FORMAT", "json").lower()
    return fmt == "json"


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """Log every request as a single JSON line with structured fields."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self.use_json = _should_use_json()

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start = time.monotonic()
        response = await call_next(request)
        duration_ms = (time.monotonic() - start) * 1000

        request_id = getattr(request.state, "request_id", "unknown")

        if self.use_json:
            record = {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()),
                "level": "WARN" if duration_ms > 1000 else "INFO",
                "logger": "learnhouse.api",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query": str(request.url.query) if request.url.query else "",
                "status": response.status_code,
                "duration_ms": round(duration_ms, 2),
                "service": "api",
            }
            line = json.dumps(record, ensure_ascii=False)
            if duration_ms > 1000:
                logger.warning("%s", line)
            else:
                logger.info("%s", line)
        else:
            log_fn = logger.warning if duration_ms > 1000 else logger.info
            log_fn(
                "%s %s -> %s (%.1fms) [req=%s]",
                request.method,
                request.url.path,
                response.status_code,
                duration_ms,
                request_id,
            )

        return response
