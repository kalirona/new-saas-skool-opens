import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Optional
from uuid import uuid4

from src.core.cache import cache_get, cache_set
from src.core.redis import get_redis_client

logger = logging.getLogger(__name__)

# Shared executor instance used across the application
executor: Optional["BackgroundTaskExecutor"] = None


def get_executor() -> "BackgroundTaskExecutor":
    global executor
    if executor is None:
        executor = BackgroundTaskExecutor()
    return executor


@dataclass
class TaskRetryConfig:
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_factor: float = 2.0


@dataclass
class TaskResult:
    success: bool
    task_id: str
    task_name: str
    error: Optional[str] = None
    attempts: int = 0
    duration_ms: float = 0.0


class DeadLetterStore:
    _prefix = "dlq:"

    @staticmethod
    def push(task_name: str, payload: dict, error: str) -> None:
        entry = {
            "task_name": task_name,
            "payload": payload,
            "error": error[:1000],
            "timestamp": time.time(),
        }
        r = get_redis_client()
        if r is None:
            return
        try:
            key = f"{DeadLetterStore._prefix}{task_name}:{uuid4().hex[:12]}"
            r.setex(key, 86400 * 7, json.dumps(entry))
            r.lpush(f"{DeadLetterStore._prefix}{task_name}", key)
            r.ltrim(f"{DeadLetterStore._prefix}{task_name}", 0, 999)
        except Exception:
            logger.debug("DLQ push failed", exc_info=True)

    @staticmethod
    def pop(task_name: str) -> Optional[dict]:
        r = get_redis_client()
        if r is None:
            return None
        try:
            key = r.rpop(f"{DeadLetterStore._prefix}{task_name}")
            if key:
                raw = r.get(key)
                r.delete(key)
                return json.loads(raw) if raw else None
        except Exception:
            logger.debug("DLQ pop failed", exc_info=True)
        return None


class BackgroundTaskExecutor:
    def __init__(self, max_concurrent: int = 50, shutdown_timeout: float = 30.0):
        self._tasks: set[asyncio.Task] = set()
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._shutdown_timeout = shutdown_timeout
        self._retry_config = TaskRetryConfig()
        self._dlq = DeadLetterStore()

    def _done_callback(self, task: asyncio.Task) -> None:
        self._tasks.discard(task)
        exc = task.exception()
        if exc and not task.cancelled():
            logger.error("Task %s failed: %s", task.get_name(), exc)

    async def run(
        self,
        coro_factory: Callable[[], Awaitable[Any]],
        task_name: str = "unnamed",
        task_id: Optional[str] = None,
        retry_config: Optional[TaskRetryConfig] = None,
        idempotency_key: Optional[str] = None,
        dlq_payload: Optional[dict] = None,
    ) -> asyncio.Task:
        effective_id = task_id or f"{task_name}_{uuid4().hex[:12]}"

        if idempotency_key:
            dedup_key = f"task_dedup:{idempotency_key}"
            if cache_get(dedup_key) is not None:
                logger.debug("Skipping duplicate task (key=%s)", idempotency_key)
                return None
            cache_set(dedup_key, True, ttl=300)

        async def wrapper() -> None:
            cfg = retry_config or self._retry_config
            last_error: Optional[str] = None
            start = time.monotonic()
            for attempt in range(1, cfg.max_attempts + 1):
                try:
                    async with self._semaphore:
                        await coro_factory()
                    elapsed = (time.monotonic() - start) * 1000
                    logger.info(
                        "Task %s completed in %.1fms (attempt %d/%d)",
                        effective_id, elapsed, attempt, cfg.max_attempts,
                    )
                    return
                except Exception as e:
                    last_error = str(e)
                    logger.warning(
                        "Task %s attempt %d/%d failed: %s",
                        effective_id, attempt, cfg.max_attempts, last_error,
                    )
                    if attempt < cfg.max_attempts:
                        delay = min(
                            cfg.base_delay * (cfg.backoff_factor ** (attempt - 1)),
                            cfg.max_delay,
                        )
                        await asyncio.sleep(delay)

            elapsed = (time.monotonic() - start) * 1000
            logger.error(
                "Task %s failed after %d attempts (%.1fms): %s",
                effective_id, cfg.max_attempts, elapsed, last_error,
            )
            if dlq_payload is not None:
                self._dlq.push(task_name, dlq_payload, last_error or "unknown")

        task = asyncio.create_task(wrapper(), name=effective_id)
        self._tasks.add(task)
        task.add_done_callback(self._done_callback)
        return task

    async def shutdown(self) -> None:
        if not self._tasks:
            return
        logger.info("Waiting for %d background tasks to finish...", len(self._tasks))
        pending = list(self._tasks)
        done, pending = await asyncio.wait(
            pending, timeout=self._shutdown_timeout,
        )
        for t in pending:
            t.cancel()
            logger.warning("Cancelled stuck task %s", t.get_name())
        logger.info("Background tasks shut down: %d done, %d cancelled", len(done), len(pending))
