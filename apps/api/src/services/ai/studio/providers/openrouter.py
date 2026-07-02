from __future__ import annotations

import logging
from typing import AsyncGenerator, Optional

from src.services.ai.studio.interface import AIProvider, GenerationRequest, GenerationResult
from src.services.ai.llm import generate, generate_stream

logger = logging.getLogger(__name__)


class OpenRouterProvider(AIProvider):
    provider_name = "openrouter"

    def __init__(self, config: Optional[dict] = None):
        super().__init__(config)
        self._model_name = config.get("model", "openai/gpt-4o-mini") if config else "openai/gpt-4o-mini"

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        model_name = request.model_name or self._model_name
        result = await generate(
            model_name=model_name,
            user_prompt=request.user_prompt,
            system_prompt=request.system_prompt,
            history=request.conversation_history,
            output_type=request.output_type or str,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
        )
        return GenerationResult(
            content=result.output,
            model_name=model_name,
            provider=self.provider_name,
            usage=result.usage,
        )

    async def generate_stream(
        self, request: GenerationRequest
    ) -> AsyncGenerator[str, None]:
        model_name = request.model_name or self._model_name
        async for chunk in generate_stream(
            model_name=model_name,
            user_prompt=request.user_prompt,
            system_prompt=request.system_prompt,
            history=request.conversation_history,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
        ):
            yield chunk

    async def count_tokens(self, text: str) -> int:
        try:
            import tiktoken
            enc = tiktoken.get_encoding("cl100k_base")
            return len(enc.encode(text))
        except ImportError:
            return len(text.split())
