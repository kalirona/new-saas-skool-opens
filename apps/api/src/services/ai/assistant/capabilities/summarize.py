"""Summarize capability — condense discussions, threads, and posts."""

from __future__ import annotations

import logging

from src.services.ai.assistant.prompts import build_summarize_system_prompt, build_summarize_user_prompt
from src.services.ai.assistant.schemas import SummarizeRequest, SummarizeResponse
from src.services.ai.llm import generate

logger = logging.getLogger(__name__)


async def summarize_content(req: SummarizeRequest, model_name: str, language: str = "en") -> SummarizeResponse:
    """Generate a concise summary with optional key bullet points."""
    system_prompt = build_summarize_system_prompt(language)
    user_prompt = build_summarize_user_prompt(
        content=req.content,
        summary_type=req.summary_type.value,
        max_length=req.max_length,
        include_key_points=req.include_key_points,
    )

    gen_result = await generate(
        model_name=model_name,
        user_prompt=user_prompt,
        system_prompt=system_prompt,
        output_type=SummarizeResponse,
        temperature=0.3,
        max_tokens=2048,
    )
    return gen_result.output
