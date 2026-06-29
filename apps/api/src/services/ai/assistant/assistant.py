"""AI assistant orchestrator.

Routes requests to the correct capability handler based on ``capability`` field.
All generation goes through the existing ``llm.generate()`` for provider abstraction.
Stateless — no Redis, no sessions.
"""

from __future__ import annotations

import logging

from src.services.ai.assistant.capabilities import CAPABILITY_ROUTER
from src.services.ai.assistant.schemas import (
    AssistantRequest,
    AssistantResponse,
    QARequest,
    SummarizeRequest,
    GenerateRequest,
    ModerateRequest,
)

logger = logging.getLogger(__name__)


async def run_assistant(req: AssistantRequest, model_name: str) -> AssistantResponse:
    """Dispatch to the correct capability and return the response."""
    handler = CAPABILITY_ROUTER.get(req.capability)
    if handler is None:
        raise ValueError(f"Unknown capability: {req.capability}")

    sub_req: QARequest | SummarizeRequest | GenerateRequest | ModerateRequest | None = None
    if req.capability == "qa":
        sub_req = req.qa
    elif req.capability == "summarize":
        sub_req = req.summarize
    elif req.capability == "generate":
        sub_req = req.generate
    elif req.capability == "moderate":
        sub_req = req.moderate

    if sub_req is None:
        raise ValueError(f"Request body missing for capability: {req.capability}")

    result = await handler(sub_req, model_name, req.language)

    response_kwargs = {"capability": req.capability, "credits_used": 1}
    if req.capability == "qa":
        response_kwargs["qa"] = result
    elif req.capability == "summarize":
        response_kwargs["summarize"] = result
    elif req.capability == "generate":
        response_kwargs["generate"] = result
    elif req.capability == "moderate":
        response_kwargs["moderate"] = result

    return AssistantResponse(**response_kwargs)
