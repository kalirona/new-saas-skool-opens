from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Request, Query
from pydantic import BaseModel
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.events.database import get_db_session
from src.db.users import PublicUser
from src.db.events.events import EventRead, EventDetailRead
from src.db.events.rsvps import RSVPCreate, RSVPRead
from src.db.events.recordings import EventRecordingCreate, EventRecordingRead
from src.db.events.reminders import EventReminderCreate, EventReminderRead
from src.security.auth import get_current_user
from src.services.events.events import (
    create_event,
    get_event,
    get_events_by_org,
    update_event,
    delete_event,
    get_upcoming_events,
    rsvp_event,
    get_event_rsvps,
    get_event_types,
    get_event_statuses,
    mark_attendance,
    get_calendar_events,
    create_event_reminder,
    get_event_reminders,
    get_user_reminders,
    create_recording,
    get_event_recordings,
    update_recording,
    delete_recording,
    get_event_registration_counts,
    track_recording_view,
    get_recording_views,
)


router = APIRouter()


class EventCreateRequest(BaseModel):
    title: str
    description: Optional[str] = None
    cover_image: Optional[str] = None
    event_type: str = "live_session"
    status: str = "scheduled"
    host_name: Optional[str] = None
    host_id: Optional[int] = None
    start_date: str
    end_date: Optional[str] = None
    timezone: Optional[str] = None
    duration_minutes: Optional[int] = None
    capacity: Optional[int] = None
    repeat_interval: str = "none"
    repeat_end_date: Optional[str] = None
    recurring_rule: Optional[str] = None
    meeting_url: Optional[str] = None
    meeting_provider: Optional[str] = None
    recording_url: Optional[str] = None
    attachments: Optional[Dict[str, Any]] = None
    visibility: str = "private"
    locked: bool = False
    rsvp_enabled: bool = True
    community_id: Optional[int] = None
    space_id: Optional[int] = None


class EventUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    cover_image: Optional[str] = None
    event_type: Optional[str] = None
    status: Optional[str] = None
    host_name: Optional[str] = None
    host_id: Optional[int] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    timezone: Optional[str] = None
    duration_minutes: Optional[int] = None
    capacity: Optional[int] = None
    repeat_interval: Optional[str] = None
    repeat_end_date: Optional[str] = None
    recurring_rule: Optional[str] = None
    meeting_url: Optional[str] = None
    meeting_provider: Optional[str] = None
    recording_url: Optional[str] = None
    attachments: Optional[Dict[str, Any]] = None
    visibility: Optional[str] = None
    locked: Optional[bool] = None
    rsvp_enabled: Optional[bool] = None
    community_id: Optional[int] = None
    space_id: Optional[int] = None


class AttendanceMarkRequest(BaseModel):
    user_id: int
    attended: bool


class RecordingUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    file_url: Optional[str] = None
    file_size: Optional[int] = None
    file_mime: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration_seconds: Optional[int] = None
    course_id: Optional[int] = None
    activity_id: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class TrackViewRequest(BaseModel):
    watch_seconds: int = 0


@router.get(
    "/events/types",
    summary="List supported event types",
)
async def api_get_event_types():
    return await get_event_types()


@router.get(
    "/events/statuses",
    summary="List supported event statuses",
)
async def api_get_event_statuses():
    return await get_event_statuses()


