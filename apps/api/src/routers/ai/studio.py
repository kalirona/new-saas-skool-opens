from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.core.events.database import get_db_session
from src.db.organizations import Organization
from src.db.users import PublicUser, AnonymousUser, APITokenUser
from src.security.auth import get_current_user, resolve_acting_user_id
from src.security.features_utils.usage import reserve_ai_credit
from src.security.org_auth import is_org_member
from src.services.ai.llm import model_for_tier, resolve_model_for_org
from src.services.ai.studio.course_generator import CourseGenerator, GeneratedCourse
from src.services.ai.studio.community_generator import CommunityGenerator, GeneratedCommunity
from src.services.ai.studio.post_writer import PostWriter, GeneratedPostBatch, PostContent
from src.services.ai.studio.resource_generator import ResourceGenerator, GeneratedResourceBatch
from src.services.ai.studio.landing_page_writer import LandingPageWriter, GeneratedLandingPage
from src.services.ai.studio.email_generator import EmailGenerator, GeneratedEmailBatch, GeneratedEmail
from src.services.ai.studio.workspace_assistant import WorkspaceAssistant, AssistantResponse
from src.services.ai.studio.usage_tracking_service import AIUsageTrackingService
from src.services.ai.studio.generation_service import AIGenerationService
from src.services.ai.studio.providers import get_provider
from src.services.ai.studio.cost_tracker import CostTracker
from src.services.ai.studio.token_tracker import TokenUsageTracker
from src.services.ai.studio.retry_handler import RetryHandler
from src.services.security.rate_limiting import enforce_ai_rate_limit

logger = logging.getLogger(__name__)

router = APIRouter()


class GenerateCourseRequest(BaseModel):
    org_id: int
    topic: str
    difficulty: str = "beginner"
    language: str = "en"
    num_modules: int = Field(default=5, ge=3, le=12)
    model_name: Optional[str] = None
    provider_id: Optional[str] = None


class GenerateCourseResponse(BaseModel):
    course: GeneratedCourse
    credits_used: int
    usage: dict = Field(default_factory=dict)


class GenerateCommunityRequest(BaseModel):
    org_id: int
    topic: str
    language: str = "en"
    num_spaces: int = Field(default=5, ge=3, le=12)
    model_name: Optional[str] = None
    provider_id: Optional[str] = None


class GenerateCommunityResponse(BaseModel):
    community: GeneratedCommunity
    credits_used: int
    usage: dict = Field(default_factory=dict)


class GeneratePostsRequest(BaseModel):
    org_id: int
    community_name: str
    community_description: str
    topic: Optional[str] = None
    post_type: Optional[str] = None
    language: str = "en"
    model_name: Optional[str] = None
    provider_id: Optional[str] = None


class GeneratePostsBatchResponse(BaseModel):
    posts: GeneratedPostBatch
    credits_used: int
    usage: dict = Field(default_factory=dict)


class GenerateSinglePostResponse(BaseModel):
    post: PostContent
    credits_used: int
    usage: dict = Field(default_factory=dict)


class GenerateResourcesRequest(BaseModel):
    org_id: int
    topic: str
    course_title: Optional[str] = None
    resource_type: Optional[str] = None
    language: str = "en"
    model_name: Optional[str] = None
    provider_id: Optional[str] = None


class GenerateResourcesBatchResponse(BaseModel):
    resources: GeneratedResourceBatch
    credits_used: int
    usage: dict = Field(default_factory=dict)


class GenerateSingleResourceResponse(BaseModel):
    resource: dict
    credits_used: int
    usage: dict = Field(default_factory=dict)


class GenerateLandingPageRequest(BaseModel):
    org_id: int
    topic: str
    language: str = "en"
    model_name: Optional[str] = None
    provider_id: Optional[str] = None


class GenerateLandingPageResponse(BaseModel):
    landing_page: GeneratedLandingPage
    credits_used: int
    usage: dict = Field(default_factory=dict)


