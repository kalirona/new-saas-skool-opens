from __future__ import annotations

import asyncio
import logging
from typing import Any, Awaitable, Callable, Optional, TypeVar

T = TypeVar("T")

logger = logging.getLogger(__name__)


class RetryHandler:
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        backoff_factor: float = 2.0,
        retryable_exceptions: Optional[tuple[type[Exception], ...]] = None,
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.retryable_exceptions = retryable_exceptions or (Exception,)

    async def execute(
        self,
        fn: Callable[..., Awaitable[T]],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        last_exception = None
        for attempt in range(self.max_retries + 1):
            try:
                return await fn(*args, **kwargs)
            except self.retryable_exceptions as e:
                last_exception = e
                if attempt < self.max_retries:
                    delay = min(
                        self.base_delay * (self.backoff_factor**attempt),
                        self.max_delay,
                    )
                    logger.warning(
                        "Retry attempt %d/%d for %s after %.1fs: %s",
                        attempt + 1,
                        self.max_retries,
                        fn.__name__,
                        delay,
                        e,
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        "All %d retries exhausted for %s: %s",
                        self.max_retries,
                        fn.__name__,
                        e,
                    )

        raise last_exception  # type: ignore[misc]
