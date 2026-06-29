"""Generic Redis caching utility using the shared connection pool."""

import json
import logging
from typing import Any, Callable, Optional

from src.core.redis import get_redis_client

logger = logging.getLogger(__name__)

DEFAULT_TTL = 60  # seconds


def cache_get(key: str) -> Optional[Any]:
    r = get_redis_client()
    if r is None:
        return None
    try:
        raw = r.get(key)
        if raw is not None:
            return json.loads(raw)
    except Exception as e:
        logger.debug("Cache read failed for key %s: %s", key, e)
    return None


def cache_set(key: str, value: Any, ttl: int = DEFAULT_TTL) -> None:
    r = get_redis_client()
    if r is None:
        return
    try:
        r.setex(key, ttl, json.dumps(value))
    except Exception as e:
        logger.debug("Cache write failed for key %s: %s", key, e)


def cache_delete(key: str) -> None:
    r = get_redis_client()
    if r is None:
        return
    try:
        r.delete(key)
    except Exception as e:
        logger.debug("Cache delete failed for key %s: %s", key, e)


def cache_delete_pattern(pattern: str) -> None:
    r = get_redis_client()
    if r is None:
        return
    try:
        cursor = 0
        while True:
            cursor, keys = r.scan(cursor=cursor, match=pattern, count=100)
            if keys:
                r.delete(*keys)
            if cursor == 0:
                break
    except Exception as e:
        logger.debug("Cache pattern delete failed for %s: %s", pattern, e)


async def cache_get_or_compute(
    key: str,
    compute: Callable[[], Any],
    ttl: int = DEFAULT_TTL,
) -> Any:
    cached = cache_get(key)
    if cached is not None:
        return cached
    value = await compute()
    cache_set(key, value, ttl)
    return value
