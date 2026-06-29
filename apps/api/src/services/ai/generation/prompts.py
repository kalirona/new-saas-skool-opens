"""Prompt templates for AI course generation."""


def build_course_structure_system_prompt(language: str = "en") -> str:
    """System prompt for generating a full course outline (modules + lessons)."""
    return f"""You are an expert instructional designer. Generate a complete course outline in {language}.
The outline must include a course title, description, learning outcomes, tags, and modules containing lessons.
Each lesson should have an estimated completion time.
Structure content logically from fundamentals to advanced topics.
Output MUST be valid JSON matching the GeneratedCourse schema exactly."""


def build_course_structure_user_prompt(topic: str, language: str = "en") -> str:
    """User prompt for generating a course structure."""
    return f"""Create a detailed course outline for: {topic}
Generate the response entirely in {language}.
Include 3-7 modules, each with 2-5 lessons. Each lesson should be 5-15 minutes."""


def build_lesson_content_system_prompt(language: str = "en") -> str:
    """System prompt for generating lesson body content as ProseMirror JSON."""
    return f"""You are an expert educational content writer. Generate lesson body content in {language} as a ProseMirror JSON document.
The document root must have "type": "doc" and a "content" array of block nodes.
Available block types: paragraph, heading, bulletList, orderedList, codeBlock, blockQuiz, calloutInfo, calloutWarning, blockquote, horizontalRule.
Headings use "attrs": {{"level": 2|3}}. Lists use bulletList/orderedList with listItem children.
Code blocks use "attrs": {{"language": "python"|"javascript"|...}}.
Make content engaging, clear, and pedagogically sound. Include examples and practical applications.
Output ONLY the ProseMirror JSON object, no markdown fences, no extra text."""


def build_lesson_content_user_prompt(
    lesson_title: str,
    lesson_description: str,
    module_title: str,
    course_title: str,
    include_quiz: bool = False,
    language: str = "en",
) -> str:
    """User prompt for generating lesson content."""
    parts = [
        f"Generate lesson content for the following in {language}:",
        f"Course: {course_title}",
        f"Module: {module_title}",
        f"Lesson: {lesson_title}",
        f"Description: {lesson_description}",
    ]
    if include_quiz:
        parts.append("Include a blockQuiz at the end with 3-5 multiple-choice questions to assess understanding.")
    return "\n".join(parts)


def build_quiz_system_prompt(language: str = "en") -> str:
    """System prompt for generating a quiz."""
    return f"""You are an expert assessment designer. Generate a quiz in {language} to test understanding of a lesson.
Each question should have 4 answer options with exactly one correct answer.
Questions should range from basic recall to application-level thinking.
Output MUST be valid JSON matching the GeneratedQuiz schema exactly."""


def build_quiz_user_prompt(
    lesson_title: str,
    lesson_description: str,
    module_title: str,
    course_title: str,
    num_questions: int = 5,
    language: str = "en",
) -> str:
    """User prompt for generating a quiz."""
    return f"""Generate a {num_questions}-question quiz in {language} for:
Course: {course_title}
Module: {module_title}
Lesson: {lesson_title}
Lesson Description: {lesson_description}

Each question must be multiple_choice type with 4 answers and exactly one correct."""
