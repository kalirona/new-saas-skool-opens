import json
import pytest
from typing import AsyncGenerator
from src.services.ai.studio.streaming import StreamEvent, StreamingManager


class TestStreamEvent:
    def test_to_sse_format(self):
        event = StreamEvent("chunk", {"content": "Hello"})
        sse = event.to_sse()
        assert sse.startswith("event: chunk")
        assert 'data: {"content": "Hello"}' in sse
        assert sse.endswith("\n\n")

    def test_to_sse_with_different_types(self):
        event = StreamEvent("error", {"error": "Something went wrong"})
        sse = event.to_sse()
        assert "event: error" in sse

    def test_sse_double_newline_terminator(self):
        event = StreamEvent("done", {"status": "complete"})
        sse = event.to_sse()
        assert sse.endswith("\n\n")


class TestStreamingManagerWrapStream:
    @pytest.mark.asyncio
    async def test_wraps_successful_stream(self):
        async def fake_stream():
            yield "Hello "
            yield "World"

        manager = StreamingManager()
        chunks = []
        async for chunk in manager.wrap_stream(fake_stream()):
            chunks.append(chunk)

        assert len(chunks) == 3
        first = json.loads(chunks[0].split("data: ")[1].strip())
        assert first == {"content": "Hello "}
        second = json.loads(chunks[1].split("data: ")[1].strip())
        assert second == {"content": "World"}
        done = json.loads(chunks[2].split("data: ")[1].strip())
        assert done == {"status": "complete"}

    @pytest.mark.asyncio
    async def test_wraps_stream_with_error(self):
        async def failing_stream():
            yield "Before error"
            raise ValueError("Test error")

        manager = StreamingManager()
        chunks = []
        async for chunk in manager.wrap_stream(failing_stream()):
            chunks.append(chunk)

        assert len(chunks) == 2
        first = json.loads(chunks[0].split("data: ")[1].strip())
        assert first["content"] == "Before error"
        error = json.loads(chunks[1].split("data: ")[1].strip())
        assert "error" in error
        assert "Test error" in error["error"]

    @pytest.mark.asyncio
    async def test_empty_stream(self):
        async def empty_stream():
            return
            yield

        manager = StreamingManager()
        chunks = []
        async for chunk in manager.wrap_stream(empty_stream()):
            chunks.append(chunk)

        assert len(chunks) == 1
        done = json.loads(chunks[0].split("data: ")[1].strip())
        assert done["status"] == "complete"

    @pytest.mark.asyncio
    async def test_custom_event_types(self):
        async def fake_stream():
            yield "data"

        manager = StreamingManager()
        chunks = []
        async for chunk in manager.wrap_stream(fake_stream(), event_type="token", done_event="finish", error_event="fail"):
            chunks.append(chunk)

        assert "event: token" in chunks[0]
        assert "event: finish" in chunks[1]

    @pytest.mark.asyncio
    async def test_stream_with_multiple_chunks(self):
        async def long_stream():
            for i in range(5):
                yield str(i)

        manager = StreamingManager()
        count = 0
        async for _ in manager.wrap_stream(long_stream()):
            count += 1
        assert count == 6


class TestStreamingManagerStructuredEvent:
    def test_structured_event_format(self):
        result = StreamingManager.structured_event("status", {"progress": 50})
        assert "event: status" in result
        assert '{"progress": 50}' in result

    def test_structured_event_with_nested_data(self):
        result = StreamingManager.structured_event("metrics", {"tokens": 100, "cost": 0.002})
        assert "event: metrics" in result
        assert "tokens" in result
        assert "cost" in result
