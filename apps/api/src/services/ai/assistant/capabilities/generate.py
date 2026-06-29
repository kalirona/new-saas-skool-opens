"""Generate capability — draft posts, replies, and announcements."""

from __future__ import annotations

import logging

from src.services.ai.assistant.prompts import build_generate_system_prompt, build_generate_user_prompt
from src.services.ai.assistant.schemas import GenerateRequest, GenerateResponse
from src.services.ai.llm import generate

logger = logging.getLogger(__name__)


async def generate_content(req: GenerateRequest, model_name: str, language: str = "en") -> GenerateResponse:
    """Draft community content (posts, replies, announcements, discussion prompts)."""
    system_prompt = build_generate_system_prompt(language)
    user_prompt = build_generate_user_prompt(
        content_type=req.content_type.value,
        topic=req.topic,
        tone=req.tone.value,
        context=req.context,
        max_length=req.max_length,
    )

    result = await generate(
        model_name=model_name,
        user_prompt=user_prompt,
        system_prompt=system_prompt,
        output_type=GenerateResponse,
        temperature=0.7,
        max_tokens=2048,
    )
    return result
