from __future__ import annotations

import json
import logging
from typing import Any, AsyncGenerator, Optional

logger = logging.getLogger(__name__)


class StreamEvent:
    def __init__(self, event_type: str, data: Any):
        self.event_type = event_type
        self.data = data

    def to_sse(self) -> str:
        return f"event: {self.event_type}\ndata: {json.dumps(self.data)}\n\n"


class StreamingManager:
    @staticmethod
    async def wrap_stream(
        stream: AsyncGenerator[str, None],
        event_type: str = "chunk",
        done_event: str = "done",
        error_event: str = "error",
    ) -> AsyncGenerator[str, None]:
        try:
            async for chunk in stream:
                event = StreamEvent(event_type, {"content": chunk})
                yield event.to_sse()
            event = StreamEvent(done_event, {"status": "complete"})
            yield event.to_sse()
        except Exception as e:
            logger.exception("Streaming error")
            event = StreamEvent(error_event, {"error": str(e)})
            yield event.to_sse()

    @staticmethod
    def structured_event(event: str, data: dict) -> str:
        return StreamEvent(event, data).to_sse()
