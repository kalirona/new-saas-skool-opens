from __future__ import annotations

import logging
from typing import Any, AsyncGenerator, Optional

from pydantic import BaseModel, Field

from src.services.ai.studio.generation_service import AIGenerationService

logger = logging.getLogger(__name__)


class GeneratedSpace(BaseModel):
    name: str = Field(description="Space name")
    description: str = Field(description="What this space is for")
    icon: Optional[str] = Field(default=None, description="Emoji icon for the space")


class GeneratedCommunity(BaseModel):
    name: str = Field(description="Community name")
    description: str = Field(description="Community description / elevator pitch")
    community_type: str = Field(
        default="open",
        description="Type: open, paid, invite_only, or hidden",
    )
    rules: list[str] = Field(
        description="Community rules / guidelines",
    )
    welcome_post_title: str = Field(
        description="Title for a welcome/introduction post",
    )
    welcome_post_content: str = Field(
        description="Content for a welcome/introduction post",
    )
    suggested_spaces: list[GeneratedSpace] = Field(
        description="Suggested spaces/channels for the community",
    )
    suggested_tags: list[str] = Field(
        description="Suggested tags for organizing content",
    )
    suggested_categories: list[str] = Field(
        description="Suggested categories for resources and discussions",
    )
    target_audience: str = Field(
        description="Description of the target audience",
    )
    moderation_tips: list[str] = Field(
        description="Tips for moderating this community",
    )


SYSTEM_PROMPT = (
    "You are an expert community builder and strategist. "
    "Design a complete, engaging online community from scratch. "
    "Include clear rules, a welcoming introduction post, suggested spaces, "
    "and organizational tags/categories. Output MUST be valid JSON."
)


def _build_user_prompt(
    topic: str,
    language: str = "en",
    num_spaces: int = 5,
) -> str:
    return (
        f"Design a thriving online community for: {topic}\n\n"
        f"Generate the response in {language}.\n"
        f"Include {num_spaces} suggested spaces/channels.\n"
        f"The community should have 5-8 clear rules.\n"
        f"Suggest 5-10 tags and 3-6 categories for organizing content.\n"
        f"Write a complete welcome post that introduces new members to the community.\n\n"
        f"Return ONLY valid JSON matching the GeneratedCommunity schema."
    )


class CommunityGenerator:
    def __init__(self, ai_service: AIGenerationService):
        self._ai = ai_service

    async def generate(
        self,
        topic: str,
        language: str = "en",
        num_spaces: int = 5,
        model_name: Optional[str] = None,
    ) -> GeneratedCommunity:
        user_prompt = _build_user_prompt(topic, language, num_spaces)

        result = await self._ai.generate(
            user_prompt=user_prompt,
            system_prompt=SYSTEM_PROMPT,
            temperature=0.7,
            max_tokens=8192,
            model_name=model_name,
            output_type=GeneratedCommunity,
        )

        course = result.content
        if isinstance(course, dict):
            course = GeneratedCommunity(**course)

        return course

    async def generate_stream(
        self,
        topic: str,
        language: str = "en",
        num_spaces: int = 5,
        model_name: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        user_prompt = _build_user_prompt(topic, language, num_spaces)
        async for chunk in self._ai.generate_stream(
            user_prompt=user_prompt,
            system_prompt=SYSTEM_PROMPT,
            temperature=0.7,
            max_tokens=8192,
            model_name=model_name,
        ):
            yield chunk
