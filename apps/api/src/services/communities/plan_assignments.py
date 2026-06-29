from typing import List, Optional, Union
from uuid import uuid4
from datetime import datetime
from sqlmodel import select, delete
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import HTTPException, Request
from sqlalchemy import and_

from src.db.users import PublicUser, AnonymousUser, APITokenUser
from src.db.communities.membership_plans import MembershipPlan
from src.db.communities.plan_courses import PlanCourse, PlanCourseCreate, PlanCourseRead
from src.db.communities.plan_spaces import PlanSpace, PlanSpaceCreate, PlanSpaceRead
from src.db.communities.plan_resources import PlanResource, PlanResourceCreate, PlanResourceRead
from src.db.communities.plan_events import PlanEvent, PlanEventCreate, PlanEventRead
from src.db.communities.communities import Community
from src.db.communities.spaces import Space
from src.db.resources.resources import Resource
from src.db.events.events import Event
from src.db.courses.courses import Course
from src.security.rbac import (
    check_resource_access,
    AccessAction,
    authorization_verify_if_user_is_anon,
    authorization_verify_based_on_org_admin_status,
)


async def _verify_community_admin(
    request: Request,
    community_uuid: str,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> Community:
    await authorization_verify_if_user_is_anon(current_user.id)
    community = (
        await db_session.execute(
            select(Community).where(Community.community_uuid == community_uuid)
        )
    ).scalars().first()
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")
    await authorization_verify_based_on_org_admin_status(community.org_id, current_user, request)
    return community


async def _verify_plan_belongs_to_community(
    plan_uuid: str, community_id: int, db_session: AsyncSession
) -> MembershipPlan:
    plan = (
        await db_session.execute(
            select(MembershipPlan).where(
                MembershipPlan.plan_uuid == plan_uuid,
                MembershipPlan.community_id == community_id,
            )
        )
    ).scalars().first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan


async def get_assigned_courses(
    request: Request,
    community_uuid: str,
    plan_uuid: str,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> List[PlanCourseRead]:
    community = await _verify_community_admin(request, community_uuid, current_user, db_session)
    plan = await _verify_plan_belongs_to_community(plan_uuid, community.id, db_session)
    result = await db_session.execute(
        select(PlanCourse).where(PlanCourse.plan_id == plan.id)
    )
    return [PlanCourseRead.model_validate(row.model_dump()) for row in result.scalars().all()]


async def assign_course_to_plan(
    request: Request,
    community_uuid: str,
    plan_uuid: str,
    course_uuid: str,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> PlanCourseRead:
    community = await _verify_community_admin(request, community_uuid, current_user, db_session)
    plan = await _verify_plan_belongs_to_community(plan_uuid, community.id, db_session)
    course = (
        await db_session.execute(
            select(Course).where(Course.course_uuid == course_uuid)
        )
    ).scalars().first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    existing = await db_session.execute(
        select(PlanCourse).where(
            and_(PlanCourse.plan_id == plan.id, PlanCourse.course_id == course.id)
        )
    )
    if existing.scalars().first():
        raise HTTPException(status_code=409, detail="Course already assigned to plan")
    assignment = PlanCourse(
        plan_id=plan.id,
        course_id=course.id,
        creation_date=str(datetime.now()),
        update_date=str(datetime.now()),
    )
    db_session.add(assignment)
    await db_session.commit()
    await db_session.refresh(assignment)
    return PlanCourseRead.model_validate(assignment.model_dump())


async def remove_course_from_plan(
    request: Request,
    community_uuid: str,
    plan_uuid: str,
    course_uuid: str,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> dict:
    community = await _verify_community_admin(request, community_uuid, current_user, db_session)
    plan = await _verify_plan_belongs_to_community(plan_uuid, community.id, db_session)
    course = (
        await db_session.execute(
            select(Course).where(Course.course_uuid == course_uuid)
        )
    ).scalars().first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    stmt = delete(PlanCourse).where(
        and_(PlanCourse.plan_id == plan.id, PlanCourse.course_id == course.id)
    )
    await db_session.execute(stmt)
    await db_session.commit()
    return {"status": "removed"}


async def get_assigned_spaces(
    request: Request,
    community_uuid: str,
    plan_uuid: str,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> List[PlanSpaceRead]:
    community = await _verify_community_admin(request, community_uuid, current_user, db_session)
    plan = await _verify_plan_belongs_to_community(plan_uuid, community.id, db_session)
    result = await db_session.execute(
        select(PlanSpace).where(PlanSpace.plan_id == plan.id)
    )
    return [PlanSpaceRead.model_validate(row.model_dump()) for row in result.scalars().all()]


async def assign_space_to_plan(
    request: Request,
    community_uuid: str,
    plan_uuid: str,
    space_uuid: str,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> PlanSpaceRead:
    community = await _verify_community_admin(request, community_uuid, current_user, db_session)
    plan = await _verify_plan_belongs_to_community(plan_uuid, community.id, db_session)
    space = (
        await db_session.execute(
            select(Space).where(
                Space.space_uuid == space_uuid,
                Space.community_id == community.id,
            )
        )
    ).scalars().first()
    if not space:
        raise HTTPException(status_code=404, detail="Space not found")
    existing = await db_session.execute(
        select(PlanSpace).where(
            and_(PlanSpace.plan_id == plan.id, PlanSpace.space_id == space.id)
        )
    )
    if existing.scalars().first():
        raise HTTPException(status_code=409, detail="Space already assigned to plan")
    assignment = PlanSpace(
        plan_id=plan.id,
        space_id=space.id,
        creation_date=str(datetime.now()),
        update_date=str(datetime.now()),
    )
    db_session.add(assignment)
    await db_session.commit()
    await db_session.refresh(assignment)
    return PlanSpaceRead.model_validate(assignment.model_dump())


async def remove_space_from_plan(
    request: Request,
    community_uuid: str,
    plan_uuid: str,
    space_uuid: str,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> dict:
    community = await _verify_community_admin(request, community_uuid, current_user, db_session)
    plan = await _verify_plan_belongs_to_community(plan_uuid, community.id, db_session)
    space = (
        await db_session.execute(
            select(Space).where(
                Space.space_uuid == space_uuid,
                Space.community_id == community.id,
            )
        )
    ).scalars().first()
    if not space:
        raise HTTPException(status_code=404, detail="Space not found")
    stmt = delete(PlanSpace).where(
        and_(PlanSpace.plan_id == plan.id, PlanSpace.space_id == space.id)
    )
    await db_session.execute(stmt)
    await db_session.commit()
    return {"status": "removed"}


async def get_assigned_resources(
    request: Request,
    community_uuid: str,
    plan_uuid: str,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> List[PlanResourceRead]:
    community = await _verify_community_admin(request, community_uuid, current_user, db_session)
    plan = await _verify_plan_belongs_to_community(plan_uuid, community.id, db_session)
    result = await db_session.execute(
        select(PlanResource).where(PlanResource.plan_id == plan.id)
    )
    return [PlanResourceRead.model_validate(row.model_dump()) for row in result.scalars().all()]


async def assign_resource_to_plan(
    request: Request,
    community_uuid: str,
    plan_uuid: str,
    resource_uuid: str,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> PlanResourceRead:
    community = await _verify_community_admin(request, community_uuid, current_user, db_session)
    plan = await _verify_plan_belongs_to_community(plan_uuid, community.id, db_session)
    resource = (
        await db_session.execute(
            select(Resource).where(Resource.resource_uuid == resource_uuid)
        )
    ).scalars().first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    existing = await db_session.execute(
        select(PlanResource).where(
            and_(PlanResource.plan_id == plan.id, PlanResource.resource_id == resource.id)
        )
    )
    if existing.scalars().first():
        raise HTTPException(status_code=409, detail="Resource already assigned to plan")
    assignment = PlanResource(
        plan_id=plan.id,
        resource_id=resource.id,
        creation_date=str(datetime.now()),
        update_date=str(datetime.now()),
    )
    db_session.add(assignment)
    await db_session.commit()
    await db_session.refresh(assignment)
    return PlanResourceRead.model_validate(assignment.model_dump())


async def remove_resource_from_plan(
    request: Request,
    community_uuid: str,
    plan_uuid: str,
    resource_uuid: str,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> dict:
    community = await _verify_community_admin(request, community_uuid, current_user, db_session)
    plan = await _verify_plan_belongs_to_community(plan_uuid, community.id, db_session)
    resource = (
        await db_session.execute(
            select(Resource).where(Resource.resource_uuid == resource_uuid)
        )
    ).scalars().first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    stmt = delete(PlanResource).where(
        and_(PlanResource.plan_id == plan.id, PlanResource.resource_id == resource.id)
    )
    await db_session.execute(stmt)
    await db_session.commit()
    return {"status": "removed"}


async def get_assigned_events(
    request: Request,
    community_uuid: str,
    plan_uuid: str,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> List[PlanEventRead]:
    community = await _verify_community_admin(request, community_uuid, current_user, db_session)
    plan = await _verify_plan_belongs_to_community(plan_uuid, community.id, db_session)
    result = await db_session.execute(
        select(PlanEvent).where(PlanEvent.plan_id == plan.id)
    )
    return [PlanEventRead.model_validate(row.model_dump()) for row in result.scalars().all()]


async def assign_event_to_plan(
    request: Request,
    community_uuid: str,
    plan_uuid: str,
    event_uuid: str,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> PlanEventRead:
    community = await _verify_community_admin(request, community_uuid, current_user, db_session)
    plan = await _verify_plan_belongs_to_community(plan_uuid, community.id, db_session)
    event = (
        await db_session.execute(
            select(Event).where(Event.event_uuid == event_uuid)
        )
    ).scalars().first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    existing = await db_session.execute(
        select(PlanEvent).where(
            and_(PlanEvent.plan_id == plan.id, PlanEvent.event_id == event.id)
        )
    )
    if existing.scalars().first():
        raise HTTPException(status_code=409, detail="Event already assigned to plan")
    assignment = PlanEvent(
        plan_id=plan.id,
        event_id=event.id,
        creation_date=str(datetime.now()),
        update_date=str(datetime.now()),
    )
    db_session.add(assignment)
    await db_session.commit()
    await db_session.refresh(assignment)
    return PlanEventRead.model_validate(assignment.model_dump())


async def remove_event_from_plan(
    request: Request,
    community_uuid: str,
    plan_uuid: str,
    event_uuid: str,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> dict:
    community = await _verify_community_admin(request, community_uuid, current_user, db_session)
    plan = await _verify_plan_belongs_to_community(plan_uuid, community.id, db_session)
    event = (
        await db_session.execute(
            select(Event).where(Event.event_uuid == event_uuid)
        )
    ).scalars().first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    stmt = delete(PlanEvent).where(
        and_(PlanEvent.plan_id == plan.id, PlanEvent.event_id == event.id)
    )
    await db_session.execute(stmt)
    await db_session.commit()
    return {"status": "removed"}
