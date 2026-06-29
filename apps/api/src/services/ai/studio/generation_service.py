from __future__ import annotations

import logging
from typing import Any, AsyncGenerator, Optional

from src.services.ai.studio.interface import (
    AIProvider,
    GenerationRequest,
    GenerationResult,
)
from src.services.ai.studio.retry_handler import RetryHandler
from src.services.ai.studio.token_tracker import TokenUsageTracker
from src.services.ai.studio.cost_tracker import CostTracker

logger = logging.getLogger(__name__)


class AIGenerationService:
    def __init__(
        self,
        provider: AIProvider,
        retry_handler: Optional[RetryHandler] = None,
        token_tracker: Optional[TokenUsageTracker] = None,
        cost_tracker: Optional[CostTracker] = None,
    ):
        self._provider = provider
        self._retry = retry_handler or RetryHandler()
        self._token_tracker = token_tracker or TokenUsageTracker()
        self._cost_tracker = cost_tracker or CostTracker()

    @property
    def provider(self) -> AIProvider:
        return self._provider

    @property
    def token_tracker(self) -> TokenUsageTracker:
        return self._token_tracker

    @property
    def cost_tracker(self) -> CostTracker:
        return self._cost_tracker

    async def generate(
        self,
        user_prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        model_name: Optional[str] = None,
        output_type: type = str,
        conversation_history: Optional[list[dict]] = None,
    ) -> GenerationResult:
        request = GenerationRequest(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            model_name=model_name,
            output_type=output_type,
            conversation_history=conversation_history,
        )

        result = await self._retry.execute(self._provider.generate, request)

        if result.usage:
            record = self._token_tracker.record(
                provider=result.provider,
                model_name=result.model_name,
                prompt_tokens=result.usage.get("prompt_tokens", 0),
                completion_tokens=result.usage.get("completion_tokens", 0),
            )
            cost = self._cost_tracker.calculate(record)
            logger.debug(
                "Generation cost: $%.6f | tokens: %d",
                cost,
                record.total_tokens,
            )

        return result

    async def generate_stream(
        self,
        user_prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        model_name: Optional[str] = None,
        conversation_history: Optional[list[dict]] = None,
    ) -> AsyncGenerator[str, None]:
        request = GenerationRequest(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            model_name=model_name,
            conversation_history=conversation_history,
        )

        async for chunk in self._provider.generate_stream(request):
            yield chunk

    def get_usage_summary(self) -> dict:
        return {
            **self._token_tracker.summary(),
            "total_cost": self._cost_tracker.total_cost,
        }
