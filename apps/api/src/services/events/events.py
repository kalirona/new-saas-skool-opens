"""
Event service — full CRUD + RSVP + meeting provider integration.
"""

import asyncio
from typing import List, Optional, Union, Dict, Any
from uuid import uuid4
from datetime import datetime
from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import HTTPException, Request

from src.db.users import PublicUser, AnonymousUser, APITokenUser
from src.db.organizations import Organization
from src.db.communities.communities import Community
from src.db.communities.spaces import Space
from src.db.events.events import (
    Event,
    EventCreate,
    EventRead,
    EventDetailRead,
    EventUpdate,
    EVENT_TYPES,
    EVENT_STATUSES,
)
from src.db.events.rsvps import (
    RSVP,
    RSVPCreate,
    RSVPUpdate,
    RSVPRead,
)
from src.db.events.recordings import (
    EventRecording,
    EventRecordingCreate,
    EventRecordingRead,
)
from src.db.events.reminders import (
    EventReminder,
    EventReminderCreate,
    EventReminderRead,
)
from src.db.events.analytics import (
    EventRegistrationCount,
    EventRecordingView,
    EventRSVPSnapshot,
)
from src.db.communities.membership_plans import MembershipPlan
from src.db.communities.membership_benefits import MembershipBenefit
from src.db.communities.plan_events import PlanEvent
from src.db.usergroup_user import UserGroupUser
from src.meetings.registry import MeetingProviderRegistry
from src.meetings.base import MeetingConfig
from src.security.org_auth import require_org_membership
from src.security.auth import resolve_acting_user_id
from src.security.rbac import (
    check_resource_access,
    AccessAction,
    authorization_verify_if_user_is_anon,
    authorization_verify_based_on_org_admin_status,
)


def _now_iso() -> str:
    return datetime.now().isoformat()


async def _create_meeting_for_event(
    event: Event,
) -> Dict[str, Any]:
    if not event.meeting_provider or event.meeting_provider == "custom_url":
        return {}

    if not MeetingProviderRegistry.is_supported(event.meeting_provider):
        return {}

    provider_cls = MeetingProviderRegistry.get(event.meeting_provider)
    provider = provider_cls({})

    config = MeetingConfig(
        title=event.title,
        description=event.description,
        start_time=event.start_date,
        duration_minutes=event.duration_minutes,
        timezone=event.timezone,
    )
    meeting = await provider.create_meeting(config)
    return {
        "meeting_url": meeting.join_url,
        "provider_meeting_id": meeting.provider_meeting_id,
    }


