from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel.ext.asyncio.session import AsyncSession

from src.core.events.database import get_db_session
from src.db.users import PublicUser
from src.security.auth import get_current_user, resolve_acting_user_id
from src.services.ai.prompts.prompt_library import PromptLibraryService
from src.services.security.rate_limiting import enforce_ai_rate_limit

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/prompts", summary="List prompt templates for the org")
async def api_list_prompts(
    org_id: int = Query(..., description="Organization ID"),
    category: Optional[str] = Query(default=None),
    include_system: bool = Query(default=True),
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    from src.security.org_auth import is_org_member
    if not await is_org_member(current_user.id, org_id, db_session):
        raise HTTPException(status_code=403, detail="Not a member")
    return await PromptLibraryService.list_for_org(org_id, db_session, category, include_system)


@router.get("/prompts/{prompt_uuid}", summary="Get a prompt template")
async def api_get_prompt(
    prompt_uuid: str,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    prompt = await PromptLibraryService.get(prompt_uuid, db_session)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return prompt


@router.post("/prompts", summary="Create a new prompt template")
async def api_create_prompt(
    data: dict,
    org_id: int = Query(...),
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    from src.db.ai.prompt_library import PromptTemplateCreate
    from src.security.org_auth import is_org_member
    user_id = resolve_acting_user_id(current_user)
    if not await is_org_member(user_id, org_id, db_session):
        raise HTTPException(status_code=403, detail="Not a member")
    pdata = PromptTemplateCreate(**data)
    return await PromptLibraryService.create(org_id, user_id, pdata, db_session)


@router.put("/prompts/{prompt_uuid}", summary="Update a prompt template")
async def api_update_prompt(
    prompt_uuid: str,
    data: dict,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    from src.db.ai.prompt_library import PromptTemplateUpdate
    pdata = PromptTemplateUpdate(**data)
    result = await PromptLibraryService.update(prompt_uuid, pdata, db_session)
    if not result:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return result


@router.delete("/prompts/{prompt_uuid}", summary="Delete a prompt template")
async def api_delete_prompt(
    prompt_uuid: str,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    if not await PromptLibraryService.delete(prompt_uuid, db_session):
        raise HTTPException(status_code=404, detail="Prompt not found")
    return {"status": "deleted"}


@router.post("/prompts/{prompt_uuid}/versions", summary="Create a new version")
async def api_create_prompt_version(
    prompt_uuid: str,
    data: dict,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    from src.db.ai.prompt_library import PromptTemplateVersionCreate
    user_id = resolve_acting_user_id(current_user)
    vdata = PromptTemplateVersionCreate(**data)
    result = await PromptLibraryService.create_version(prompt_uuid, user_id, vdata, db_session)
    if not result:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return result


@router.get("/prompts/{prompt_uuid}/versions", summary="List all versions of a prompt")
async def api_list_prompt_versions(
    prompt_uuid: str,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    return await PromptLibraryService.list_versions(prompt_uuid, db_session)
