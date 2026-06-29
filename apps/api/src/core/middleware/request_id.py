"""Request ID middleware — generates and propagates X-Request-ID."""

import logging
from uuid import uuid4

from starlette.datastructures import MutableHeaders
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = uuid4().hex[:16]

        request.state.request_id = request_id

        response = await call_next(request)

        MutableHeaders(response.headers)["X-Request-ID"] = request_id

        return response