@router.get(
    "/events/org/{org_id}",
    response_model=dict,
    summary="List events for an organization",
)
async def api_get_events_by_org(
    request: Request,
    org_id: int,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    upcoming: bool = Query(default=False),
    search: Optional[str] = Query(default=None),
    sort_by: str = Query(default="date_asc"),
    event_type: Optional[str] = Query(default=None),
    community_id: Optional[int] = Query(default=None),
    space_id: Optional[int] = Query(default=None),
    status: Optional[str] = Query(default=None),
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> dict:
    events, total = await get_events_by_org(
        request, org_id, current_user, db_session,
        page=page, limit=limit, upcoming=upcoming,
        search=search, sort_by=sort_by,
        event_type=event_type, community_id=community_id,
        space_id=space_id, status=status,
    )
    return {"events": events, "total": total, "page": page, "limit": limit}


@router.get(
    "/events/org/{org_id}/upcoming",
    response_model=List[EventRead],
    summary="Get upcoming events for widget",
)
async def api_get_upcoming_events(
    request: Request,
    org_id: int,
    limit: int = Query(default=5, ge=1, le=20),
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> List[EventRead]:
    return await get_upcoming_events(request, org_id, current_user, db_session, limit)


@router.post(
    "/events/org/{org_id}",
    response_model=EventRead,
    summary="Create a new event",
)
async def api_create_event(
    request: Request,
    org_id: int,
    event_data: EventCreateRequest,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> EventRead:
    from src.db.events.events import EventCreate
    ec = EventCreate(**event_data.model_dump())
    ec.org_id = org_id
    ec.author_id = current_user.id
    return await create_event(request, org_id, ec, current_user, db_session)


@router.get(
    "/events/{event_uuid}",
    response_model=EventDetailRead,
    summary="Get a single event with detail",
)
async def api_get_event(
    request: Request,
    event_uuid: str,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> EventDetailRead:
    return await get_event(request, event_uuid, current_user, db_session)


@router.put(
    "/events/{event_uuid}",
    response_model=EventRead,
    summary="Update an event",
)
async def api_update_event(
    request: Request,
    event_uuid: str,
    event_data: EventUpdateRequest,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> EventRead:
    from src.db.events.events import EventUpdate
    eu = EventUpdate(**event_data.model_dump(exclude_none=True))
    return await update_event(request, event_uuid, eu, current_user, db_session)


@router.delete(
    "/events/{event_uuid}",
    summary="Delete an event",
)
async def api_delete_event(
    request: Request,
    event_uuid: str,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> dict:
    return await delete_event(request, event_uuid, current_user, db_session)


# ── TASK 4 — RSVP ─────────────────────────────────────────────────────────


@router.post(
    "/events/{event_uuid}/rsvp",
    response_model=RSVPRead,
    summary="RSVP to an event (with auto-waitlist if capacity reached & membership check)",
)
async def api_rsvp_event(
    request: Request,
    event_uuid: str,
    rsvp_data: RSVPCreate,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> RSVPRead:
    return await rsvp_event(request, event_uuid, rsvp_data, current_user, db_session)


@router.get(
    "/events/{event_uuid}/rsvps",
    response_model=List[RSVPRead],
    summary="List RSVPs for an event",
)
async def api_get_event_rsvps(
    request: Request,
    event_uuid: str,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> List[RSVPRead]:
    return await get_event_rsvps(request, event_uuid, current_user, db_session)


@router.put(
    "/events/{event_uuid}/attendance",
    summary="Mark a user's attendance for an event",
)
async def api_mark_attendance(
    request: Request,
    event_uuid: str,
    body: AttendanceMarkRequest,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> RSVPRead:
    return await mark_attendance(request, event_uuid, body.user_id, body.attended, current_user, db_session)


# ── TASK 6 — Calendar ─────────────────────────────────────────────────────


@router.get(
    "/events/org/{org_id}/calendar",
    summary="Calendar view for events (month/week/agenda)",
)
async def api_get_calendar(
    request: Request,
    org_id: int,
    start_date: str = Query(...),
    end_date: str = Query(...),
    view: str = Query(default="month"),
    event_type: Optional[str] = Query(default=None),
    community_id: Optional[int] = Query(default=None),
    space_id: Optional[int] = Query(default=None),
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> dict:
    events = await get_calendar_events(
        request, org_id, current_user, db_session,
        start_date=start_date, end_date=end_date, view=view,
        event_type=event_type, community_id=community_id, space_id=space_id,
    )
    return {"events": events, "view": view, "start_date": start_date, "end_date": end_date}


# ── TASK 7 — Reminders ────────────────────────────────────────────────────


@router.post(
    "/events/{event_uuid}/reminders",
    response_model=EventReminderRead,
    summary="Create a reminder for an event",
)
async def api_create_reminder(
    request: Request,
    event_uuid: str,
    reminder_data: EventReminderCreate,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> EventReminderRead:
    return await create_event_reminder(request, event_uuid, reminder_data, current_user, db_session)


@router.get(
    "/events/{event_uuid}/reminders",
    summary="List reminders for an event",
)
async def api_get_reminders(
    request: Request,
    event_uuid: str,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> list:
    return await get_event_reminders(request, event_uuid, current_user, db_session)


@router.get(
    "/reminders",
    summary="List reminders for the current user",
)
async def api_get_user_reminders(
    request: Request,
    status: Optional[str] = Query(default=None),
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> list:
    return await get_user_reminders(request, current_user, db_session, status=status)


# ── TASK 8 — Recordings ───────────────────────────────────────────────────


@router.post(
    "/events/recordings",
    response_model=EventRecordingRead,
    summary="Attach a recording/slides/resource to an event",
)
async def api_create_recording(
    request: Request,
    recording_data: EventRecordingCreate,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> EventRecordingRead:
    return await create_recording(request, recording_data, current_user, db_session)


@router.get(
    "/events/{event_uuid}/recordings",
    summary="List recordings for an event",
)
async def api_get_recordings(
    request: Request,
    event_uuid: str,
    recording_type: Optional[str] = Query(default=None),
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> list:
    return await get_event_recordings(request, event_uuid, current_user, db_session, recording_type=recording_type)


@router.put(
    "/events/recordings/{recording_id}",
    response_model=EventRecordingRead,
    summary="Update a recording",
)
async def api_update_recording(
    request: Request,
    recording_id: int,
    update_data: RecordingUpdateRequest,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> EventRecordingRead:
    return await update_recording(request, recording_id, update_data.model_dump(exclude_none=True), current_user, db_session)


@router.delete(
    "/events/recordings/{recording_id}",
    summary="Delete a recording",
)
async def api_delete_recording(
    request: Request,
    recording_id: int,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> dict:
    return await delete_recording(request, recording_id, current_user, db_session)


# ── TASK 9 — Analytics ────────────────────────────────────────────────────


@router.get(
    "/events/{event_uuid}/analytics/registrations",
    summary="Registration & attendance analytics for an event",
)
async def api_get_registration_analytics(
    request: Request,
    event_uuid: str,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> dict:
    return await get_event_registration_counts(request, event_uuid, current_user, db_session)


@router.post(
    "/events/recordings/{recording_id}/views",
    summary="Track a recording view",
)
async def api_track_recording_view(
    request: Request,
    recording_id: int,
    body: TrackViewRequest,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> dict:
    return await track_recording_view(request, recording_id, body.watch_seconds, current_user, db_session)


@router.get(
    "/events/recordings/{recording_id}/views",
    summary="Get recording view analytics",
)
async def api_get_recording_views(
    request: Request,
    recording_id: int,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> dict:
    return await get_recording_views(request, recording_id, current_user, db_session)
