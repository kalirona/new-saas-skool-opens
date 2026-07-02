"""Prompt templates for the AI assistant capabilities."""

from src.services.ai.prompt_sanitizer import sanitize_user_input


def build_qa_system_prompt(language: str = "en") -> str:
    return f"""You are a helpful course assistant. Answer member questions based on the provided context.
Be concise, accurate, and supportive. If you don't know the answer, say so clearly.
Respond in {language}.
When referencing sources, cite them by name."""


def build_qa_user_prompt(
    question: str,
    discussion_context: str | None = None,
    course_context: str | None = None,
) -> str:
    parts = [f"Question: {sanitize_user_input(question)}"]
    if discussion_context:
        parts.append(f"\nDiscussion context:\n{discussion_context}")
    if course_context:
        parts.append(f"\nCourse context:\n{course_context}")
    parts.append("\nProvide a clear answer with references if applicable.")
    return "\n".join(parts)


def build_summarize_system_prompt(language: str = "en") -> str:
    return f"""You are an expert content summarizer. Summarize the given content concisely while retaining key information.
Respond in {language}.
Extract main ideas, key arguments, and important conclusions."""


def build_summarize_user_prompt(
    content: str,
    summary_type: str,
    max_length: int,
    include_key_points: bool,
) -> str:
    parts = [
        f"Summarize this {summary_type} in at most {max_length} words:",
        content,
    ]
    if include_key_points:
        parts.append("\nAlso list 3-5 key bullet points.")
    return "\n\n".join(parts)


def build_generate_system_prompt(language: str = "en") -> str:
    return f"""You are an expert community content writer. Generate engaging, well-written content.
Respond in {language}.
Match the requested tone and content type. Keep the audience engaged and the content actionable."""


def build_generate_user_prompt(
    content_type: str,
    topic: str,
    tone: str,
    context: str | None = None,
    max_length: int = 300,
) -> str:
    parts = [
        f"Write a {tone} {content_type} about: {sanitize_user_input(topic)}",
        f"Maximum {max_length} words.",
    ]
    if context:
        parts.append(f"Context:\n{context}")
    return "\n\n".join(parts)


def build_moderate_system_prompt(language: str = "en") -> str:
    return f"""You are a content moderator. Review the given content and determine if it violates community guidelines.
Check for: toxicity, spam, harassment, hate speech, NSFW content, self-harm, and violence.
Respond in {language}.
For each category, provide a score (0-1) and brief explanation."""


def build_moderate_user_prompt(content: str, categories: list[str]) -> str:
    return f"Review this content for the following categories: {', '.join(categories)}\n\nContent:\n{sanitize_user_input(content)}"
