from __future__ import annotations

import logging
from typing import AsyncGenerator, Optional

from pydantic import BaseModel, Field

from src.services.ai.studio.generation_service import AIGenerationService

logger = logging.getLogger(__name__)


class GeneratedResourceMetadata(BaseModel):
    title: str = Field(description="Resource title")
    description: str = Field(description="Brief description of the resource")
    category: Optional[str] = Field(
        default=None,
        description="Category for the resource",
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Tags for discoverability",
    )
    resource_type: str = Field(
        description="Type: pdf, video, audio, link, file, markdown, rich_text, ai_prompt, template",
    )
    visibility: str = Field(
        default="public",
        description="Visibility: public, private, or restricted",
    )
    estimated_read_minutes: Optional[int] = Field(
        default=None,
        description="Estimated reading time in minutes",
    )


class GeneratedPDFOutline(BaseModel):
    title: str = Field(description="PDF title")
    description: str = Field(description="What this PDF covers")
    sections: list[dict] = Field(
        description="Sections each with title, content_summary, and estimated_pages",
    )
    target_audience: str = Field(description="Who this PDF is for")
    key_takeaways: list[str] = Field(description="Key takeaways for readers")
    metadata: GeneratedResourceMetadata = Field(
        description="Resource metadata for this outline",
    )


class GeneratedPromptPack(BaseModel):
    title: str = Field(description="Prompt pack title")
    description: str = Field(description="Overview of what these prompts help with")
    prompts: list[dict] = Field(
        description="Each prompt with: title, category, prompt_text, use_case, expected_output",
    )
    difficulty: str = Field(description="Difficulty: beginner, intermediate, or advanced")
    metadata: GeneratedResourceMetadata = Field(
        description="Resource metadata for this prompt pack",
    )


class GeneratedTemplate(BaseModel):
    title: str = Field(description="Template title")
    description: str = Field(description="What this template is used for")
    template_structure: list[dict] = Field(
        description="Template sections each with: section_name, description, placeholder_fields",
    )
    usage_instructions: str = Field(description="How to use this template")
    metadata: GeneratedResourceMetadata = Field(
        description="Resource metadata for this template",
    )


class GeneratedChecklist(BaseModel):
    title: str = Field(description="Checklist title")
    description: str = Field(description="What this checklist helps with")
    categories: list[dict] = Field(
        description="Each category with: name, items (list of checklist items with task and priority)",
    )
    completion_criteria: str = Field(description="How to determine completion")
    metadata: GeneratedResourceMetadata = Field(
        description="Resource metadata for this checklist",
    )


class GeneratedGuide(BaseModel):
    title: str = Field(description="Guide title")
    description: str = Field(description="Guide overview")
    sections: list[dict] = Field(
        description="Sections each with: heading, content_summary, key_tips, estimated_read_minutes",
    )
    prerequisites: list[str] = Field(description="Required knowledge or tools")
    next_steps: list[str] = Field(description="Recommended next steps after reading")
    metadata: GeneratedResourceMetadata = Field(
        description="Resource metadata for this guide",
    )


class GeneratedDownload(BaseModel):
    title: str = Field(description="Download title")
    description: str = Field(description="What this download contains")
    file_type: str = Field(description="File type: pdf, zip, csv, json, markdown")
    file_size_estimate: str = Field(description="Estimated file size")
    contents: list[dict] = Field(
        description="Contents each with: name, description, format",
    )
    metadata: GeneratedResourceMetadata = Field(
        description="Resource metadata for this download",
    )


RESOURCE_TYPE_MAP = {
    "pdf_outline": {
        "class": GeneratedPDFOutline,
        "description": "a detailed PDF outline with sections and key takeaways",
        "resource_type": "pdf",
    },
    "prompt_pack": {
        "class": GeneratedPromptPack,
        "description": "a pack of AI prompts organized by category and use case",
        "resource_type": "ai_prompt",
    },
    "template": {
        "class": GeneratedTemplate,
        "description": "a reusable template with placeholders and instructions",
        "resource_type": "template",
    },
    "checklist": {
        "class": GeneratedChecklist,
        "description": "a structured checklist with categories and priorities",
        "resource_type": "markdown",
    },
    "guide": {
        "class": GeneratedGuide,
        "description": "a comprehensive how-to guide with sections and tips",
        "resource_type": "markdown",
    },
    "download": {
        "class": GeneratedDownload,
        "description": "a downloadable resource with contents listing",
        "resource_type": "file",
    },
}


