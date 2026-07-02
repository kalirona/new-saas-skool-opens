"""Slow query logging for SQLAlchemy.

Attaches a listener to the SQLAlchemy engine that logs queries exceeding
a configurable threshold. Helps identify N+1 patterns and inefficient
queries before they reach production at scale.

Configure via:
  LEARNHOUSE_SLOW_QUERY_THRESHOLD_MS — threshold in ms (default 500)
"""

import logging
import os
import time

from sqlalchemy import event
from sqlalchemy.engine import Engine

logger = logging.getLogger("learnhouse.slow_queries")


def _get_threshold_ms() -> float:
    raw = os.environ.get("LEARNHOUSE_SLOW_QUERY_THRESHOLD_MS", "500")
    try:
        return float(raw)
    except ValueError:
        return 500.0


def install_slow_query_logging(engine: Engine) -> None:
    """Attach before/after execute listeners to the given SQLAlchemy engine."""
    threshold_ms = _get_threshold_ms()
    logger.info("Slow query threshold: %.0fms", threshold_ms)

    @event.listens_for(engine, "before_execute")
    def before_execute(conn, clause, multiparams, params, execution_context=None):
        conn._slow_query_start = time.monotonic()
        conn._slow_query_statement = str(clause)[:2000]

    @event.listens_for(engine, "after_execute")
    def after_execute(conn, clause, multiparams, params, result, execution_context=None):
        start = getattr(conn, "_slow_query_start", None)
        if start is None:
            return
        duration_ms = (time.monotonic() - start) * 1000
        if duration_ms > threshold_ms:
            statement = getattr(conn, "_slow_query_statement", str(clause)[:2000])
            logger.warning(
                "Slow query (%.0fms): %s",
                duration_ms,
                statement,
            )
