"""Background job monitoring.

Provides a context manager and decorator for tracking background task
execution in Sentry. Wraps any async or sync background job with:
  - Sentry transaction/span for observability
  - Duration tracking and structured logging
  - Error capture to Sentry

Usage:
    from src.services.monitoring.background_jobs import monitor_background_job

    async def send_email(user_id: int):
        with monitor_background_job("send_email", {"user_id": user_id}):
            ...  # the actual work

    # Or as a decorator:
    @monitor_background_job("send_email")
    async def send_email(user_id: int):
        ...
"""

import asyncio
import functools
import logging
import time
from contextlib import contextmanager
from typing import Any, Optional

logger = logging.getLogger("learnhouse.background_jobs")


@contextmanager
def monitor_background_job(
    job_name: str,
    metadata: Optional[dict[str, Any]] = None,
    capture_errors: bool = True,
):
    """Context manager that wraps a background job with monitoring.

    Args:
        job_name: Human-readable name for the job (e.g. "send_email", "backup_db")
        metadata: Extra context to attach to the span/log (e.g. {"user_id": 42})
        capture_errors: If True, exceptions are captured to Sentry (but re-raised)

    Yields:
        None — the caller runs the actual job inside the with block

    Raises:
        Any exception raised by the wrapped code is re-raised after logging.
    """
    start = time.monotonic()
    metadata = metadata or {}
    request_id = metadata.pop("request_id", "bg")

    try:
        import sentry_sdk
        sentry_available = True
    except ImportError:
        sentry_available = False

    sentry_transaction = None
    if sentry_available:
        sentry_transaction = sentry_sdk.start_transaction(
            op="background_job",
            name=job_name,
        )

    try:
        yield
    except Exception as exc:
        duration_ms = (time.monotonic() - start) * 1000
        logger.error(
            "Background job '%s' failed after %.0fms: %s [req=%s]",
            job_name, duration_ms, exc, request_id,
        )
        if sentry_available and capture_errors:
            with sentry_sdk.new_scope() as scope:
                scope.set_tag("job_name", job_name)
                scope.set_extra("duration_ms", duration_ms)
                scope.set_extra("metadata", metadata)
                sentry_sdk.capture_exception(exc)
        raise
    else:
        duration_ms = (time.monotonic() - start) * 1000
        logger.info(
            "Background job '%s' completed in %.0fms [req=%s]",
            job_name, duration_ms, request_id,
        )
    finally:
        if sentry_transaction is not None:
            sentry_transaction.finish()


def monitor_job(job_name: Optional[str] = None, capture_errors: bool = True):
    """Decorator version of monitor_background_job.

    Usage:
        @monitor_job("send_welcome_email")
        async def send_welcome_email(user_email: str):
            ...
    """
    def decorator(func):
        actual_name = job_name or func.__name__

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            meta = {"args": str(args)[:200], "kwargs": str(kwargs)[:200]}
            with monitor_background_job(actual_name, meta, capture_errors):
                return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            meta = {"args": str(args)[:200], "kwargs": str(kwargs)[:200]}
            with monitor_background_job(actual_name, meta, capture_errors):
                return func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
