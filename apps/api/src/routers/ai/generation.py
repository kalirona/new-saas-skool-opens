"""API routes for AI course generation.

Provides a stateless generation API (no Redis sessions) that produces
structured course outlines, lesson content, and quizzes.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.core.events.database import get_db_session
from src.db.organizations import Organization
from src.db.users import PublicUser, AnonymousUser, APITokenUser
from src.security.auth import get_current_user, resolve_acting_user_id
from src.security.features_utils.usage import reserve_ai_credit
from src.security.org_auth import is_org_member
from src.services.ai.generation import (
    GeneratedCourse,
    GeneratedQuiz,
    generate_course_structure,
    generate_lesson_content,
    generate_quiz,
)
from src.services.ai.llm import model_for_tier, resolve_model_for_org
from src.services.security.rate_limiting import enforce_ai_rate_limit

logger = logging.getLogger(__name__)

router = APIRouter()


# ──────────────────────────────── Request / Response models ───────────────────


class CourseStructureRequest(BaseModel):
    org_id: int = Field(description="Organization ID")
    topic: str = Field(description="Course topic or description")
    language: str = Field(default="en", description="ISO language code for content")


class CourseStructureResponse(BaseModel):
    course: GeneratedCourse
    credits_used: int


class LessonContentRequest(BaseModel):
    org_id: int
    lesson_title: str
    lesson_description: str
    module_title: str
    course_title: str
    language: str = "en"
    include_quiz: bool = False


class LessonContentResponse(BaseModel):
    content: dict
    credits_used: int


class QuizRequest(BaseModel):
    org_id: int
    lesson_title: str
    lesson_description: str
    module_title: str
    course_title: str
    language: str = "en"
    num_questions: int = 5


class QuizResponse(BaseModel):
    quiz: GeneratedQuiz
    credits_used: int


# ──────────────────────────────── Endpoints ───────────────────────────────────


async def _verify_org_and_user(org_id: int, user_id: int, db_session: AsyncSession) -> Organization:
    """Verify org exists and user is a member. Returns the org."""
    statement = select(Organization).where(Organization.id == org_id)
    org = (await db_session.execute(statement)).scalars().first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    if not await is_org_member(user_id, org_id, db_session):
        raise HTTPException(status_code=403, detail="User is not a member of this organization")
    return org


async def _resolve_model_and_credit_cost(
    org_id: int, db_session: AsyncSession
) -> tuple[str, int]:
    """Resolve AI model for the org and the credit cost per call."""
    model = await resolve_model_for_org(org_id, db_session, purpose="planning")
    credit_cost = 3 if model == model_for_tier("pro") else 1
    return model, credit_cost


async def _charge_ai_credit(
    org_id: int, user_id: int, credit_cost: int, db_session: AsyncSession
) -> None:
    """Apply rate limit and deduct AI credit."""
    enforce_ai_rate_limit(user_id, org_id)
    await reserve_ai_credit(org_id, db_session, amount=credit_cost)


@router.post(
    "/generation/course",
    response_model=CourseStructureResponse,
    summary="Generate course structure",
    description="Generate a complete course outline (modules, lessons, descriptions) from a topic. Stateless — no session management.",
    responses={
        200: {"description": "Generated course structure", "model": CourseStructureResponse},
        401: {"description": "Authentication required"},
        403: {"description": "User not org member or insufficient credits"},
        404: {"description": "Organization not found"},
    },
)
async def api_generate_course_structure(
    req: CourseStructureRequest,
    current_user: PublicUser | AnonymousUser | APITokenUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> CourseStructureResponse:
    """Generate a full course outline from a topic description."""
    user_id = resolve_acting_user_id(current_user)
    await _verify_org_and_user(req.org_id, user_id, db_session)

    model_name, credit_cost = await _resolve_model_and_credit_cost(req.org_id, db_session)
    await _charge_ai_credit(req.org_id, user_id, credit_cost, db_session)

    course = await generate_course_structure(
        topic=req.topic,
        model_name=model_name,
        language=req.language,
    )
    return CourseStructureResponse(course=course, credits_used=credit_cost)


@router.post(
    "/generation/lesson-content",
    response_model=LessonContentResponse,
    summary="Generate lesson content",
    description="Generate ProseMirror JSON content for a single lesson. Optionally includes an inline quiz block.",
    responses={
        200: {"description": "Generated lesson content as ProseMirror JSON", "model": LessonContentResponse},
        401: {"description": "Authentication required"},
        403: {"description": "User not org member or insufficient credits"},
        404: {"description": "Organization not found"},
    },
)
async def api_generate_lesson_content(
    req: LessonContentRequest,
    current_user: PublicUser | AnonymousUser | APITokenUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> LessonContentResponse:
    """Generate lesson body content as ProseMirror JSON."""
    user_id = resolve_acting_user_id(current_user)
    await _verify_org_and_user(req.org_id, user_id, db_session)

    model_name, credit_cost = await _resolve_model_and_credit_cost(req.org_id, db_session)
    await _charge_ai_credit(req.org_id, user_id, credit_cost, db_session)

    content = await generate_lesson_content(
        lesson_title=req.lesson_title,
        lesson_description=req.lesson_description,
        module_title=req.module_title,
        course_title=req.course_title,
        model_name=model_name,
        language=req.language,
        include_quiz=req.include_quiz,
    )
    return LessonContentResponse(content=content, credits_used=credit_cost)


@router.post(
    "/generation/quiz",
    response_model=QuizResponse,
    summary="Generate lesson quiz",
    description="Generate a standalone quiz (multiple-choice questions) for a lesson. Useful for creating assessments independent of content generation.",
    responses={
        200: {"description": "Generated quiz", "model": QuizResponse},
        401: {"description": "Authentication required"},
        403: {"description": "User not org member or insufficient credits"},
        404: {"description": "Organization not found"},
    },
)
async def api_generate_quiz(
    req: QuizRequest,
    current_user: PublicUser | AnonymousUser | APITokenUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> QuizResponse:
    """Generate a quiz for a lesson."""
    user_id = resolve_acting_user_id(current_user)
    await _verify_org_and_user(req.org_id, user_id, db_session)

    model_name, credit_cost = await _resolve_model_and_credit_cost(req.org_id, db_session)
    await _charge_ai_credit(req.org_id, user_id, credit_cost, db_session)

    quiz = await generate_quiz(
        lesson_title=req.lesson_title,
        lesson_description=req.lesson_description,
        module_title=req.module_title,
        course_title=req.course_title,
        model_name=model_name,
        language=req.language,
        num_questions=req.num_questions,
    )
    return QuizResponse(quiz=quiz, credits_used=credit_cost)
