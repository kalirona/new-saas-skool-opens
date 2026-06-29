from typing import List
from fastapi import APIRouter, Depends, Request
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.events.database import get_db_session
from src.db.users import PublicUser
from src.db.communities.plan_courses import PlanCourseRead
from src.db.communities.plan_spaces import PlanSpaceRead
from src.db.communities.plan_resources import PlanResourceRead
from src.db.communities.plan_events import PlanEventRead
from src.security.auth import get_current_user
from src.services.communities.plan_assignments import (
    get_assigned_courses,
    assign_course_to_plan,
    remove_course_from_plan,
    get_assigned_spaces,
    assign_space_to_plan,
    remove_space_from_plan,
    get_assigned_resources,
    assign_resource_to_plan,
    remove_resource_from_plan,
    get_assigned_events,
    assign_event_to_plan,
    remove_event_from_plan,
)


router = APIRouter()


@router.get(
    "/communities/{community_uuid}/plans/{plan_uuid}/courses",
    response_model=List[PlanCourseRead],
    summary="List courses assigned to a plan",
)
async def api_get_plan_courses(
    request: Request,
    community_uuid: str,
    plan_uuid: str,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> List[PlanCourseRead]:
    return await get_assigned_courses(request, community_uuid, plan_uuid, current_user, db_session)


@router.post(
    "/communities/{community_uuid}/plans/{plan_uuid}/courses/{course_uuid}",
    response_model=PlanCourseRead,
    summary="Assign a course to a plan",
)
async def api_assign_course_to_plan(
    request: Request,
    community_uuid: str,
    plan_uuid: str,
    course_uuid: str,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> PlanCourseRead:
    return await assign_course_to_plan(request, community_uuid, plan_uuid, course_uuid, current_user, db_session)


@router.delete(
    "/communities/{community_uuid}/plans/{plan_uuid}/courses/{course_uuid}",
    summary="Remove a course from a plan",
)
async def api_remove_course_from_plan(
    request: Request,
    community_uuid: str,
    plan_uuid: str,
    course_uuid: str,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> dict:
    return await remove_course_from_plan(request, community_uuid, plan_uuid, course_uuid, current_user, db_session)


@router.get(
    "/communities/{community_uuid}/plans/{plan_uuid}/spaces",
    response_model=List[PlanSpaceRead],
    summary="List spaces assigned to a plan",
)
async def api_get_plan_spaces(
    request: Request,
    community_uuid: str,
    plan_uuid: str,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> List[PlanSpaceRead]:
    return await get_assigned_spaces(request, community_uuid, plan_uuid, current_user, db_session)


@router.post(
    "/communities/{community_uuid}/plans/{plan_uuid}/spaces/{space_uuid}",
    response_model=PlanSpaceRead,
    summary="Assign a space to a plan",
)
async def api_assign_space_to_plan(
    request: Request,
    community_uuid: str,
    plan_uuid: str,
    space_uuid: str,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> PlanSpaceRead:
    return await assign_space_to_plan(request, community_uuid, plan_uuid, space_uuid, current_user, db_session)


@router.delete(
    "/communities/{community_uuid}/plans/{plan_uuid}/spaces/{space_uuid}",
    summary="Remove a space from a plan",
)
async def api_remove_space_from_plan(
    request: Request,
    community_uuid: str,
    plan_uuid: str,
    space_uuid: str,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> dict:
    return await remove_space_from_plan(request, community_uuid, plan_uuid, space_uuid, current_user, db_session)


@router.get(
    "/communities/{community_uuid}/plans/{plan_uuid}/resources",
    response_model=List[PlanResourceRead],
    summary="List resources assigned to a plan",
)
async def api_get_plan_resources(
    request: Request,
    community_uuid: str,
    plan_uuid: str,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> List[PlanResourceRead]:
    return await get_assigned_resources(request, community_uuid, plan_uuid, current_user, db_session)


@router.post(
    "/communities/{community_uuid}/plans/{plan_uuid}/resources/{resource_uuid}",
    response_model=PlanResourceRead,
    summary="Assign a resource to a plan",
)
async def api_assign_resource_to_plan(
    request: Request,
    community_uuid: str,
    plan_uuid: str,
    resource_uuid: str,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> PlanResourceRead:
    return await assign_resource_to_plan(request, community_uuid, plan_uuid, resource_uuid, current_user, db_session)


@router.delete(
    "/communities/{community_uuid}/plans/{plan_uuid}/resources/{resource_uuid}",
    summary="Remove a resource from a plan",
)
async def api_remove_resource_from_plan(
    request: Request,
    community_uuid: str,
    plan_uuid: str,
    resource_uuid: str,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> dict:
    return await remove_resource_from_plan(request, community_uuid, plan_uuid, resource_uuid, current_user, db_session)


@router.get(
    "/communities/{community_uuid}/plans/{plan_uuid}/events",
    response_model=List[PlanEventRead],
    summary="List events assigned to a plan",
)
async def api_get_plan_events(
    request: Request,
    community_uuid: str,
    plan_uuid: str,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> List[PlanEventRead]:
    return await get_assigned_events(request, community_uuid, plan_uuid, current_user, db_session)


@router.post(
    "/communities/{community_uuid}/plans/{plan_uuid}/events/{event_uuid}",
    response_model=PlanEventRead,
    summary="Assign an event to a plan",
)
async def api_assign_event_to_plan(
    request: Request,
    community_uuid: str,
    plan_uuid: str,
    event_uuid: str,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> PlanEventRead:
    return await assign_event_to_plan(request, community_uuid, plan_uuid, event_uuid, current_user, db_session)


@router.delete(
    "/communities/{community_uuid}/plans/{plan_uuid}/events/{event_uuid}",
    summary="Remove an event from a plan",
)
async def api_remove_event_from_plan(
    request: Request,
    community_uuid: str,
    plan_uuid: str,
    event_uuid: str,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> dict:
    return await remove_event_from_plan(request, community_uuid, plan_uuid, event_uuid, current_user, db_session)
