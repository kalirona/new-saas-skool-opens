"""Capability registry for the AI assistant.

Each capability is a callable that takes (request, model_name) and returns a response.
"""

from __future__ import annotations

from typing import Awaitable, Callable

from src.services.ai.assistant.schemas import (
    AssistantCapability,
    QARequest,
    QAResponse,
    SummarizeRequest,
    SummarizeResponse,
    GenerateRequest,
    GenerateResponse,
    ModerateRequest,
    ModerateResponse,
)

# Type alias for any capability handler
CapabilityHandler = Callable[..., Awaitable[object]]


async def handle_qa(req: QARequest, model_name: str, language: str = "en") -> QAResponse:
    from src.services.ai.assistant.capabilities.qa import answer_question
    return await answer_question(req, model_name, language)


async def handle_summarize(req: SummarizeRequest, model_name: str, language: str = "en") -> SummarizeResponse:
    from src.services.ai.assistant.capabilities.summarize import summarize_content
    return await summarize_content(req, model_name, language)


async def handle_generate(req: GenerateRequest, model_name: str, language: str = "en") -> GenerateResponse:
    from src.services.ai.assistant.capabilities.generate import generate_content
    return await generate_content(req, model_name, language)


async def handle_moderate(req: ModerateRequest, model_name: str, language: str = "en") -> ModerateResponse:
    from src.services.ai.assistant.capabilities.moderate import moderate_content
    return await moderate_content(req, model_name, language)


CAPABILITY_ROUTER: dict[AssistantCapability, CapabilityHandler] = {
    "qa": handle_qa,
    "summarize": handle_summarize,
    "generate": handle_generate,
    "moderate": handle_moderate,
}