class GeneratedResourceBatch(BaseModel):
    pdf_outline: GeneratedPDFOutline = Field(description="Generated PDF outline")
    prompt_pack: GeneratedPromptPack = Field(description="Generated prompt pack")
    template: GeneratedTemplate = Field(description="Generated template")
    checklist: GeneratedChecklist = Field(description="Generated checklist")
    guide: GeneratedGuide = Field(description="Generated guide")
    download: GeneratedDownload = Field(description="Generated downloadable resource")


BATCH_SYSTEM_PROMPT = (
    "You are an expert content creator and instructional designer. "
    "Generate a comprehensive batch of educational resources for a course or topic. "
    "Each resource type must have complete, actionable content with proper metadata. "
    "Output MUST be valid JSON matching the GeneratedResourceBatch schema exactly."
)


def _build_batch_prompt(
    topic: str,
    course_title: Optional[str] = None,
    language: str = "en",
) -> str:
    parts = [
        f"Create a batch of educational resources for: {topic}",
    ]
    if course_title:
        parts.append(f"Course: {course_title}")
    parts.append(f"Language: {language}")
    parts.append(
        "Generate all 6 resource types:\n"
        "1. PDF outline — a structured document outline with sections and takeaways\n"
        "2. Prompt pack — AI prompts organized by use case\n"
        "3. Template — a reusable template with placeholder fields\n"
        "4. Checklist — action items organized by category with priorities\n"
        "5. Guide — a comprehensive how-to guide with sections\n"
        "6. Download — a downloadable resource with file listing\n\n"
        "Each resource must include proper metadata (title, description, tags, category, type)."
        "\n\nReturn ONLY valid JSON matching the GeneratedResourceBatch schema."
    )
    return "\n".join(parts)


class ResourceGenerator:
    def __init__(self, ai_service: AIGenerationService):
        self._ai = ai_service

    async def generate_batch(
        self,
        topic: str,
        course_title: Optional[str] = None,
        language: str = "en",
        model_name: Optional[str] = None,
    ) -> GeneratedResourceBatch:
        user_prompt = _build_batch_prompt(topic, course_title, language)

        result = await self._ai.generate(
            user_prompt=user_prompt,
            system_prompt=BATCH_SYSTEM_PROMPT,
            temperature=0.7,
            max_tokens=8192,
            model_name=model_name,
            output_type=GeneratedResourceBatch,
        )

        content = result.content
        if isinstance(content, dict):
            content = GeneratedResourceBatch(**content)
        return content

    async def generate_single(
        self,
        resource_type: str,
        topic: str,
        course_title: Optional[str] = None,
        language: str = "en",
        model_name: Optional[str] = None,
    ) -> BaseModel:
        type_info = RESOURCE_TYPE_MAP.get(resource_type)
        if not type_info:
            raise ValueError(
                f"Invalid resource type '{resource_type}'. "
                f"Choose from: {', '.join(RESOURCE_TYPE_MAP.keys())}"
            )

        output_cls = type_info["class"]
        system_prompt = (
            f"You are an expert content creator. Generate {type_info['description']}. "
            f"Output MUST be valid JSON matching {output_cls.__name__} schema exactly."
        )
        parts = [
            f"Create a {resource_type} for: {topic}",
        ]
        if course_title:
            parts.append(f"Course: {course_title}")
        parts.append(f"Language: {language}")
        parts.append(f"\nReturn ONLY valid JSON matching the {output_cls.__name__} schema.")
        user_prompt = "\n".join(parts)

        result = await self._ai.generate(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=4096,
            model_name=model_name,
            output_type=output_cls,
        )

        content = result.content
        if isinstance(content, dict):
            content = output_cls(**content)
        return content

    async def generate_stream(
        self,
        topic: str,
        course_title: Optional[str] = None,
        language: str = "en",
        model_name: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        user_prompt = _build_batch_prompt(topic, course_title, language)
        async for chunk in self._ai.generate_stream(
            user_prompt=user_prompt,
            system_prompt=BATCH_SYSTEM_PROMPT,
            temperature=0.7,
            max_tokens=8192,
            model_name=model_name,
        ):
            yield chunk
