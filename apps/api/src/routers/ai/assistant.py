"""API routes for the AI assistant.

Provides a single endpoint ``POST /ai/assistant/run`` that dispatches to
the correct capability based on the ``capability`` field.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.core.events.database import get_db_session
from src.db.organizations import Organization
from src.db.users import PublicUser, AnonymousUser, APITokenUser
from src.security.auth import get_current_user, resolve_acting_user_id
from src.security.features_utils.usage import reserve_ai_credit
from src.security.org_auth import is_org_member
from src.services.ai.assistant import AssistantRequest, AssistantResponse, run_assistant
from src.services.ai.llm import model_for_tier, resolve_model_for_org
from src.services.security.rate_limiting import enforce_ai_rate_limit

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/assistant/run",
    response_model=AssistantResponse,
    summary="Run an AI assistant capability",
    description="Dispatch to the requested assistant capability (qa|summarize|generate|moderate). Stateless — no session management.",
    responses={
        200: {"description": "Assistant response", "model": AssistantResponse},
        400: {"description": "Invalid capability or missing request body"},
        401: {"description": "Authentication required"},
        403: {"description": "User not org member or insufficient credits"},
        404: {"description": "Organization not found"},
    },
)
async def api_run_assistant(
    req: AssistantRequest,
    current_user: PublicUser | AnonymousUser | APITokenUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> AssistantResponse:
    """Run an AI assistant capability."""
    user_id = resolve_acting_user_id(current_user)

    # Verify org exists and user is a member
    statement = select(Organization).where(Organization.id == req.org_id)
    org = (await db_session.execute(statement)).scalars().first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    if not await is_org_member(user_id, req.org_id, db_session):
        raise HTTPException(status_code=403, detail="User is not a member of this organization")

    # Resolve model and credit cost
    model_name = await resolve_model_for_org(req.org_id, db_session, purpose="assistant")
    credit_cost = 3 if model_name == model_for_tier("pro") else 1

    # Rate limit and deduct AI credit
    enforce_ai_rate_limit(user_id, req.org_id)
    await reserve_ai_credit(req.org_id, db_session, amount=credit_cost)

    # Dispatch to the capability handler
    try:
        response = await run_assistant(req, model_name)
        response.credits_used = credit_cost
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
