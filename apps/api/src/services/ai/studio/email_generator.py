from __future__ import annotations

import logging
from typing import AsyncGenerator, Optional

from pydantic import BaseModel, Field

from src.services.ai.studio.generation_service import AIGenerationService

logger = logging.getLogger(__name__)


class GeneratedEmail(BaseModel):
    subject: str = Field(description="Email subject line")
    preview_text: str = Field(description="Email preview text (preheader)")
    greeting: str = Field(description="Email greeting / salutation")
    body_html: str = Field(description="HTML body content — use <h2>, <p>, <ul>, <li>, <a>, <strong>")
    body_text: str = Field(description="Plain text version of the email body")
    cta_text: Optional[str] = Field(default=None, description="Call-to-action button text")
    cta_link: Optional[str] = Field(default=None, description="Call-to-action URL placeholder")
    closing: str = Field(description="Email closing / sign-off")
    signature_name: Optional[str] = Field(default=None, description="Sender name for signature")


class GeneratedEmailBatch(BaseModel):
    welcome_email: GeneratedEmail = Field(description="Welcome email for new members")
    onboarding_series: list[GeneratedEmail] = Field(
        description="Onboarding email series (3-5 emails)",
    )
    sales_email: GeneratedEmail = Field(description="Sales / promotional email")
    reminder_email: GeneratedEmail = Field(description="Reminder / re-engagement email")
    event_email: GeneratedEmail = Field(description="Event announcement or reminder email")


EMAIL_TYPE_PROMPTS = {
    "welcome": (
        "a warm welcome email for new members. Make them feel valued and "
        "excited about joining. Include what to expect next."
    ),
    "onboarding": (
        "an onboarding email series that guides users through getting started. "
        "Focus on key actions, tips, and encouragement."
    ),
    "sales": (
        "a persuasive sales or promotional email. Highlight value, create urgency, "
        "and include a clear call to action."
    ),
    "reminder": (
        "a re-engagement or reminder email. Be helpful and timely, "
        "reminding users of value they might be missing."
    ),
    "event": (
        "an event announcement or reminder email. Build excitement, "
        "include key details (date, time, link), and drive registration."
    ),
}

SYSTEM_PROMPT = (
    "You are an expert email marketing copywriter. Create professional, "
    "engaging emails that drive action. Each email should have a compelling "
    "subject line, clear preview text, well-structured HTML body, and a "
    "plain text alternative. Output MUST be valid JSON."
)

BATCH_SYSTEM_PROMPT = (
    "You are an expert email marketing strategist. Create a complete email "
    "campaign including welcome, onboarding series, sales, reminder, and event "
    "emails. Each email must have subject, preview, HTML body, text body, CTA, "
    "and closing. Output MUST be valid JSON matching the GeneratedEmailBatch schema."
)


def _build_batch_prompt(
    product_name: str,
    product_description: str,
    audience: Optional[str] = None,
    language: str = "en",
) -> str:
    parts = [
        f"Create a complete email campaign for: {product_name}",
        f"Product description: {product_description}",
    ]
    if audience:
        parts.append(f"Target audience: {audience}")
    parts.append(f"Language: {language}")
    parts.append(
        "Include:\n"
        "1. Welcome email\n"
        "2. Onboarding series (4 emails)\n"
        "3. Sales email\n"
        "4. Reminder email\n"
        "5. Event email\n\n"
        "Each email must have HTML body using simple tags (h2, p, ul, li, a)."
        "\n\nReturn ONLY valid JSON matching the GeneratedEmailBatch schema."
    )
    return "\n".join(parts)


class EmailGenerator:
    def __init__(self, ai_service: AIGenerationService):
        self._ai = ai_service

    async def generate_batch(
        self,
        product_name: str,
        product_description: str,
        audience: Optional[str] = None,
        language: str = "en",
        model_name: Optional[str] = None,
    ) -> GeneratedEmailBatch:
        user_prompt = _build_batch_prompt(product_name, product_description, audience, language)
        result = await self._ai.generate(
            user_prompt=user_prompt,
            system_prompt=BATCH_SYSTEM_PROMPT,
            temperature=0.7,
            max_tokens=8192,
            model_name=model_name,
            output_type=GeneratedEmailBatch,
        )
        content = result.content
        if isinstance(content, dict):
            content = GeneratedEmailBatch(**content)
        return content

    async def generate_single(
        self,
        email_type: str,
        product_name: str,
        product_description: str,
        audience: Optional[str] = None,
        language: str = "en",
        model_name: Optional[str] = None,
    ) -> GeneratedEmail:
        type_desc = EMAIL_TYPE_PROMPTS.get(email_type)
        if not type_desc:
            raise ValueError(
                f"Invalid email type '{email_type}'. Choose from: {', '.join(EMAIL_TYPE_PROMPTS.keys())}"
            )
        system_prompt = (
            f"You are an expert email copywriter. Write {type_desc} "
            "Output MUST be valid JSON matching the GeneratedEmail schema."
        )
        parts = [
            f"Write a {email_type} email for: {product_name}",
            f"Description: {product_description}",
        ]
        if audience:
            parts.append(f"Audience: {audience}")
        parts.append(f"Language: {language}")
        parts.append("\nReturn ONLY valid JSON matching the GeneratedEmail schema.")
        user_prompt = "\n".join(parts)

        result = await self._ai.generate(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=4096,
            model_name=model_name,
            output_type=GeneratedEmail,
        )
        content = result.content
        if isinstance(content, dict):
            content = GeneratedEmail(**content)
        return content

    async def generate_stream(
        self,
        product_name: str,
        product_description: str,
        audience: Optional[str] = None,
        language: str = "en",
        model_name: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        user_prompt = _build_batch_prompt(product_name, product_description, audience, language)
        async for chunk in self._ai.generate_stream(
            user_prompt=user_prompt,
            system_prompt=BATCH_SYSTEM_PROMPT,
            temperature=0.7,
            max_tokens=8192,
            model_name=model_name,
        ):
            yield chunk
