from __future__ import annotations

import logging
from typing import AsyncGenerator, Optional

from pydantic import BaseModel, Field

from src.services.ai.studio.generation_service import AIGenerationService

logger = logging.getLogger(__name__)


class TestimonialPlaceholder(BaseModel):
    name: str = Field(description="Fictional person's name")
    role: str = Field(description="Job title or role")
    quote: str = Field(description="Testimonial quote")
    avatar_initials: str = Field(description="Two-letter initials for avatar placeholder")


class FAQItem(BaseModel):
    question: str = Field(description="Frequently asked question")
    answer: str = Field(description="Answer to the question")


class SEOMetadata(BaseModel):
    page_title: str = Field(description="SEO page title (50-60 chars)")
    meta_description: str = Field(description="Meta description (150-160 chars)")
    meta_keywords: list[str] = Field(description="Target keywords")
    og_title: str = Field(description="Open Graph title")
    og_description: str = Field(description="Open Graph description")


class GeneratedLandingPage(BaseModel):
    headline: str = Field(description="Primary headline / value proposition")
    subheadline: str = Field(description="Supporting subheadline")
    hero_description: str = Field(description="Hero section description text")
    hero_cta_text: str = Field(description="Call-to-action button text for hero")
    benefits: list[dict] = Field(
        description="Each benefit: title, description, icon_name",
    )
    testimonials: list[TestimonialPlaceholder] = Field(
        description="Placeholder testimonials (3-4)",
    )
    faq: list[FAQItem] = Field(description="FAQ section items (5-8)")
    cta_headline: str = Field(description="CTA section headline")
    cta_description: str = Field(description="CTA section description text")
    cta_button_text: str = Field(description="CTA button text")
    seo: SEOMetadata = Field(description="SEO metadata")


SYSTEM_PROMPT = (
    "You are an expert marketing copywriter and conversion designer. "
    "Create a complete, compelling landing page for a product, course, or community. "
    "Focus on clear value propositions, social proof, and strong calls to action. "
    "Output MUST be valid JSON matching the GeneratedLandingPage schema exactly."
)


def _build_user_prompt(topic: str, language: str = "en") -> str:
    return (
        f"Create a high-converting landing page for: {topic}\n"
        f"Language: {language}\n\n"
        f"Include:\n"
        f"- A powerful headline and subheadline\n"
        f"- Hero section with description and CTA\n"
        f"- 4-6 key benefits with descriptions\n"
        f"- 3-4 placeholder testimonials\n"
        f"- 5-8 FAQ items\n"
        f"- A compelling CTA section\n"
        f"- Complete SEO metadata\n\n"
        f"Return ONLY valid JSON matching the GeneratedLandingPage schema."
    )


class LandingPageWriter:
    def __init__(self, ai_service: AIGenerationService):
        self._ai = ai_service

    async def generate(
        self,
        topic: str,
        language: str = "en",
        model_name: Optional[str] = None,
    ) -> GeneratedLandingPage:
        user_prompt = _build_user_prompt(topic, language)
        result = await self._ai.generate(
            user_prompt=user_prompt,
            system_prompt=SYSTEM_PROMPT,
            temperature=0.7,
            max_tokens=8192,
            model_name=model_name,
            output_type=GeneratedLandingPage,
        )
        content = result.content
        if isinstance(content, dict):
            content = GeneratedLandingPage(**content)
        return content

    async def generate_stream(
        self,
        topic: str,
        language: str = "en",
        model_name: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        user_prompt = _build_user_prompt(topic, language)
        async for chunk in self._ai.generate_stream(
            user_prompt=user_prompt,
            system_prompt=SYSTEM_PROMPT,
            temperature=0.7,
            max_tokens=8192,
            model_name=model_name,
        ):
            yield chunk
