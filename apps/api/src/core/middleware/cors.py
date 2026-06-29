"""Tenancy-aware CORS configuration using explicit allow-lists."""

import re
from urllib.parse import urlparse

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.config import get_learnhouse_config


_LOCALHOST_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
]

_LOCALHOST_REGEX = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"


def _host_from(value: str) -> str:
    """Extract a bare hostname from a config value that may be a host or URL."""
    value = (value or "").strip().rstrip("/")
    if not value:
        return ""
    host = urlparse(value).hostname if "://" in value else value
    return (host or "").removeprefix("www.").lower()


def _build_allow_origins(config) -> list:
    """Build the explicit CORS allow-list.

    Priority:
      1. ``allowed_origins`` from config (set via config.yaml or
         ``LEARNHOUSE_ALLOWED_ORIGINS`` env var) — exact origins.
      2. In development mode, localhost origins are auto-included.
      3. In single-tenancy mode, the configured frontend/domain is
         added if not already present.
    """
    origins = list(config.hosting_config.allowed_origins or [])

    if config.general_config.development_mode:
        for lo in _LOCALHOST_ORIGINS:
            if lo not in origins:
                origins.append(lo)

    if config.hosting_config.tenancy == "single":
        for cfg_value in (
            config.hosting_config.frontend_domain,
            config.hosting_config.domain,
        ):
            host = _host_from(cfg_value)
            if host and "localhost" not in host:
                for scheme in ("http", "https"):
                    origin = f"{scheme}://{host}"
                    if origin not in origins:
                        # Also add with port 80/443 variants for robustness
                        origins.append(origin)
                        if scheme == "http":
                            origins.append(f"{scheme}://{host}:80")
                        else:
                            origins.append(f"{scheme}://{host}:443")

    return origins


def get_cors_origin_regex() -> str:
    """Build a CORS origin regex from the explicit allow-list.

    Falls back to ``allowed_regexp`` from config only when the explicit
    allow-list is empty and development mode is off.
    """
    config = get_learnhouse_config()
    origins = _build_allow_origins(config)

    if origins:
        escaped = [re.escape(o) for o in sorted(set(origins))]
        return r"^(" + "|".join(escaped) + r")$"

    regex = config.hosting_config.allowed_regexp
    if regex:
        return regex

    return _LOCALHOST_REGEX


def configure_cors(app: FastAPI) -> None:
    """Register CORS middleware on ``app`` with explicit origin allow-list."""
    origins = _build_allow_origins(get_learnhouse_config())
    origin_regex = get_cors_origin_regex()

    if origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            allow_credentials=True,
            allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        )
    else:
        app.add_middleware(
            CORSMiddleware,
            allow_origin_regex=origin_regex,
            allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            allow_credentials=True,
            allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        )
