from __future__ import annotations

import logging
from typing import AsyncGenerator, Optional

from pydantic import BaseModel, Field

from src.services.ai.studio.generation_service import AIGenerationService

logger = logging.getLogger(__name__)


class PostContent(BaseModel):
    title: str = Field(description="Post title")
    content: str = Field(description="Main post content / body")
    label: Optional[str] = Field(
        default=None,
        description="Discussion label: general, question, idea, announcement, or showcase",
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Suggested tags for the post",
    )
    is_pinned: bool = Field(
        default=False,
        description="Whether this post should be pinned",
    )


class GeneratedPoll(PostContent):
    poll_question: str = Field(description="The poll question")
    poll_options: list[str] = Field(
        description="Options for the poll (2-6 choices)",
    )


class GeneratedAMAPrompt(PostContent):
    guest_name: Optional[str] = Field(default=None, description="Name of the AMA guest")
    guest_bio: Optional[str] = Field(default=None, description="Brief bio of the guest")
    suggested_questions: list[str] = Field(
        description="Suggested questions to get the discussion started",
    )


class GeneratedPostBatch(BaseModel):
    announcement: PostContent = Field(description="Community announcement post")
    weekly_post: PostContent = Field(description="Weekly discussion or update post")
    discussion_question: PostContent = Field(description="Thought-provoking discussion question")
    poll: GeneratedPoll = Field(description="Engagement poll for the community")
    ama_prompt: GeneratedAMAPrompt = Field(description="AMA (Ask Me Anything) prompt")
    event_announcement: PostContent = Field(description="Upcoming event announcement")


POST_TYPES = {
    "announcement": "a formal community announcement",
    "weekly_post": "a weekly update or discussion thread",
    "discussion_question": "an engaging discussion question to spark conversation",
    "poll": "an interactive poll with options",
    "ama_prompt": "an Ask Me Anything session prompt",
    "event_announcement": "an announcement for an upcoming event",
}

SYSTEM_PROMPT = (
    "You are an expert community engagement strategist and content writer. "
    "Create compelling, platform-ready posts that drive engagement. "
    "Each post should feel authentic, encourage participation, and match the community's tone. "
    "Include appropriate labels, tags, and pin suggestions. "
    "Output MUST be valid JSON matching the GeneratedPostBatch schema exactly."
)


def _build_user_prompt(
    community_name: str,
    community_description: str,
    topic: Optional[str] = None,
    language: str = "en",
) -> str:
    parts = [
        f"Create a batch of community posts for: {community_name}",
        f"Community description: {community_description}",
    ]
    if topic:
        parts.append(f"Focus topic or theme: {topic}")
    parts.append(f"Generate the response in {language}.")
    parts.append(
        "Include all 6 post types: announcement, weekly post, discussion question, "
        "poll, AMA prompt, and event announcement."
    )
    parts.append("Each post must have a compelling title and engaging content.")
    parts.append("Set is_pinned=True for the announcement and event announcement.")
    parts.append("Set appropriate labels based on the content type.")
    parts.append("\nReturn ONLY valid JSON matching the GeneratedPostBatch schema.")
    return "\n".join(parts)


class PostWriter:
    def __init__(self, ai_service: AIGenerationService):
        self._ai = ai_service

    async def generate(
        self,
        community_name: str,
        community_description: str,
        topic: Optional[str] = None,
        language: str = "en",
        model_name: Optional[str] = None,
    ) -> GeneratedPostBatch:
        user_prompt = _build_user_prompt(
            community_name, community_description, topic, language
        )

        result = await self._ai.generate(
            user_prompt=user_prompt,
            system_prompt=SYSTEM_PROMPT,
            temperature=0.8,
            max_tokens=8192,
            model_name=model_name,
            output_type=GeneratedPostBatch,
        )

        content = result.content
        if isinstance(content, dict):
            content = GeneratedPostBatch(**content)
        return content

    async def generate_single(
        self,
        post_type: str,
        community_name: str,
        community_description: str,
        topic: Optional[str] = None,
        language: str = "en",
        model_name: Optional[str] = None,
    ) -> PostContent:
        if post_type not in POST_TYPES:
            raise ValueError(
                f"Invalid post type '{post_type}'. Choose from: {', '.join(POST_TYPES.keys())}"
            )

        system_prompt = (
            f"You are an expert content writer. Create {POST_TYPES[post_type]}. "
            "Output MUST be valid JSON matching the PostContent schema."
        )
        parts = [
            f"Create a {post_type} for: {community_name}",
            f"Description: {community_description}",
        ]
        if topic:
            parts.append(f"Theme: {topic}")
        parts.append(f"Language: {language}")
        parts.append("\nReturn ONLY valid JSON matching the PostContent schema.")
        user_prompt = "\n".join(parts)

        result = await self._ai.generate(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.8,
            max_tokens=4096,
            model_name=model_name,
            output_type=PostContent,
        )

        content = result.content
        if isinstance(content, dict):
            content = PostContent(**content)
        return content

    async def generate_stream(
        self,
        community_name: str,
        community_description: str,
        topic: Optional[str] = None,
        language: str = "en",
        model_name: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        user_prompt = _build_user_prompt(
            community_name, community_description, topic, language
        )
        async for chunk in self._ai.generate_stream(
            user_prompt=user_prompt,
            system_prompt=SYSTEM_PROMPT,
            temperature=0.8,
            max_tokens=8192,
            model_name=model_name,
        ):
            yield chunk
