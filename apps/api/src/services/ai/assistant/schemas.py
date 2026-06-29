"""Request/response schemas for the AI assistant.

Each capability has its own pair of request/response models.
The top-level ``AssistantRequest`` / ``AssistantResponse`` wraps them all.
"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional, Literal

from pydantic import BaseModel, Field


# ── Capability identifiers ──────────────────────────────────────────────────

AssistantCapability = Literal["qa", "summarize", "generate", "moderate"]


# ── Q&A ────────────────────────────────────────────────────────────────────


class QARequest(BaseModel):
    question: str = Field(description="The member's question")
    discussion_context: Optional[str] = Field(default=None, description="Related discussion thread content")
    course_context: Optional[str] = Field(default=None, description="Related course/lesson name")
    max_sources: int = Field(default=3, description="Max source references to include")


class QAResponse(BaseModel):
    answer: str = Field(description="AI-generated answer to the question")
    sources: List[str] = Field(default_factory=list, description="Referenced sources")
    confidence: Literal["high", "medium", "low"] = Field(default="medium", description="Answer confidence level")


# ── Summarize ──────────────────────────────────────────────────────────────


class SummaryType(str, Enum):
    THREAD = "thread"
    DISCUSSION = "discussion"
    POST = "post"


class SummarizeRequest(BaseModel):
    content: str = Field(description="The content to summarize")
    summary_type: SummaryType = Field(default=SummaryType.DISCUSSION, description="Type of content being summarized")
    max_length: int = Field(default=200, description="Maximum summary length in words")
    include_key_points: bool = Field(default=True, description="Extract key bullet points")


class SummarizeResponse(BaseModel):
    summary: str = Field(description="Concise summary of the content")
    key_points: List[str] = Field(default_factory=list, description="Key bullet points extracted")
    word_count: int = Field(default=0, description="Word count of the summary")


# ── Generate ───────────────────────────────────────────────────────────────


class ContentTone(str, Enum):
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    ENCOURAGING = "encouraging"
    NEUTRAL = "neutral"


class ContentTypeName(str, Enum):
    POST = "post"
    REPLY = "reply"
    ANNOUNCEMENT = "announcement"
    DISCUSSION_PROMPT = "discussion_prompt"


class GenerateRequest(BaseModel):
    content_type: ContentTypeName = Field(description="Type of content to generate")
    topic: str = Field(description="The main topic or subject")
    tone: ContentTone = Field(default=ContentTone.PROFESSIONAL, description="Desired tone of voice")
    context: Optional[str] = Field(default=None, description="Additional context or background")
    max_length: int = Field(default=300, description="Maximum length in words")


class GenerateResponse(BaseModel):
    content: str = Field(description="Generated content text")
    title_suggestion: Optional[str] = Field(default=None, description="Suggested title if applicable")
    word_count: int = Field(default=0, description="Word count of generated content")


# ── Moderate ───────────────────────────────────────────────────────────────


class ModerationCategory(str, Enum):
    TOXICITY = "toxicity"
    SPAM = "spam"
    HARASSMENT = "harassment"
    HATE_SPEECH = "hate_speech"
    NSFW = "nsfw"
    SELF_HARM = "self_harm"
    VIOLENCE = "violence"


class ModerateRequest(BaseModel):
    content: str = Field(description="The content to moderate")
    categories: List[ModerationCategory] = Field(
        default_factory=lambda: [ModerationCategory.TOXICITY, ModerationCategory.SPAM, ModerationCategory.HARASSMENT],
        description="Categories to check"
    )


class ModerationResult(BaseModel):
    category: ModerationCategory
    flagged: bool = Field(default=False)
    score: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence score (0-1)")
    explanation: Optional[str] = Field(default=None)


class ModerateResponse(BaseModel):
    is_flagged: bool = Field(default=False, description="True if any category exceeds threshold")
    results: List[ModerationResult] = Field(default_factory=list, description="Per-category results")
    summary: Optional[str] = Field(default=None, description="Overall moderation explanation")


# ── Top-level wrapper ──────────────────────────────────────────────────────


class AssistantRequest(BaseModel):
    capability: AssistantCapability = Field(description="Which assistant capability to invoke")
    org_id: int = Field(description="Organization ID")
    language: str = Field(default="en", description="ISO language code")
    qa: Optional[QARequest] = None
    summarize: Optional[SummarizeRequest] = None
    generate: Optional[GenerateRequest] = None
    moderate: Optional[ModerateRequest] = None


class AssistantResponse(BaseModel):
    capability: AssistantCapability
    qa: Optional[QAResponse] = None
    summarize: Optional[SummarizeResponse] = None
    generate: Optional[GenerateResponse] = None
    moderate: Optional[ModerateResponse] = None
    credits_used: int = Field(default=1)