class GenerateEmailsRequest(BaseModel):
    org_id: int
    product_name: str
    product_description: str
    audience: Optional[str] = None
    email_type: Optional[str] = None
    language: str = "en"
    model_name: Optional[str] = None
    provider_id: Optional[str] = None


class GenerateEmailsBatchResponse(BaseModel):
    emails: GeneratedEmailBatch
    credits_used: int
    usage: dict = Field(default_factory=dict)


class GenerateSingleEmailResponse(BaseModel):
    email: GeneratedEmail
    credits_used: int
    usage: dict = Field(default_factory=dict)


class AskAssistantRequest(BaseModel):
    org_id: int
    query: str
    entity_type: Optional[str] = Field(default=None, description="Filter: course, resource, community, event, setting")
    rag_enabled: bool = False
    model_name: Optional[str] = None
    provider_id: Optional[str] = None


class AskAssistantResponse(BaseModel):
    answer: str
    sources: list[dict] = Field(default_factory=list)
    requires_rag: bool = False
    usage: dict = Field(default_factory=dict)


class StudioInfoResponse(BaseModel):
    supported_providers: list[str]
    supported_difficulties: list[str]
    supported_post_types: list[str]
    supported_resource_types: list[str]
    supported_email_types: list[str]
    supported_entity_types: list[str]
    default_model_fast: str
    default_model_standard: str
    default_model_pro: str


def _build_generation_service(provider_id: Optional[str] = None) -> AIGenerationService:
    pid = (provider_id or "").strip().lower() or "gemini"
    provider = get_provider(pid)
    return AIGenerationService(
        provider=provider,
        token_tracker=TokenUsageTracker(),
        cost_tracker=CostTracker(),
        retry_handler=RetryHandler(max_retries=2),
    )


async def _verify_org_and_user(org_id: int, user_id: int, db_session: AsyncSession) -> Organization:
    org = (await db_session.execute(select(Organization).where(Organization.id == org_id))).scalars().first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    if not await is_org_member(user_id, org_id, db_session):
        raise HTTPException(status_code=403, detail="Not a member of this organization")
    return org


async def _resolve_model_and_charge(org_id: int, user_id: int, db_session: AsyncSession) -> tuple[str, int]:
    model_name = await resolve_model_for_org(org_id, db_session, purpose="planning")
    credit_cost = 3 if model_name == model_for_tier("pro") else 1
    enforce_ai_rate_limit(user_id, org_id)
    await reserve_ai_credit(org_id, db_session, amount=credit_cost)
    return model_name, credit_cost


@router.get("/studio/info", response_model=StudioInfoResponse)
async def api_studio_info() -> StudioInfoResponse:
    from src.services.ai.studio.providers import list_providers
    from src.services.ai.studio.post_writer import POST_TYPES
    from src.services.ai.studio.resource_generator import RESOURCE_TYPE_MAP
    from src.services.ai.studio.email_generator import EMAIL_TYPE_PROMPTS
    return StudioInfoResponse(
        supported_providers=list_providers(),
        supported_difficulties=["beginner", "intermediate", "advanced"],
        supported_post_types=list(POST_TYPES.keys()),
        supported_resource_types=list(RESOURCE_TYPE_MAP.keys()),
        supported_email_types=list(EMAIL_TYPE_PROMPTS.keys()),
        supported_entity_types=["course", "resource", "community", "event", "setting"],
        default_model_fast=model_for_tier("fast"),
        default_model_standard=model_for_tier("standard"),
        default_model_pro=model_for_tier("pro"),
    )


# ── TASK 2 — Course Generator ─────────────────────────────────────────────

