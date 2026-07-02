"""Q&A capability — answer member questions based on discussion/course context."""

from __future__ import annotations

import logging

from src.services.ai.assistant.prompts import build_qa_system_prompt, build_qa_user_prompt
from src.services.ai.assistant.schemas import QARequest, QAResponse
from src.services.ai.llm import generate

logger = logging.getLogger(__name__)


async def answer_question(req: QARequest, model_name: str, language: str = "en") -> QAResponse:
    """Generate an answer to a member's question given optional context."""
    system_prompt = build_qa_system_prompt(language)
    user_prompt = build_qa_user_prompt(
        question=req.question,
        discussion_context=req.discussion_context,
        course_context=req.course_context,
    )

    gen_result = await generate(
        model_name=model_name,
        user_prompt=user_prompt,
        system_prompt=system_prompt,
        output_type=QAResponse,
        temperature=0.3,
        max_tokens=1024,
    )
    return gen_result.output
