import pytest
from unittest.mock import AsyncMock
from src.services.ai.studio.retry_handler import RetryHandler


class TestRetryHandler:
    @pytest.fixture
    def handler(self):
        return RetryHandler(max_retries=2, base_delay=0.01, max_delay=0.1)

    @pytest.mark.asyncio
    async def test_success_on_first_try(self, handler):
        fn = AsyncMock(return_value="success")
        result = await handler.execute(fn)
        assert result == "success"
        fn.assert_called_once()

    @pytest.mark.asyncio
    async def test_retries_on_failure_then_succeeds(self, handler):
        fn = AsyncMock(side_effect=[ValueError("fail"), "success"])
        result = await handler.execute(fn)
        assert result == "success"
        assert fn.call_count == 2

    @pytest.mark.asyncio
    async def test_exhausts_retries_and_raises(self, handler):
        fn = AsyncMock(side_effect=ValueError("persistent"))
        with pytest.raises(ValueError, match="persistent"):
            await handler.execute(fn)
        assert fn.call_count == 3

    @pytest.mark.asyncio
    async def test_only_retries_specified_exceptions(self):
        handler = RetryHandler(
            max_retries=1, base_delay=0.01,
            retryable_exceptions=(ValueError,),
        )
        fn = AsyncMock(side_effect=TypeError("non-retryable"))
        with pytest.raises(TypeError, match="non-retryable"):
            await handler.execute(fn)
        fn.assert_called_once()

    @pytest.mark.asyncio
    async def test_respects_max_retries_zero(self):
        handler = RetryHandler(max_retries=0)
        fn = AsyncMock(side_effect=ValueError("fail"))
        with pytest.raises(ValueError):
            await handler.execute(fn)
        fn.assert_called_once()

    @pytest.mark.asyncio
    async def test_raises_last_exception_type(self, handler):
        fn = AsyncMock(side_effect=[RuntimeError("first"), RuntimeError("second"), RuntimeError("third")])
        with pytest.raises(RuntimeError, match="third"):
            await handler.execute(fn)

    @pytest.mark.asyncio
    async def test_passes_args_and_kwargs(self, handler):
        fn = AsyncMock(return_value="ok")
        result = await handler.execute(fn, "arg1", key="val")
        assert result == "ok"
        fn.assert_called_once_with("arg1", key="val")

    @pytest.mark.asyncio
    async def test_backoff_delay_increases(self, handler):
        fn = AsyncMock(side_effect=[ValueError("1"), ValueError("2"), "success"])
        result = await handler.execute(fn)
        assert result == "success"