@router.post("/studio/generate-course", response_model=GenerateCourseResponse, summary="Generate a complete course")
async def api_generate_course(
    req: GenerateCourseRequest,
    current_user: PublicUser | AnonymousUser | APITokenUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> GenerateCourseResponse:
    user_id = resolve_acting_user_id(current_user)
    await _verify_org_and_user(req.org_id, user_id, db_session)
    model_name, credit_cost = await _resolve_model_and_charge(req.org_id, user_id, db_session)
    model_name = req.model_name or model_name
    svc = _build_generation_service(req.provider_id)
    try:
        course = await CourseGenerator(svc).generate(
            topic=req.topic, difficulty=req.difficulty, language=req.language,
            num_modules=req.num_modules, model_name=model_name,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return GenerateCourseResponse(course=course, credits_used=credit_cost, usage=svc.get_usage_summary())


# ── TASK 3 — Community Generator ──────────────────────────────────────────

@router.post("/studio/generate-community", response_model=GenerateCommunityResponse, summary="Generate a community design")
async def api_generate_community(
    req: GenerateCommunityRequest,
    current_user: PublicUser | AnonymousUser | APITokenUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> GenerateCommunityResponse:
    user_id = resolve_acting_user_id(current_user)
    await _verify_org_and_user(req.org_id, user_id, db_session)
    model_name, credit_cost = await _resolve_model_and_charge(req.org_id, user_id, db_session)
    model_name = req.model_name or model_name
    svc = _build_generation_service(req.provider_id)
    community = await CommunityGenerator(svc).generate(
        topic=req.topic, language=req.language, num_spaces=req.num_spaces, model_name=model_name,
    )
    return GenerateCommunityResponse(community=community, credits_used=credit_cost, usage=svc.get_usage_summary())


# ── TASK 4 — Post Writer ──────────────────────────────────────────────────

@router.post("/studio/generate-posts", summary="Generate community posts")
async def api_generate_posts(
    req: GeneratePostsRequest,
    current_user: PublicUser | AnonymousUser | APITokenUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> GeneratePostsBatchResponse | GenerateSinglePostResponse:
    user_id = resolve_acting_user_id(current_user)
    await _verify_org_and_user(req.org_id, user_id, db_session)
    model_name, credit_cost = await _resolve_model_and_charge(req.org_id, user_id, db_session)
    model_name = req.model_name or model_name
    svc = _build_generation_service(req.provider_id)
    writer = PostWriter(svc)

    if req.post_type:
        post = await writer.generate_single(
            post_type=req.post_type, community_name=req.community_name,
            community_description=req.community_description, topic=req.topic,
            language=req.language, model_name=model_name,
        )
        return GenerateSinglePostResponse(post=post, credits_used=credit_cost, usage=svc.get_usage_summary())

    posts = await writer.generate(
        community_name=req.community_name, community_description=req.community_description,
        topic=req.topic, language=req.language, model_name=model_name,
    )
    return GeneratePostsBatchResponse(posts=posts, credits_used=credit_cost, usage=svc.get_usage_summary())


# ── TASK 5 — Resource Generator ───────────────────────────────────────────

@router.post("/studio/generate-resources", summary="Generate educational resources")
async def api_generate_resources(
    req: GenerateResourcesRequest,
    current_user: PublicUser | AnonymousUser | APITokenUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> GenerateResourcesBatchResponse | GenerateSingleResourceResponse:
    user_id = resolve_acting_user_id(current_user)
    await _verify_org_and_user(req.org_id, user_id, db_session)
    model_name, credit_cost = await _resolve_model_and_charge(req.org_id, user_id, db_session)
    model_name = req.model_name or model_name
    svc = _build_generation_service(req.provider_id)
    gen = ResourceGenerator(svc)

    if req.resource_type:
        resource = await gen.generate_single(
            resource_type=req.resource_type, topic=req.topic,
            course_title=req.course_title, language=req.language, model_name=model_name,
        )
        return GenerateSingleResourceResponse(
            resource=resource.model_dump(), credits_used=credit_cost, usage=svc.get_usage_summary(),
        )

    resources = await gen.generate_batch(
        topic=req.topic, course_title=req.course_title, language=req.language, model_name=model_name,
    )
    return GenerateResourcesBatchResponse(resources=resources, credits_used=credit_cost, usage=svc.get_usage_summary())


# ── TASK 6 — Landing Page Writer ──────────────────────────────────────────

@router.post("/studio/generate-landing-page", response_model=GenerateLandingPageResponse, summary="Generate a landing page")
async def api_generate_landing_page(
    req: GenerateLandingPageRequest,
    current_user: PublicUser | AnonymousUser | APITokenUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> GenerateLandingPageResponse:
    user_id = resolve_acting_user_id(current_user)
    await _verify_org_and_user(req.org_id, user_id, db_session)
    model_name, credit_cost = await _resolve_model_and_charge(req.org_id, user_id, db_session)
    model_name = req.model_name or model_name
    svc = _build_generation_service(req.provider_id)
    lp = await LandingPageWriter(svc).generate(topic=req.topic, language=req.language, model_name=model_name)
    return GenerateLandingPageResponse(landing_page=lp, credits_used=credit_cost, usage=svc.get_usage_summary())


# ── TASK 7 — Email Generator ──────────────────────────────────────────────

@router.post("/studio/generate-emails", summary="Generate email campaigns")
async def api_generate_emails(
    req: GenerateEmailsRequest,
    current_user: PublicUser | AnonymousUser | APITokenUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> GenerateEmailsBatchResponse | GenerateSingleEmailResponse:
    user_id = resolve_acting_user_id(current_user)
    await _verify_org_and_user(req.org_id, user_id, db_session)
    model_name, credit_cost = await _resolve_model_and_charge(req.org_id, user_id, db_session)
    model_name = req.model_name or model_name
    svc = _build_generation_service(req.provider_id)
    gen = EmailGenerator(svc)

    if req.email_type:
        email = await gen.generate_single(
            email_type=req.email_type, product_name=req.product_name,
            product_description=req.product_description, audience=req.audience,
            language=req.language, model_name=model_name,
        )
        return GenerateSingleEmailResponse(email=email, credits_used=credit_cost, usage=svc.get_usage_summary())

    emails = await gen.generate_batch(
        product_name=req.product_name, product_description=req.product_description,
        audience=req.audience, language=req.language, model_name=model_name,
    )
    return GenerateEmailsBatchResponse(emails=emails, credits_used=credit_cost, usage=svc.get_usage_summary())


# ── TASK 8 — Workspace Assistant ──────────────────────────────────────────

@router.post("/studio/ask", response_model=AskAssistantResponse, summary="Ask the workspace AI assistant")
async def api_ask_assistant(
    req: AskAssistantRequest,
    current_user: PublicUser | AnonymousUser | APITokenUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> AskAssistantResponse:
    user_id = resolve_acting_user_id(current_user)
    await _verify_org_and_user(req.org_id, user_id, db_session)
    enforce_ai_rate_limit(user_id, req.org_id)

    model_name = req.model_name or await resolve_model_for_org(req.org_id, db_session, purpose="assistant")
    svc = _build_generation_service(req.provider_id)
    assistant = WorkspaceAssistant(svc)

    result = await assistant.ask(
        query=req.query, org_id=req.org_id, user_id=user_id,
        db_session=db_session, entity_type=req.entity_type,
        rag_enabled=req.rag_enabled, model_name=model_name,
    )

    return AskAssistantResponse(
        answer=result.answer,
        sources=result.sources,
        requires_rag=result.requires_rag,
        usage=svc.get_usage_summary(),
    )


# ── TASK 9 — Prompt Library ───────────────────────────────────────────────

@router.get("/studio/prompts", summary="List prompt templates")
async def api_list_prompts(
    org_id: int = Query(...),
    category: Optional[str] = Query(default=None),
    include_system: bool = Query(default=True),
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    from src.services.ai.prompts.prompt_library import PromptLibraryService
    if not await is_org_member(current_user.id, org_id, db_session):
        raise HTTPException(status_code=403, detail="Not a member")
    return await PromptLibraryService.list_for_org(org_id, db_session, category, include_system)


@router.get("/studio/prompts/{prompt_uuid}", summary="Get a prompt template")
async def api_get_prompt(
    prompt_uuid: str,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    from src.services.ai.prompts.prompt_library import PromptLibraryService
    prompt = await PromptLibraryService.get(prompt_uuid, db_session)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return prompt


@router.post("/studio/prompts", summary="Create a new prompt template")
async def api_create_prompt(
    data: dict,
    org_id: int = Query(...),
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    from src.db.ai.prompt_library import PromptTemplateCreate
    from src.services.ai.prompts.prompt_library import PromptLibraryService
    user_id = resolve_acting_user_id(current_user)
    if not await is_org_member(user_id, org_id, db_session):
        raise HTTPException(status_code=403, detail="Not a member")
    pdata = PromptTemplateCreate(**data)
    return await PromptLibraryService.create(org_id, user_id, pdata, db_session)


@router.put("/studio/prompts/{prompt_uuid}", summary="Update a prompt template")
async def api_update_prompt(
    prompt_uuid: str,
    data: dict,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    from src.db.ai.prompt_library import PromptTemplateUpdate
    from src.services.ai.prompts.prompt_library import PromptLibraryService
    pdata = PromptTemplateUpdate(**data)
    result = await PromptLibraryService.update(prompt_uuid, pdata, db_session)
    if not result:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return result


@router.delete("/studio/prompts/{prompt_uuid}", summary="Delete a prompt template")
async def api_delete_prompt(
    prompt_uuid: str,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    from src.services.ai.prompts.prompt_library import PromptLibraryService
    if not await PromptLibraryService.delete(prompt_uuid, db_session):
        raise HTTPException(status_code=404, detail="Prompt not found")
    return {"status": "deleted"}


@router.post("/studio/prompts/{prompt_uuid}/versions", summary="Create a new version")
async def api_create_prompt_version(
    prompt_uuid: str,
    data: dict,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    from src.db.ai.prompt_library import PromptTemplateVersionCreate
    from src.services.ai.prompts.prompt_library import PromptLibraryService
    user_id = resolve_acting_user_id(current_user)
    vdata = PromptTemplateVersionCreate(**data)
    result = await PromptLibraryService.create_version(prompt_uuid, user_id, vdata, db_session)
    if not result:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return result


@router.get("/studio/prompts/{prompt_uuid}/versions", summary="List all versions")
async def api_list_prompt_versions(
    prompt_uuid: str,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    from src.services.ai.prompts.prompt_library import PromptLibraryService
    return await PromptLibraryService.list_versions(prompt_uuid, db_session)


# ── TASK 10 — Usage & Limits ──────────────────────────────────────────────

@router.get("/studio/usage", summary="Get AI usage summary for workspace")
async def api_get_usage(
    org_id: int = Query(...),
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    user_id = resolve_acting_user_id(current_user)
    await _verify_org_and_user(org_id, user_id, db_session)
    return await AIUsageTrackingService.get_usage_summary(org_id, db_session)


@router.get("/studio/usage/quota", summary="Get AI quota for workspace")
async def api_get_quota(
    org_id: int = Query(...),
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    user_id = resolve_acting_user_id(current_user)
    await _verify_org_and_user(org_id, user_id, db_session)
    return await AIUsageTrackingService.get_or_create_quota(org_id, db_session)


@router.put("/studio/usage/quota", summary="Update AI quota for workspace")
async def api_update_quota(
    data: dict,
    org_id: int = Query(...),
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    user_id = resolve_acting_user_id(current_user)
    await _verify_org_and_user(org_id, user_id, db_session)
    from src.security.features_utils.usage import check_feature_access
    await check_feature_access("ai", org_id, db_session)
    result = await AIUsageTrackingService.update_quota(org_id, db_session, **data)
    if not result:
        raise HTTPException(status_code=404, detail="Quota not found")
    return result
