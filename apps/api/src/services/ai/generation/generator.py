"""AI course generation orchestrator.

Uses the existing provider-agnostic ``generate()`` function from the ``llm`` layer
(which wraps Pydantic AI). Generation is stateless — no Redis, no sessions.
Each call produces structured output via the ``output_type`` parameter.
"""

from __future__ import annotations

import logging
from typing import Optional

from src.services.ai.generation.schemas import (
    GeneratedCourse,
    GeneratedLesson,
    GeneratedQuiz,
)
from src.services.ai.generation.prompts import (
    build_course_structure_system_prompt,
    build_course_structure_user_prompt,
    build_lesson_content_system_prompt,
    build_lesson_content_user_prompt,
    build_quiz_system_prompt,
    build_quiz_user_prompt,
)
from src.services.ai.llm import generate

logger = logging.getLogger(__name__)


async def generate_course_structure(
    *,
    topic: str,
    model_name: str,
    language: str = "en",
) -> GeneratedCourse:
    """Generate a full course outline (modules, lessons, descriptions) from a topic.

    Uses ``output_type=GeneratedCourse`` for structured output.
    """
    system_prompt = build_course_structure_system_prompt(language)
    user_prompt = build_course_structure_user_prompt(topic, language)

    result = await generate(
        model_name=model_name,
        user_prompt=user_prompt,
        system_prompt=system_prompt,
        output_type=GeneratedCourse,
        temperature=0.7,
        max_tokens=4096,
    )
    return result


async def generate_lesson_content(
    *,
    lesson_title: str,
    lesson_description: str,
    module_title: str,
    course_title: str,
    model_name: str,
    language: str = "en",
    include_quiz: bool = False,
) -> dict:
    """Generate ProseMirror JSON content for a single lesson.

    Returns a ``dict`` (ProseMirror ``doc`` node) suitable for storing as
    ``Activity.content``.
    """
    system_prompt = build_lesson_content_system_prompt(language)
    user_prompt = build_lesson_content_user_prompt(
        lesson_title=lesson_title,
        lesson_description=lesson_description,
        module_title=module_title,
        course_title=course_title,
        include_quiz=include_quiz,
        language=language,
    )

    result = await generate(
        model_name=model_name,
        user_prompt=user_prompt,
        system_prompt=system_prompt,
        output_type=dict,
        temperature=0.7,
        max_tokens=8192,
    )
    return result


async def generate_quiz(
    *,
    lesson_title: str,
    lesson_description: str,
    module_title: str,
    course_title: str,
    model_name: str,
    language: str = "en",
    num_questions: int = 5,
) -> GeneratedQuiz:
    """Generate a quiz for a specific lesson.

    Returns a ``GeneratedQuiz`` with questions and answers.
    """
    system_prompt = build_quiz_system_prompt(language)
    user_prompt = build_quiz_user_prompt(
        lesson_title=lesson_title,
        lesson_description=lesson_description,
        module_title=module_title,
        course_title=course_title,
        num_questions=num_questions,
        language=language,
    )

    result = await generate(
        model_name=model_name,
        user_prompt=user_prompt,
        system_prompt=system_prompt,
        output_type=GeneratedQuiz,
        temperature=0.7,
        max_tokens=4096,
    )
    return result
