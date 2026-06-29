from __future__ import annotations

from typing import Any, Optional


class PromptTemplate:
    def __init__(self, template: str):
        self.template = template

    def render(self, **kwargs: Any) -> str:
        return self.template.format(**kwargs)


SYSTEM_PROMPTS: dict[str, str] = {
    "instructional_designer": (
        "You are an expert instructional designer. Create detailed, pedagogically sound "
        "educational content. Structure content logically from fundamentals to advanced topics. "
        "Use clear language and include practical examples."
    ),
    "content_writer": (
        "You are an expert educational content writer. Write engaging, clear content "
        "that is appropriate for the specified difficulty level. Include examples, "
        "practical applications, and assessment opportunities."
    ),
    "assessment_designer": (
        "You are an expert assessment designer. Create assessments that test understanding "
        "at multiple levels: recall, comprehension, application, and analysis."
    ),
    "curriculum_planner": (
        "You are an expert curriculum planner. Design complete course structures with "
        "clear progression, appropriate pacing, and measurable learning outcomes."
    ),
}


USER_PROMPTS: dict[str, str] = {
    "course_structure": (
        "Create a {level}-level course outline for: {topic}\n"
        "Generate the response in {language}.\n"
        "Include {num_modules} modules, each with 2-5 lessons.\n"
        "Each lesson should estimate 5-15 minutes to complete.\n"
        "Include assignments and quizzes for each module.\n"
        "Specify a certificate requirement (passing score)."
    ),
    "assignment": (
        "Create an assignment for the course '{course_title}', "
        "module '{module_title}', lesson '{lesson_title}'.\n"
        "Difficulty: {level}\n"
        "Include: title, description, instructions, grading rubric, "
        "max score, and submission type (file, text, quiz, or code)."
    ),
    "quiz": (
        "Create a {num_questions}-question quiz in {language} for:\n"
        "Course: {course_title}\n"
        "Module: {module_title}\n"
        "Lesson: {lesson_title}\n"
        "Difficulty: {level}\n"
        "Include multiple choice and true/false questions with answer explanations."
    ),
    "certificate": (
        "Define a certificate configuration for the course '{course_title}'.\n"
        "Include: title, description, passing criteria, and what the certificate certifies."
    ),
}


class PromptTemplateService:
    @staticmethod
    def get_system_prompt(role: str, language: str = "en") -> str:
        base = SYSTEM_PROMPTS.get(role, SYSTEM_PROMPTS["instructional_designer"])
        return f"{base}\nRespond in {language}."

    @staticmethod
    def render(template_key: str, **kwargs: Any) -> str:
        template = USER_PROMPTS.get(template_key)
        if not template:
            raise ValueError(f"Unknown prompt template: {template_key}")
        return template.format(**kwargs)

    @staticmethod
    def register_template(key: str, template: str):
        USER_PROMPTS[key] = template
