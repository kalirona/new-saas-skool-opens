from pydantic import BaseModel, Field
from typing import Optional, List


class GeneratedQuizQuestion(BaseModel):
    question: str = Field(description="The quiz question text")
    type: str = Field(default="multiple_choice", description="Question type: multiple_choice, true_false, short_answer")
    answers: List[dict] = Field(description="List of answer options, each with answer_id, answer, and correct (bool)")


class GeneratedQuiz(BaseModel):
    title: str = Field(description="A descriptive title for the quiz")
    questions: List[GeneratedQuizQuestion] = Field(description="The list of quiz questions")


class GeneratedLesson(BaseModel):
    title: str = Field(description="Lesson title")
    description: str = Field(description="Brief description of what this lesson covers")
    estimated_minutes: int = Field(default=10, description="Estimated time to complete in minutes")


class GeneratedModule(BaseModel):
    title: str = Field(description="Module/chapter title")
    description: str = Field(description="Overview of what this module covers")
    lessons: List[GeneratedLesson] = Field(description="Lessons within this module")


class GeneratedCourse(BaseModel):
    title: str = Field(description="Course title")
    description: str = Field(description="Course description / elevator pitch")
    learnings: List[str] = Field(description="List of learning outcomes")
    tags: List[str] = Field(description="Relevant tags for discoverability")
    modules: List[GeneratedModule] = Field(description="Modules/chapters in the course")
