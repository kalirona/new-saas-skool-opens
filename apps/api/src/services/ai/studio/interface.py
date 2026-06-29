from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, Optional

logger = logging.getLogger(__name__)


@dataclass
class GenerationRequest:
    user_prompt: str
    system_prompt: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4096
    model_name: Optional[str] = None
    output_type: type = str
    conversation_history: Optional[list[dict]] = None


@dataclass
class GenerationResult:
    content: Any
    model_name: str
    provider: str
    usage: dict = field(default_factory=dict)


@dataclass
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class AIProvider(ABC):
    provider_name: str = ""

    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}

    @abstractmethod
    async def generate(self, request: GenerationRequest) -> GenerationResult:
        ...

    @abstractmethod
    async def generate_stream(
        self, request: GenerationRequest
    ) -> AsyncGenerator[str, None]:
        ...

    @abstractmethod
    async def count_tokens(self, text: str) -> int:
        ...

    def get_usage(self) -> TokenUsage:
        return TokenUsage()
