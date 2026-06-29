"""Security headers middleware (HSTS, XFO, CSP, etc.)."""

import os

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from config.config import get_learnhouse_config


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        learnhouse_config = get_learnhouse_config()
        hosting = learnhouse_config.hosting_config

        if hosting.ssl:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

        csp = hosting.csp_header
        if not csp:
            csp = os.environ.get("LEARNHOUSE_CSP_HEADER", "")
        if csp:
            response.headers["Content-Security-Policy"] = csp

        return response
