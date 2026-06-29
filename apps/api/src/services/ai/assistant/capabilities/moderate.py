"""Moderate capability — flag toxic, spam, or policy-violating content."""

from __future__ import annotations

import logging

from src.services.ai.assistant.prompts import build_moderate_system_prompt, build_moderate_user_prompt
from src.services.ai.assistant.schemas import ModerateRequest, ModerateResponse, ModerationResult
from src.services.ai.llm import generate

logger = logging.getLogger(__name__)


async def moderate_content(req: ModerateRequest, model_name: str, language: str = "en") -> ModerateResponse:
    """Review content and return per-category moderation results."""
    system_prompt = build_moderate_system_prompt(language)
    user_prompt = build_moderate_user_prompt(
        content=req.content,
        categories=[c.value for c in req.categories],
    )

    result = await generate(
        model_name=model_name,
        user_prompt=user_prompt,
        system_prompt=system_prompt,
        output_type=ModerateResponse,
        temperature=0.1,
        max_tokens=2048,
    )
    return result