async def create_event(
    request: Request,
    org_id: int,
    event_object: EventCreate,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> EventRead:
    await authorization_verify_if_user_is_anon(current_user.id)
    await require_org_membership(resolve_acting_user_id(current_user), org_id, db_session)

    org = (
        await db_session.execute(
            select(Organization).where(Organization.id == org_id)
        )
    ).scalars().first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    event = Event(
        title=event_object.title,
        description=event_object.description,
        cover_image=event_object.cover_image,
        event_type=event_object.event_type or "live_session",
        status=event_object.status or "scheduled",
        host_name=event_object.host_name,
        host_id=event_object.host_id,
        start_date=event_object.start_date,
        end_date=event_object.end_date,
        timezone=event_object.timezone,
        duration_minutes=event_object.duration_minutes,
        capacity=event_object.capacity,
        repeat_interval=event_object.repeat_interval or "none",
        repeat_end_date=event_object.repeat_end_date,
        recurring_rule=event_object.recurring_rule,
        meeting_url=event_object.meeting_url,
        meeting_provider=event_object.meeting_provider,
        recording_url=event_object.recording_url,
        attachments=event_object.attachments,
        visibility=event_object.visibility or "private",
        locked=event_object.locked or False,
        rsvp_enabled=event_object.rsvp_enabled if event_object.rsvp_enabled is not None else True,
        org_id=org_id,
        community_id=event_object.community_id,
        space_id=event_object.space_id,
        author_id=current_user.id,
        event_uuid=f"event_{uuid4()}",
        creation_date=_now_iso(),
        update_date=_now_iso(),
    )
    db_session.add(event)
    await db_session.commit()
    await db_session.refresh(event)

    result = await _create_meeting_for_event(event)
    if result.get("meeting_url"):
        event.meeting_url = result["meeting_url"]
        db_session.add(event)
        await db_session.commit()
        await db_session.refresh(event)

    from src.db.notifications.notifications import NotificationCreate
    from src.services.notifications.notifications import create_notification

    await create_notification(
        NotificationCreate(
            notification_type="event_reminder",
            title=f"New {event.event_type}: {event.title}",
            message=f"Scheduled for {event.start_date}",
            user_id=current_user.id,
            org_id=org_id,
            actor_id=current_user.id,
            resource_uuid=event.event_uuid,
            link="/dash/calendar",
        ),
        db_session,
    )

    return EventRead.model_validate(event.model_dump())


async def get_event(
    request: Request,
    event_uuid: str,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> EventDetailRead:
    event = (
        await db_session.execute(
            select(Event).where(Event.event_uuid == event_uuid)
        )
    ).scalars().first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    await check_resource_access(
        request, db_session, current_user, event_uuid, AccessAction.READ
    )

    detail = EventDetailRead.model_validate(event.model_dump())

    community = space = None
    rsvp_count = rsvp_user = None
    tasks = []

    if event.community_id:
        tasks.append(db_session.execute(select(Community).where(Community.id == event.community_id)))
    else:
        tasks.append(None)

    if event.space_id:
        tasks.append(db_session.execute(select(Space).where(Space.id == event.space_id)))
    else:
        tasks.append(None)

    tasks.append(
        db_session.execute(
            select(func.count(RSVP.id)).where(
                RSVP.event_id == event.id,
                RSVP.status.in_(["going", "maybe"]),
            )
        )
    )

    if not isinstance(current_user, (AnonymousUser,)):
        tasks.append(
            db_session.execute(
                select(RSVP).where(
                    RSVP.event_id == event.id,
                    RSVP.user_id == current_user.id,
                )
            )
        )

    results = await asyncio.gather(*[t for t in tasks if t is not None])

    idx = 0
    if event.community_id:
        community = results[idx].scalars().first()
        idx += 1
    if event.space_id:
        space = results[idx].scalars().first()
        idx += 1

    if community:
        detail.community_name = community.name
        detail.community_uuid = community.community_uuid

    if space:
        detail.space_name = space.name
        detail.space_uuid = space.space_uuid

    rsvp_count = results[idx].scalar() or 0
    idx += 1
    detail.attendee_count = rsvp_count

    if not isinstance(current_user, (AnonymousUser,)):
        rsvp_user = results[idx].scalars().first() if idx < len(results) else None
        if rsvp_user:
            detail.rsvp_status = rsvp_user.status

    return detail


async def get_events_by_org(
    request: Request,
    org_id: int,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
    page: int = 1,
    limit: int = 20,
    upcoming: bool = False,
    search: Optional[str] = None,
    sort_by: str = "date_asc",
    event_type: Optional[str] = None,
    community_id: Optional[int] = None,
    space_id: Optional[int] = None,
    status: Optional[str] = None,
) -> tuple[List[EventRead], int]:
    limit = min(limit, 100)
    offset = (page - 1) * limit

    statement = select(Event).where(Event.org_id == org_id)

    if event_type:
        statement = statement.where(Event.event_type == event_type)
    if community_id:
        statement = statement.where(Event.community_id == community_id)
    if space_id:
        statement = statement.where(Event.space_id == space_id)
    if status:
        statement = statement.where(Event.status == status)
    if upcoming:
        today = str(datetime.now().date())
        statement = statement.where(Event.start_date >= today)
    if search:
        statement = statement.where(Event.title.ilike(f"%{search}%"))

    count_statement = select(func.count()).select_from(statement.subquery())
    total = (await db_session.execute(count_statement)).scalar() or 0

    if sort_by == "date_asc":
        statement = statement.order_by(Event.start_date.asc(), Event.id.asc())
    elif sort_by == "date_desc":
        statement = statement.order_by(Event.start_date.desc(), Event.id.desc())
    elif sort_by == "title":
        statement = statement.order_by(Event.title.asc(), Event.id.asc())
    elif sort_by == "type":
        statement = statement.order_by(Event.event_type.asc(), Event.id.asc())

    statement = statement.offset(offset).limit(limit)
    events = (await db_session.execute(statement)).scalars().all()

    return [EventRead.model_validate(e.model_dump()) for e in events], total


async def update_event(
    request: Request,
    event_uuid: str,
    event_object: EventUpdate,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> EventRead:
    event = (
        await db_session.execute(
            select(Event).where(Event.event_uuid == event_uuid)
        )
    ).scalars().first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    await check_resource_access(
        request, db_session, current_user, event_uuid, AccessAction.UPDATE
    )

    for field, value in event_object.model_dump(exclude_none=True).items():
        setattr(event, field, value)

    event.update_date = _now_iso()
    db_session.add(event)
    await db_session.commit()
    await db_session.refresh(event)

    return EventRead.model_validate(event.model_dump())


async def delete_event(
    request: Request,
    event_uuid: str,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> dict:
    event = (
        await db_session.execute(
            select(Event).where(Event.event_uuid == event_uuid)
        )
    ).scalars().first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    await check_resource_access(
        request, db_session, current_user, event_uuid, AccessAction.DELETE
    )

    await db_session.delete(event)
    await db_session.commit()

    return {"detail": "Event deleted"}


async def get_upcoming_events(
    request: Request,
    org_id: int,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
    limit: int = 10,
) -> List[EventRead]:
    today = str(datetime.now().date())
    statement = (
        select(Event)
        .where(Event.org_id == org_id, Event.start_date >= today)
        .order_by(Event.start_date.asc())
        .limit(limit)
    )
    events = (await db_session.execute(statement)).scalars().all()
    return [EventRead.model_validate(e.model_dump()) for e in events]


# ── RSVP ──────────────────────────────────────────────────────────────────


async def rsvp_event(
    request: Request,
    event_uuid: str,
    rsvp_data: RSVPCreate,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> RSVPRead:
    await authorization_verify_if_user_is_anon(current_user.id)

    event = (
        await db_session.execute(
            select(Event).where(Event.event_uuid == event_uuid)
        )
    ).scalars().first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    if event.status == "cancelled":
        raise HTTPException(status_code=400, detail="Event is cancelled")

    await require_org_membership(resolve_acting_user_id(current_user), event.org_id, db_session)
    has_access = await check_event_membership_access(event, current_user.id, db_session)
    if not has_access:
        raise HTTPException(
            status_code=403,
            detail="This event requires a membership plan. Please subscribe to access.",
        )

    existing = (
        await db_session.execute(
            select(RSVP).where(
                RSVP.event_id == event.id,
                RSVP.user_id == current_user.id,
            )
        )
    ).scalars().first()

    capacity = event.capacity
    if capacity and rsvp_data.status in ("going", "maybe") and not existing:
        going_count = (
            await db_session.execute(
                select(func.count(RSVP.id)).where(
                    RSVP.event_id == event.id,
                    RSVP.status.in_(["going", "maybe"]),
                )
            )
        ).scalar() or 0
        if going_count >= capacity:
            rsvp_data.status = "waitlist"

    now = _now_iso()
    if existing:
        existing.status = rsvp_data.status
        existing.updated_at = now
        db_session.add(existing)
        await db_session.commit()
        await db_session.refresh(existing)
        return RSVPRead.model_validate(existing.model_dump())

    rsvp = RSVP(
        event_id=event.id,
        user_id=current_user.id,
        status=rsvp_data.status,
        created_at=now,
        updated_at=now,
    )
    db_session.add(rsvp)
    await db_session.commit()
    await db_session.refresh(rsvp)
    return RSVPRead.model_validate(rsvp.model_dump())


async def get_event_rsvps(
    request: Request,
    event_uuid: str,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> List[RSVPRead]:
    event = (
        await db_session.execute(
            select(Event).where(Event.event_uuid == event_uuid)
        )
    ).scalars().first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    await check_resource_access(
        request, db_session, current_user, event_uuid, AccessAction.READ
    )

    rsvps = (
        await db_session.execute(
            select(RSVP).where(RSVP.event_id == event.id)
        )
    ).scalars().all()
    return [RSVPRead.model_validate(r.model_dump()) for r in rsvps]


async def get_event_types() -> list:
    return EVENT_TYPES


async def get_event_statuses() -> list:
    return EVENT_STATUSES


# ── TASK 4 — RSVP: waitlist + attendance ──────────────────────────────────


async def rsvp_event_with_waitlist(
    request: Request,
    event_uuid: str,
    rsvp_data: RSVPCreate,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> RSVPRead:
    """RSVP with capacity check — auto-waitlist if event is full."""
    await authorization_verify_if_user_is_anon(current_user.id)

    event = (
        await db_session.execute(
            select(Event).where(Event.event_uuid == event_uuid)
        )
    ).scalars().first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if event.status == "cancelled":
        raise HTTPException(status_code=400, detail="Event is cancelled")

    existing = (
        await db_session.execute(
            select(RSVP).where(
                RSVP.event_id == event.id,
                RSVP.user_id == current_user.id,
            )
        )
    ).scalars().first()

    capacity = event.capacity
    if capacity and rsvp_data.status in ("going", "maybe"):
        going_count = (
            await db_session.execute(
                select(func.count(RSVP.id)).where(
                    RSVP.event_id == event.id,
                    RSVP.status.in_(["going", "maybe"]),
                )
            )
        ).scalar() or 0
        if going_count >= capacity:
            rsvp_data.status = "waitlist"

    now = _now_iso()
    if existing:
        existing.status = rsvp_data.status
        existing.updated_at = now
        db_session.add(existing)
        await db_session.commit()
        await db_session.refresh(existing)
        return RSVPRead.model_validate(existing.model_dump())

    rsvp = RSVP(
        event_id=event.id,
        user_id=current_user.id,
        status=rsvp_data.status,
        created_at=now,
        updated_at=now,
    )
    db_session.add(rsvp)
    await db_session.commit()
    await db_session.refresh(rsvp)
    return RSVPRead.model_validate(rsvp.model_dump())


async def mark_attendance(
    request: Request,
    event_uuid: str,
    user_id: int,
    attended: bool,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> RSVPRead:
    event = (
        await db_session.execute(
            select(Event).where(Event.event_uuid == event_uuid)
        )
    ).scalars().first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    await check_resource_access(
        request, db_session, current_user, event_uuid, AccessAction.UPDATE
    )

    rsvp = (
        await db_session.execute(
            select(RSVP).where(
                RSVP.event_id == event.id,
                RSVP.user_id == user_id,
            )
        )
    ).scalars().first()
    if not rsvp:
        raise HTTPException(status_code=404, detail="RSVP not found")

    rsvp.attended = attended
    rsvp.attended_at = _now_iso() if attended else None
    rsvp.updated_at = _now_iso()
    db_session.add(rsvp)
    await db_session.commit()
    await db_session.refresh(rsvp)
    return RSVPRead.model_validate(rsvp.model_dump())


# ── TASK 5 — Membership event access ──────────────────────────────────────


async def check_event_membership_access(
    event: Event,
    user_id: int,
    db_session: AsyncSession,
) -> bool:
    """Check if user has membership access to an event via their plan's usergroup."""
    plan_links = (
        await db_session.execute(
            select(PlanEvent).where(PlanEvent.event_id == event.id)
        )
    ).scalars().all()
    if not plan_links:
        return True

    plan_ids = [pl.plan_id for pl in plan_links]
    plans = (
        await db_session.execute(
            select(MembershipPlan).where(MembershipPlan.id.in_(plan_ids))
        )
    ).scalars().all()

    usergroup_ids = [plan.usergroup_id for plan in plans if plan.usergroup_id]
    if not usergroup_ids:
        return False

    membership = (
        await db_session.execute(
            select(UserGroupUser).where(
                UserGroupUser.usergroup_id.in_(usergroup_ids),
                UserGroupUser.user_id == user_id,
            ).limit(1)
        )
    ).scalars().first()
    return membership is not None


# ── TASK 6 — Calendar ─────────────────────────────────────────────────────


CALENDAR_VIEW_TYPES = ["month", "week", "agenda"]


async def get_calendar_events(
    request: Request,
    org_id: int,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
    start_date: str,
    end_date: str,
    view: str = "month",
    event_type: Optional[str] = None,
    community_id: Optional[int] = None,
    space_id: Optional[int] = None,
) -> list:
    statement = select(Event).where(
        Event.org_id == org_id,
        Event.start_date >= start_date,
        Event.start_date <= end_date,
    )
    if event_type:
        statement = statement.where(Event.event_type == event_type)
    if community_id:
        statement = statement.where(Event.community_id == community_id)
    if space_id:
        statement = statement.where(Event.space_id == space_id)

    statement = statement.order_by(Event.start_date.asc())
    events = (await db_session.execute(statement)).scalars().all()

    event_ids = [e.id for e in events]
    count_rows = (
        await db_session.execute(
            select(RSVP.event_id, func.count(RSVP.id))
            .where(
                RSVP.event_id.in_(event_ids),
                RSVP.status.in_(["going", "maybe"]),
            )
            .group_by(RSVP.event_id)
        )
    ).all()
    count_by_event = {row[0]: row[1] for row in count_rows}

    results = []
    for e in events:
        detail = EventDetailRead.model_validate(e.model_dump())
        detail.attendee_count = count_by_event.get(e.id, 0)
        results.append(detail)

    return results


# ── TASK 7 — Reminders ────────────────────────────────────────────────────


async def create_event_reminder(
    request: Request,
    event_uuid: str,
    reminder_data: EventReminderCreate,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> EventReminderRead:
    await authorization_verify_if_user_is_anon(current_user.id)

    event = (
        await db_session.execute(
            select(Event).where(Event.event_uuid == event_uuid)
        )
    ).scalars().first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    reminder = EventReminder(
        event_id=event.id,
        user_id=reminder_data.user_id,
        org_id=reminder_data.org_id,
        remind_at=reminder_data.remind_at,
        channel=reminder_data.channel or "both",
        status="pending",
        created_at=_now_iso(),
        updated_at=_now_iso(),
    )
    db_session.add(reminder)
    await db_session.commit()
    await db_session.refresh(reminder)
    return EventReminderRead.model_validate(reminder.model_dump())


async def get_event_reminders(
    request: Request,
    event_uuid: str,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> list:
    event = (
        await db_session.execute(
            select(Event).where(Event.event_uuid == event_uuid)
        )
    ).scalars().first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    await check_resource_access(
        request, db_session, current_user, event_uuid, AccessAction.READ
    )

    reminders = (
        await db_session.execute(
            select(EventReminder).where(EventReminder.event_id == event.id)
        )
    ).scalars().all()
    return [EventReminderRead.model_validate(r.model_dump()) for r in reminders]


async def get_user_reminders(
    request: Request,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
    status: Optional[str] = None,
) -> list:
    await authorization_verify_if_user_is_anon(current_user.id)

    statement = select(EventReminder).where(
        EventReminder.user_id == current_user.id
    )
    if status:
        statement = statement.where(EventReminder.status == status)

    statement = statement.order_by(EventReminder.remind_at.asc())
    reminders = (await db_session.execute(statement)).scalars().all()
    return [EventReminderRead.model_validate(r.model_dump()) for r in reminders]


async def schedule_reminders_for_event(
    event: Event,
    db_session: AsyncSession,
) -> list:
    """Auto-schedule 1-hour-before reminders for all 'going' RSVPs."""
    rsvps = (
        await db_session.execute(
            select(RSVP).where(
                RSVP.event_id == event.id,
                RSVP.status == "going",
            )
        )
    ).scalars().all()

    from datetime import timedelta
    from datetime import datetime as dt

    created = []
    try:
        event_dt = dt.fromisoformat(event.start_date)
    except (ValueError, TypeError):
        return []

    for rsvp_entry in rsvps:
        remind_at = (event_dt - timedelta(hours=1)).isoformat()
        reminder = EventReminder(
            event_id=event.id,
            user_id=rsvp_entry.user_id,
            org_id=event.org_id,
            remind_at=remind_at,
            channel="both",
            status="pending",
            created_at=_now_iso(),
            updated_at=_now_iso(),
        )
        db_session.add(reminder)
        created.append(reminder)

    if created:
        await db_session.commit()

    return [EventReminderRead.model_validate(r.model_dump()) for r in created]


# ── TASK 8 — Recordings ───────────────────────────────────────────────────


async def create_recording(
    request: Request,
    recording_data: EventRecordingCreate,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> EventRecordingRead:
    await authorization_verify_if_user_is_anon(current_user.id)

    event = (
        await db_session.execute(
            select(Event).where(Event.id == recording_data.event_id)
        )
    ).scalars().first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    recording = EventRecording(
        event_id=recording_data.event_id,
        org_id=recording_data.org_id,
        recording_type=recording_data.recording_type or "recording",
        title=recording_data.title,
        description=recording_data.description,
        file_url=recording_data.file_url,
        file_size=recording_data.file_size,
        file_mime=recording_data.file_mime,
        thumbnail_url=recording_data.thumbnail_url,
        duration_seconds=recording_data.duration_seconds,
        course_id=recording_data.course_id,
        activity_id=recording_data.activity_id,
        metadata=recording_data.metadata,
        created_at=_now_iso(),
        updated_at=_now_iso(),
    )
    db_session.add(recording)
    await db_session.commit()
    await db_session.refresh(recording)
    return EventRecordingRead.model_validate(recording.model_dump())


async def get_event_recordings(
    request: Request,
    event_uuid: str,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
    recording_type: Optional[str] = None,
) -> list:
    event = (
        await db_session.execute(
            select(Event).where(Event.event_uuid == event_uuid)
        )
    ).scalars().first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    await check_resource_access(
        request, db_session, current_user, event_uuid, AccessAction.READ
    )

    statement = select(EventRecording).where(
        EventRecording.event_id == event.id
    )
    if recording_type:
        statement = statement.where(
            EventRecording.recording_type == recording_type
        )

    recordings = (await db_session.execute(statement)).scalars().all()
    return [EventRecordingRead.model_validate(r.model_dump()) for r in recordings]


async def update_recording(
    request: Request,
    recording_id: int,
    update_data: dict,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> EventRecordingRead:
    recording = (
        await db_session.execute(
            select(EventRecording).where(EventRecording.id == recording_id)
        )
    ).scalars().first()
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")

    event = (
        await db_session.execute(
            select(Event).where(Event.id == recording.event_id)
        )
    ).scalars().first()
    if event:
        await check_resource_access(
            request, db_session, current_user, event.event_uuid, AccessAction.UPDATE
        )

    for field, value in update_data.items():
        if value is not None:
            setattr(recording, field, value)

    recording.updated_at = _now_iso()
    db_session.add(recording)
    await db_session.commit()
    await db_session.refresh(recording)
    return EventRecordingRead.model_validate(recording.model_dump())


async def delete_recording(
    request: Request,
    recording_id: int,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> dict:
    recording = (
        await db_session.execute(
            select(EventRecording).where(EventRecording.id == recording_id)
        )
    ).scalars().first()
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")

    event = (
        await db_session.execute(
            select(Event).where(Event.id == recording.event_id)
        )
    ).scalars().first()
    if event:
        await check_resource_access(
            request, db_session, current_user, event.event_uuid, AccessAction.UPDATE
        )

    await db_session.delete(recording)
    await db_session.commit()
    return {"detail": "Recording deleted"}


# ── TASK 9 — Analytics ────────────────────────────────────────────────────


async def get_event_registration_counts(
    request: Request,
    event_uuid: str,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> dict:
    event = (
        await db_session.execute(
            select(Event).where(Event.event_uuid == event_uuid)
        )
    ).scalars().first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    await check_resource_access(
        request, db_session, current_user, event_uuid, AccessAction.READ
    )

    rsvps = (
        await db_session.execute(
            select(RSVP).where(RSVP.event_id == event.id)
        )
    ).scalars().all()

    total = len(rsvps)
    going = sum(1 for r in rsvps if r.status == "going")
    maybe = sum(1 for r in rsvps if r.status == "maybe")
    waitlist = sum(1 for r in rsvps if r.status == "waitlist")
    not_going = sum(1 for r in rsvps if r.status == "not_going")
    attended = sum(1 for r in rsvps if r.attended)

    return {
        "total_rsvps": total,
        "going": going,
        "maybe": maybe,
        "waitlist": waitlist,
        "not_going": not_going,
        "attended": attended,
        "attendance_rate": round(attended / going * 100, 1) if going else 0.0,
    }


async def track_recording_view(
    request: Request,
    recording_id: int,
    watch_seconds: int,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> dict:
    await authorization_verify_if_user_is_anon(current_user.id)

    recording = (
        await db_session.execute(
            select(EventRecording).where(EventRecording.id == recording_id)
        )
    ).scalars().first()
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")

    view = EventRecordingView(
        recording_id=recording_id,
        user_id=current_user.id,
        org_id=recording.org_id,
        watch_seconds=watch_seconds,
        viewed_at=_now_iso(),
        created_at=_now_iso(),
    )
    db_session.add(view)
    await db_session.commit()
    await db_session.refresh(view)
    return {"id": view.id, "watch_seconds": view.watch_seconds, "viewed_at": view.viewed_at}


async def get_recording_views(
    request: Request,
    recording_id: int,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> dict:
    recording = (
        await db_session.execute(
            select(EventRecording).where(EventRecording.id == recording_id)
        )
    ).scalars().first()
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")

    views = (
        await db_session.execute(
            select(EventRecordingView).where(
                EventRecordingView.recording_id == recording_id
            )
        )
    ).scalars().all()

    total_views = len(views)
    unique_users = len(set(v.user_id for v in views))
    total_watch_seconds = sum(v.watch_seconds for v in views)

    return {
        "total_views": total_views,
        "unique_users": unique_users,
        "total_watch_seconds": total_watch_seconds,
        "average_watch_seconds": round(total_watch_seconds / total_views, 1) if total_views else 0,
    }
