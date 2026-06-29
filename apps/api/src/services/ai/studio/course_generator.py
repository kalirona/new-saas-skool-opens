from __future__ import annotations

import logging
from typing import Any, AsyncGenerator, Optional

from pydantic import BaseModel, Field

from src.services.ai.studio.generation_service import AIGenerationService
from src.services.ai.studio.prompt_templates import PromptTemplateService

logger = logging.getLogger(__name__)


class GeneratedAssignment(BaseModel):
    title: str = Field(description="Assignment title")
    description: str = Field(description="Assignment description")
    instructions: str = Field(description="Detailed instructions for the assignment")
    submission_type: str = Field(
        description="Submission type: file, text, quiz, or code",
    )
    max_score: int = Field(default=100, description="Maximum score")
    grading_rubric: Optional[str] = Field(
        default=None,
        description="Brief grading rubric or criteria",
    )


class GeneratedQuizQuestion(BaseModel):
    question: str = Field(description="The quiz question text")
    question_type: str = Field(
        default="multiple_choice",
        description="Question type: multiple_choice, true_false, short_answer",
    )
    options: list[str] = Field(
        default_factory=list,
        description="Answer options (for multiple_choice and true_false)",
    )
    correct_answer: str = Field(description="The correct answer")
    explanation: str = Field(description="Explanation of the correct answer")


class GeneratedQuiz(BaseModel):
    title: str = Field(description="Quiz title")
    questions: list[GeneratedQuizQuestion] = Field(
        description="List of quiz questions",
    )


class GeneratedCertificate(BaseModel):
    title: str = Field(description="Certificate title")
    description: str = Field(description="What this certificate certifies")
    passing_score: int = Field(
        default=80,
        description="Minimum passing score percentage required",
    )


class GeneratedLesson(BaseModel):
    title: str = Field(description="Lesson title")
    description: str = Field(description="Brief description of what this lesson covers")
    estimated_minutes: int = Field(
        default=10,
        description="Estimated time to complete in minutes",
    )
    key_points: list[str] = Field(
        default_factory=list,
        description="Key learning points for this lesson",
    )


class GeneratedModule(BaseModel):
    title: str = Field(description="Module/chapter title")
    description: str = Field(description="Overview of what this module covers")
    learning_objectives: list[str] = Field(
        default_factory=list,
        description="Specific learning objectives for this module",
    )
    lessons: list[GeneratedLesson] = Field(
        description="Lessons within this module",
    )
    assignment: Optional[GeneratedAssignment] = Field(
        default=None,
        description="Optional assignment for this module",
    )
    quiz: Optional[GeneratedQuiz] = Field(
        default=None,
        description="Optional quiz for this module",
    )


class GeneratedCourse(BaseModel):
    title: str = Field(description="Course title")
    description: str = Field(description="Course description / elevator pitch")
    learnings: list[str] = Field(
        description="List of learning outcomes / objectives",
    )
    tags: list[str] = Field(
        description="Relevant tags for discoverability",
    )
    difficulty: str = Field(
        description="Difficulty level: beginner, intermediate, or advanced",
    )
    estimated_total_minutes: int = Field(
        default=0,
        description="Total estimated time to complete the course in minutes",
    )
    modules: list[GeneratedModule] = Field(
        description="Modules/chapters in the course",
    )
    final_quiz: Optional[GeneratedQuiz] = Field(
        default=None,
        description="Optional final exam for the course",
    )
    certificate: Optional[GeneratedCertificate] = Field(
        default=None,
        description="Optional certificate configuration",
    )


DIFFICULTY_GUIDES: dict[str, str] = {
    "beginner": (
        "Assume no prior knowledge. Use simple language, define all terms, "
        "provide step-by-step instructions, and include plenty of examples. "
        "Focus on foundational concepts and build confidence."
    ),
    "intermediate": (
        "Assume basic familiarity with the topic. Include more depth, "
        "real-world scenarios, and moderate complexity. Connect concepts "
        "and encourage critical thinking."
    ),
    "advanced": (
        "Assume strong foundational knowledge. Cover complex topics, "
        "advanced techniques, edge cases, and expert-level insights. "
        "Challenge the learner with nuanced material."
    ),
}


SYSTEM_PROMPT = (
    "You are an expert curriculum designer and instructional designer. "
    "Generate a complete, production-ready course plan. "
    "Structure content logically with clear progression. "
    "Include practical assignments and assessment quizzes for each module. "
    "Design a comprehensive final exam and a certificate configuration. "
    "Output MUST be valid JSON matching the GeneratedCourse schema exactly."
)


def _build_user_prompt(
    topic: str,
    difficulty: str,
    language: str = "en",
    num_modules: int = 5,
) -> str:
    guide = DIFFICULTY_GUIDES.get(difficulty, DIFFICULTY_GUIDES["beginner"])
    return (
        f"Create a {difficulty}-level course outline for: {topic}\n\n"
        f"Difficulty guidelines:\n{guide}\n\n"
        f"Generate the response in {language}.\n"
        f"Include {num_modules} modules.\n"
        f"Each module should have 2-5 lessons, one assignment, and one quiz.\n"
        f"Each lesson should estimate 5-15 minutes to complete.\n"
        f"Include a final exam quiz and a certificate configuration.\n"
        f"Calculate the estimated_total_minutes as the sum of all lesson estimates."
        f"\n\nReturn ONLY valid JSON matching the GeneratedCourse schema."
    )


class CourseGenerator:
    def __init__(self, ai_service: AIGenerationService):
        self._ai = ai_service

    async def generate(
        self,
        topic: str,
        difficulty: str = "beginner",
        language: str = "en",
        num_modules: int = 5,
        model_name: Optional[str] = None,
    ) -> GeneratedCourse:
        if difficulty not in DIFFICULTY_GUIDES:
            raise ValueError(
                f"Invalid difficulty '{difficulty}'. Choose from: {', '.join(DIFFICULTY_GUIDES.keys())}"
            )

        user_prompt = _build_user_prompt(topic, difficulty, language, num_modules)

        result = await self._ai.generate(
            user_prompt=user_prompt,
            system_prompt=SYSTEM_PROMPT,
            temperature=0.7,
            max_tokens=8192,
            model_name=model_name,
            output_type=GeneratedCourse,
        )

        course = result.content
        if isinstance(course, dict):
            course = GeneratedCourse(**course)

        course.difficulty = difficulty

        total = sum(
            sum(l.estimated_minutes for l in m.lessons) for m in course.modules
        )
        course.estimated_total_minutes = total

        return course

    async def generate_stream(
        self,
        topic: str,
        difficulty: str = "beginner",
        language: str = "en",
        num_modules: int = 5,
        model_name: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        user_prompt = _build_user_prompt(topic, difficulty, language, num_modules)
        async for chunk in self._ai.generate_stream(
            user_prompt=user_prompt,
            system_prompt=SYSTEM_PROMPT,
            temperature=0.7,
            max_tokens=8192,
            model_name=model_name,
        ):
            yield chunk
