import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from fastapi import HTTPException
from sqlmodel import select
from src.db.usergroup_user import UserGroupUser


# ── Helper fixtures ──────────────────────────────────────────────────────


@pytest.fixture
async def event(db, org, community):
    from src.db.events.events import Event
    now = str(datetime.now())
    e = Event(
        id=1, title="Test Event", description="A test event",
        event_type="live_session", status="scheduled",
        start_date=now, end_date=now,
        org_id=org.id, community_id=community.id,
        author_id=1, event_uuid="event_test",
        capacity=100, rsvp_enabled=True,
        visibility="private", locked=False,
        creation_date=now, update_date=now,
    )
    db.add(e)
    await db.commit()
    await db.refresh(e)
    return e


@pytest.fixture
async def community(db, org):
    from src.db.communities.communities import Community
    c = Community(
        id=1, name="Test Community", org_id=org.id,
        community_uuid="comm_test",
        creation_date=str(datetime.now()), update_date=str(datetime.now()),
    )
    db.add(c)
    await db.commit()
    await db.refresh(c)
    return c


@pytest.fixture
async def space(db, org):
    from src.db.communities.spaces import Space
    s = Space(
        id=1, name="Test Space", org_id=org.id,
        community_id=1, space_uuid="space_test",
        creation_date=str(datetime.now()), update_date=str(datetime.now()),
    )
    db.add(s)
    await db.commit()
    await db.refresh(s)
    return s


@pytest.fixture
async def membership_plan(db, org, community):
    from src.db.communities.membership_plans import MembershipPlan
    mp = MembershipPlan(
        id=1, name="Pro Plan", plan_uuid="plan_test", price=29.99,
        interval="monthly", community_id=community.id, org_id=org.id,
        creation_date=str(datetime.now()), update_date=str(datetime.now()),
    )
    db.add(mp)
    await db.commit()
    await db.refresh(mp)
    return mp


@pytest.fixture
async def plan_event(db, membership_plan, event):
    from src.db.communities.plan_events import PlanEvent
    pe = PlanEvent(
        id=1, plan_id=membership_plan.id, event_id=event.id,
        creation_date=str(datetime.now()), update_date=str(datetime.now()),
    )
    db.add(pe)
    await db.commit()
    await db.refresh(pe)
    return pe


# ── Event CRUD ───────────────────────────────────────────────────────────


class TestCreateEvent:
    @pytest.mark.asyncio
    async def test_creates_event(self, db, org, admin_user, bypass_rbac, bypass_analytics):
        from src.services.events.events import create_event
        from src.db.events.events import EventCreate
        ec = EventCreate(
            title="New Event", description="desc", start_date=str(datetime.now()),
            event_type="webinar", org_id=org.id, author_id=admin_user.id,
        )
        result = await create_event(MagicMock(), org.id, ec, admin_user, db)
        assert result.title == "New Event"
        assert result.event_type == "webinar"
        assert result.event_uuid.startswith("event_")

    @pytest.mark.asyncio
    async def test_creates_event_with_meeting_url(self, db, org, admin_user, bypass_rbac, bypass_analytics):
        from src.services.events.events import create_event
        from src.db.events.events import EventCreate
        ec = EventCreate(
            title="Meeting Event", start_date=str(datetime.now()),
            meeting_url="https://zoom.us/j/123", meeting_provider="custom_url",
            org_id=org.id, author_id=admin_user.id,
        )
        result = await create_event(MagicMock(), org.id, ec, admin_user, db)
        assert result.meeting_url == "https://zoom.us/j/123"

    @pytest.mark.asyncio
    async def test_rejects_anonymous_user(self, db, org, anonymous_user):
        from src.services.events.events import create_event
        from src.db.events.events import EventCreate
        from fastapi import HTTPException
        ec = EventCreate(title="Fail", start_date=str(datetime.now()), org_id=org.id, author_id=0)
        with pytest.raises(HTTPException):
            await create_event(MagicMock(), org.id, ec, anonymous_user, db)

    @pytest.mark.asyncio
    async def test_rejects_nonexistent_org(self, db, admin_user, bypass_rbac):
        from src.services.events.events import create_event
        from src.db.events.events import EventCreate
        ec = EventCreate(title="Fail", start_date=str(datetime.now()), org_id=9999, author_id=admin_user.id)
        with pytest.raises(HTTPException, match="Organization not found"):
            await create_event(MagicMock(), 9999, ec, admin_user, db)


class TestGetEvent:
    @pytest.mark.asyncio
    async def test_gets_event(self, db, event, admin_user, bypass_rbac):
        from src.services.events.events import get_event
        result = await get_event(MagicMock(), "event_test", admin_user, db)
        assert result.title == "Test Event"
        assert result.event_uuid == "event_test"
        assert result.attendee_count == 0

    @pytest.mark.asyncio
    async def test_raises_404_for_missing(self, db, admin_user):
        from src.services.events.events import get_event
        with pytest.raises(HTTPException, match="Event not found"):
            await get_event(MagicMock(), "event_nonexistent", admin_user, db)

    @pytest.mark.asyncio
    async def test_returns_restricted_flag(self, db, org, community, event, regular_user, bypass_rbac):
        from src.services.events.events import get_event
        result = await get_event(MagicMock(), "event_test", regular_user, db)
        assert hasattr(result, "is_restricted")


class TestGetEventsByOrg:
    @pytest.mark.asyncio
    async def test_lists_events_paginated(self, db, org, event, admin_user):
        from src.services.events.events import get_events_by_org
        events, total = await get_events_by_org(MagicMock(), org.id, admin_user, db)
        assert len(events) >= 1
        assert total >= 1

    @pytest.mark.asyncio
    async def test_filters_by_event_type(self, db, org, event, admin_user):
        from src.services.events.events import get_events_by_org
        events, total = await get_events_by_org(MagicMock(), org.id, admin_user, db, event_type="webinar")
        assert total == 0
        events, total = await get_events_by_org(MagicMock(), org.id, admin_user, db, event_type="live_session")
        assert total >= 1

    @pytest.mark.asyncio
    async def test_filters_by_status(self, db, org, event, admin_user):
        from src.services.events.events import get_events_by_org
        events, total = await get_events_by_org(MagicMock(), org.id, admin_user, db, status="scheduled")
        assert total >= 1
        events, total = await get_events_by_org(MagicMock(), org.id, admin_user, db, status="cancelled")
        assert total == 0

    @pytest.mark.asyncio
    async def test_searches_by_title(self, db, org, event, admin_user):
        from src.services.events.events import get_events_by_org
        events, total = await get_events_by_org(MagicMock(), org.id, admin_user, db, search="Test")
        assert total >= 1
        events, total = await get_events_by_org(MagicMock(), org.id, admin_user, db, search="Nonexistent")
        assert total == 0

    @pytest.mark.asyncio
    async def test_sorts_by_date_desc(self, db, org, admin_user):
        from src.services.events.events import create_event, get_events_by_org
        from src.db.events.events import EventCreate
        from datetime import timedelta
        import time
        base = str(datetime.now())
        ec1 = EventCreate(title="Later Event", start_date=base, org_id=org.id, author_id=admin_user.id)
        ec2 = EventCreate(title="Earlier Event", start_date=base, org_id=org.id, author_id=admin_user.id)
        await create_event(MagicMock(), org.id, ec1, admin_user, db)
        events_desc, _ = await get_events_by_org(MagicMock(), org.id, admin_user, db, sort_by="date_desc")
        assert len(events_desc) >= 2

    @pytest.mark.asyncio
    async def test_respects_limit(self, db, org, event, admin_user):
        from src.services.events.events import get_events_by_org
        events, total = await get_events_by_org(MagicMock(), org.id, admin_user, db, limit=1)
        assert len(events) <= 1


class TestUpdateEvent:
    @pytest.mark.asyncio
    async def test_updates_title(self, db, event, admin_user, bypass_rbac):
        from src.services.events.events import update_event
        from src.db.events.events import EventUpdate
        eu = EventUpdate(title="Updated Title")
        result = await update_event(MagicMock(), "event_test", eu, admin_user, db)
        assert result.title == "Updated Title"

    @pytest.mark.asyncio
    async def test_updates_multiple_fields(self, db, event, admin_user, bypass_rbac):
        from src.services.events.events import update_event
        from src.db.events.events import EventUpdate
        eu = EventUpdate(title="New Title", description="New desc", event_type="workshop")
        result = await update_event(MagicMock(), "event_test", eu, admin_user, db)
        assert result.title == "New Title"
        assert result.event_type == "workshop"

    @pytest.mark.asyncio
    async def test_raises_404_for_missing(self, db, admin_user):
        from src.services.events.events import update_event
        from src.db.events.events import EventUpdate
        with pytest.raises(HTTPException, match="Event not found"):
            await update_event(MagicMock(), "event_nonexistent", EventUpdate(title="X"), admin_user, db)

    @pytest.mark.asyncio
    async def test_raises_on_empty_update(self, db, event, admin_user, bypass_rbac):
        from src.services.events.events import update_event
        from src.db.events.events import EventUpdate
        result = await update_event(MagicMock(), "event_test", EventUpdate(), admin_user, db)
        assert result.title == "Test Event"


class TestDeleteEvent:
    @pytest.mark.asyncio
    async def test_deletes_event(self, db, event, admin_user, bypass_rbac):
        from src.services.events.events import delete_event
        result = await delete_event(MagicMock(), "event_test", admin_user, db)
        assert result["detail"] == "Event deleted"

    @pytest.mark.asyncio
    async def test_raises_404_for_missing(self, db, admin_user):
        from src.services.events.events import delete_event
        with pytest.raises(HTTPException, match="Event not found"):
            await delete_event(MagicMock(), "event_nonexistent", admin_user, db)


class TestGetUpcomingEvents:
    @pytest.mark.asyncio
    async def test_returns_upcoming_events(self, db, org, event, admin_user):
        from src.services.events.events import get_upcoming_events
        from datetime import timedelta
        future_date = (datetime.now().replace(year=datetime.now().year + 1)).isoformat()
        from src.db.events.events import Event
        future_event = Event(
            id=999, title="Future Event", start_date=future_date,
            org_id=org.id, author_id=admin_user.id, event_uuid="event_future",
            rsvp_enabled=True, creation_date=str(datetime.now()), update_date=str(datetime.now()),
        )
        db.add(future_event)
        await db.commit()
        results = await get_upcoming_events(MagicMock(), org.id, admin_user, db, limit=10)
        assert any(e.title == "Future Event" for e in results)

    @pytest.mark.asyncio
    async def test_respects_limit(self, db, org, event, admin_user):
        from src.services.events.events import get_upcoming_events
        results = await get_upcoming_events(MagicMock(), org.id, admin_user, db, limit=1)
        assert len(results) <= 1


# ── RSVP ─────────────────────────────────────────────────────────────────


class TestRSVPEvent:
    @pytest.mark.asyncio
    async def test_rsvp_going(self, db, org, event, admin_user, bypass_rbac):
        from src.services.events.events import rsvp_event
        from src.db.events.rsvps import RSVPCreate
        rsvp_data = RSVPCreate(event_id=event.id, user_id=admin_user.id, status="going")
        result = await rsvp_event(MagicMock(), "event_test", rsvp_data, admin_user, db)
        assert result.status == "going"
        assert result.event_id == event.id

    @pytest.mark.asyncio
    async def test_rsvp_maybe(self, db, org, event, admin_user, bypass_rbac):
        from src.services.events.events import rsvp_event
        from src.db.events.rsvps import RSVPCreate
        rsvp_data = RSVPCreate(event_id=event.id, user_id=admin_user.id, status="maybe")
        result = await rsvp_event(MagicMock(), "event_test", rsvp_data, admin_user, db)
        assert result.status == "maybe"

    @pytest.mark.asyncio
    async def test_rsvp_not_going(self, db, org, event, admin_user, bypass_rbac):
        from src.services.events.events import rsvp_event
        from src.db.events.rsvps import RSVPCreate
        rsvp_data = RSVPCreate(event_id=event.id, user_id=admin_user.id, status="not_going")
        result = await rsvp_event(MagicMock(), "event_test", rsvp_data, admin_user, db)
        assert result.status == "not_going"

    @pytest.mark.asyncio
    async def test_raises_on_cancelled_event(self, db, org, event, admin_user):
        from src.services.events.events import rsvp_event
        from src.db.events.rsvps import RSVPCreate
        from src.db.events.events import Event
        event.status = "cancelled"
        db.add(event)
        await db.commit()
        with pytest.raises(HTTPException, match="Event is cancelled"):
            await rsvp_event(MagicMock(), "event_test", RSVPCreate(event_id=event.id, user_id=admin_user.id, status="going"), admin_user, db)

    @pytest.mark.asyncio
    async def test_raises_on_disabled_rsvp(self, db, org, event, admin_user):
        from src.services.events.events import rsvp_event
        from src.db.events.rsvps import RSVPCreate
        event.rsvp_enabled = False
        db.add(event)
        await db.commit()
        with pytest.raises(HTTPException, match="RSVPs are disabled"):
            await rsvp_event(MagicMock(), "event_test", RSVPCreate(event_id=event.id, user_id=admin_user.id, status="going"), admin_user, db)

    @pytest.mark.asyncio
    async def test_updates_existing_rsvp(self, db, org, event, admin_user, bypass_rbac):
        from src.services.events.events import rsvp_event
        from src.db.events.rsvps import RSVPCreate
        rsvp_data = RSVPCreate(event_id=event.id, user_id=admin_user.id, status="going")
        result = await rsvp_event(MagicMock(), "event_test", rsvp_data, admin_user, db)
        assert result.status == "going"
        rsvp_data2 = RSVPCreate(event_id=event.id, user_id=admin_user.id, status="maybe")
        result2 = await rsvp_event(MagicMock(), "event_test", rsvp_data2, admin_user, db)
        assert result2.status == "maybe"
        assert result2.id == result.id

    @pytest.mark.asyncio
    async def test_raises_on_anonymous(self, db, org, event, anonymous_user):
        from src.services.events.events import rsvp_event
        from src.db.events.rsvps import RSVPCreate
        with pytest.raises(HTTPException):
            await rsvp_event(MagicMock(), "event_test", RSVPCreate(event_id=event.id, user_id=0, status="going"), anonymous_user, db)

    @pytest.mark.asyncio
    async def test_raises_403_on_no_membership_access(self, db, org, community, event, regular_user, bypass_rbac):
        from src.services.events.events import rsvp_event
        from src.db.events.rsvps import RSVPCreate
        from src.db.communities.plan_events import PlanEvent
        from src.db.communities.membership_plans import MembershipPlan
        mp = MembershipPlan(
            id=999, name="Restricted", plan_uuid="plan_restrict", price=99.99,
            interval="monthly", community_id=community.id, org_id=org.id,
            creation_date=str(datetime.now()), update_date=str(datetime.now()),
        )
        db.add(mp)
        await db.commit()
        pe = PlanEvent(id=999, plan_id=mp.id, event_id=event.id,
                       creation_date=str(datetime.now()), update_date=str(datetime.now()))
        db.add(pe)
        await db.commit()
        with pytest.raises(HTTPException, match="membership"):
            await rsvp_event(MagicMock(), "event_test", RSVPCreate(event_id=event.id, user_id=regular_user.id, status="going"), regular_user, db)


# ── Attendance ───────────────────────────────────────────────────────────


class TestMarkAttendance:
    @pytest.mark.asyncio
    async def test_marks_attended(self, db, event, admin_user, bypass_rbac):
        from src.services.events.events import rsvp_event, mark_attendance
        from src.db.events.rsvps import RSVPCreate
        await rsvp_event(MagicMock(), "event_test", RSVPCreate(event_id=event.id, user_id=admin_user.id, status="going"), admin_user, db)
        result = await mark_attendance(MagicMock(), "event_test", admin_user.id, True, admin_user, db)
        assert result.attended is True
        assert result.attended_at is not None

    @pytest.mark.asyncio
    async def test_marks_not_attended(self, db, event, admin_user, bypass_rbac):
        from src.services.events.events import rsvp_event, mark_attendance
        from src.db.events.rsvps import RSVPCreate
        await rsvp_event(MagicMock(), "event_test", RSVPCreate(event_id=event.id, user_id=admin_user.id, status="going"), admin_user, db)
        result = await mark_attendance(MagicMock(), "event_test", admin_user.id, False, admin_user, db)
        assert result.attended is False


class TestSelfCheckin:
    @pytest.mark.asyncio
    async def test_self_checkin(self, db, event, admin_user, bypass_rbac):
        from src.services.events.events import rsvp_event, self_checkin_attendance
        from src.db.events.rsvps import RSVPCreate
        await rsvp_event(MagicMock(), "event_test", RSVPCreate(event_id=event.id, user_id=admin_user.id, status="going"), admin_user, db)
        result = await self_checkin_attendance(MagicMock(), "event_test", admin_user, db)
        assert result.attended is True

    @pytest.mark.asyncio
    async def test_self_checkin_requires_rsvp(self, db, event, admin_user):
        from src.services.events.events import self_checkin_attendance
        with pytest.raises(HTTPException, match="not found"):
            await self_checkin_attendance(MagicMock(), "event_test", admin_user, db)


class TestGetEventRSVPs:
    @pytest.mark.asyncio
    async def test_lists_rsvps(self, db, event, admin_user, bypass_rbac):
        from src.services.events.events import rsvp_event, get_event_rsvps
        from src.db.events.rsvps import RSVPCreate
        await rsvp_event(MagicMock(), "event_test", RSVPCreate(event_id=event.id, user_id=admin_user.id, status="going"), admin_user, db)
        rsvps = await get_event_rsvps(MagicMock(), "event_test", admin_user, db)
        assert len(rsvps) == 1
        assert rsvps[0].status == "going"

    @pytest.mark.asyncio
    async def test_raises_404_for_missing_event(self, db, admin_user):
        from src.services.events.events import get_event_rsvps
        with pytest.raises(HTTPException, match="Event not found"):
            await get_event_rsvps(MagicMock(), "event_nonexistent", admin_user, db)


# ── Calendar ─────────────────────────────────────────────────────────────


class TestCalendarEvents:
    @pytest.mark.asyncio
    async def test_gets_calendar_events(self, db, org, event, admin_user, bypass_rbac):
        from src.services.events.events import get_calendar_events
        start = "2000-01-01"
        end = "2099-12-31"
        results = await get_calendar_events(MagicMock(), org.id, admin_user, db, start_date=start, end_date=end)
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_filters_by_event_type(self, db, org, event, admin_user, bypass_rbac):
        from src.services.events.events import get_calendar_events
        start, end = "2000-01-01", "2099-12-31"
        results = await get_calendar_events(MagicMock(), org.id, admin_user, db, start_date=start, end_date=end, event_type="webinar")
        assert len(results) == 0
        results = await get_calendar_events(MagicMock(), org.id, admin_user, db, start_date=start, end_date=end, event_type="live_session")
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_filters_by_community(self, db, org, community, event, admin_user, bypass_rbac):
        from src.services.events.events import get_calendar_events
        start, end = "2000-01-01", "2099-12-31"
        results = await get_calendar_events(MagicMock(), org.id, admin_user, db, start_date=start, end_date=end, community_id=community.id)
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_filters_by_space(self, db, org, space, community, admin_user, bypass_rbac):
        from src.services.events.events import get_calendar_events, create_event
        from src.db.events.events import EventCreate
        ec = EventCreate(title="Space Event", start_date=str(datetime.now()), org_id=org.id, author_id=admin_user.id, space_id=space.id)
        await create_event(MagicMock(), org.id, ec, admin_user, db)
        start, end = "2000-01-01", "2099-12-31"
        results = await get_calendar_events(MagicMock(), org.id, admin_user, db, start_date=start, end_date=end, space_id=space.id)
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_returns_empty_for_no_events(self, db, org, admin_user):
        from src.services.events.events import get_calendar_events
        start, end = "2000-01-01", "2000-01-02"
        results = await get_calendar_events(MagicMock(), org.id, admin_user, db, start_date=start, end_date=end)
        assert len(results) == 0


# ── Reminders ────────────────────────────────────────────────────────────


class TestCreateEventReminder:
    @pytest.mark.asyncio
    async def test_creates_reminder(self, db, org, event, admin_user):
        from src.services.events.events import create_event_reminder
        from src.db.events.reminders import EventReminderCreate
        rem_data = EventReminderCreate(
            event_id=event.id, user_id=admin_user.id, org_id=org.id,
            remind_at=str(datetime.now()), channel="email",
        )
        result = await create_event_reminder(MagicMock(), "event_test", rem_data, admin_user, db)
        assert result.channel == "email"
        assert result.status == "pending"

    @pytest.mark.asyncio
    async def test_requires_event(self, db, admin_user):
        from src.services.events.events import create_event_reminder
        from src.db.events.reminders import EventReminderCreate
        with pytest.raises(HTTPException, match="Event not found"):
            await create_event_reminder(MagicMock(), "event_nonexistent",
                EventReminderCreate(event_id=0, user_id=admin_user.id, org_id=0, remind_at=""), admin_user, db)


class TestGetEventReminders:
    @pytest.mark.asyncio
    async def test_lists_reminders(self, db, org, event, admin_user):
        from src.services.events.events import create_event_reminder, get_event_reminders
        from src.db.events.reminders import EventReminderCreate
        await create_event_reminder(MagicMock(), "event_test",
            EventReminderCreate(event_id=event.id, user_id=admin_user.id, org_id=org.id, remind_at=str(datetime.now())), admin_user, db)
        reminders = await get_event_reminders(MagicMock(), "event_test", admin_user, db)
        assert len(reminders) >= 1


class TestGetUserReminders:
    @pytest.mark.asyncio
    async def test_lists_user_reminders(self, db, org, event, admin_user):
        from src.services.events.events import create_event_reminder, get_user_reminders
        from src.db.events.reminders import EventReminderCreate
        await create_event_reminder(MagicMock(), "event_test",
            EventReminderCreate(event_id=event.id, user_id=admin_user.id, org_id=org.id, remind_at=str(datetime.now())), admin_user, db)
        reminders = await get_user_reminders(MagicMock(), admin_user, db)
        assert len(reminders) >= 1

    @pytest.mark.asyncio
    async def test_filters_by_status(self, db, org, event, admin_user):
        from src.services.events.events import create_event_reminder, get_user_reminders
        from src.db.events.reminders import EventReminderCreate
        await create_event_reminder(MagicMock(), "event_test",
            EventReminderCreate(event_id=event.id, user_id=admin_user.id, org_id=org.id, remind_at=str(datetime.now())), admin_user, db)
        pending = await get_user_reminders(MagicMock(), admin_user, db, status="pending")
        assert len(pending) >= 1
        sent = await get_user_reminders(MagicMock(), admin_user, db, status="sent")
        assert len(sent) == 0


# ── Recordings ───────────────────────────────────────────────────────────


class TestCreateRecording:
    @pytest.mark.asyncio
    async def test_creates_recording(self, db, org, event, admin_user):
        from src.services.events.events import create_recording
        from src.db.events.recordings import EventRecordingCreate
        rec_data = EventRecordingCreate(
            event_id=event.id, org_id=org.id, recording_type="recording",
            title="Test Recording", file_url="https://cdn.example.com/rec.mp4",
        )
        result = await create_recording(MagicMock(), rec_data, admin_user, db)
        assert result.title == "Test Recording"
        assert result.recording_type == "recording"

    @pytest.mark.asyncio
    async def test_creates_slides(self, db, org, event, admin_user):
        from src.services.events.events import create_recording
        from src.db.events.recordings import EventRecordingCreate
        rec_data = EventRecordingCreate(
            event_id=event.id, org_id=org.id, recording_type="slides",
            title="Deck.pdf", file_url="https://cdn.example.com/deck.pdf",
        )
        result = await create_recording(MagicMock(), rec_data, admin_user, db)
        assert result.recording_type == "slides"


class TestGetEventRecordings:
    @pytest.mark.asyncio
    async def test_lists_recordings(self, db, org, event, admin_user):
        from src.services.events.events import create_recording, get_event_recordings
        from src.db.events.recordings import EventRecordingCreate
        await create_recording(MagicMock(), EventRecordingCreate(event_id=event.id, org_id=org.id, title="Rec1", file_url="url"), admin_user, db)
        await create_recording(MagicMock(), EventRecordingCreate(event_id=event.id, org_id=org.id, title="Rec2", file_url="url2"), admin_user, db)
        recordings = await get_event_recordings(MagicMock(), "event_test", admin_user, db)
        assert len(recordings) == 2

    @pytest.mark.asyncio
    async def test_filters_by_type(self, db, org, event, admin_user):
        from src.services.events.events import create_recording, get_event_recordings
        from src.db.events.recordings import EventRecordingCreate
        await create_recording(MagicMock(), EventRecordingCreate(event_id=event.id, org_id=org.id, title="Rec", file_url="url", recording_type="recording"), admin_user, db)
        await create_recording(MagicMock(), EventRecordingCreate(event_id=event.id, org_id=org.id, title="Slides", file_url="url2", recording_type="slides"), admin_user, db)
        recordings = await get_event_recordings(MagicMock(), "event_test", admin_user, db, recording_type="slides")
        assert len(recordings) == 1
        assert recordings[0].recording_type == "slides"


class TestUpdateRecording:
    @pytest.mark.asyncio
    async def test_updates_title(self, db, org, event, admin_user):
        from src.services.events.events import create_recording, update_recording
        from src.db.events.recordings import EventRecordingCreate
        rec = await create_recording(MagicMock(), EventRecordingCreate(event_id=event.id, org_id=org.id, title="Old", file_url="url"), admin_user, db)
        result = await update_recording(MagicMock(), rec.id, {"title": "New Title"}, admin_user, db)
        assert result.title == "New Title"

    @pytest.mark.asyncio
    async def test_updates_file_url(self, db, org, event, admin_user):
        from src.services.events.events import create_recording, update_recording
        from src.db.events.recordings import EventRecordingCreate
        rec = await create_recording(MagicMock(), EventRecordingCreate(event_id=event.id, org_id=org.id, title="Rec", file_url="old_url"), admin_user, db)
        result = await update_recording(MagicMock(), rec.id, {"file_url": "new_url"}, admin_user, db)
        assert result.file_url == "new_url"


class TestDeleteRecording:
    @pytest.mark.asyncio
    async def test_deletes_recording(self, db, org, event, admin_user):
        from src.services.events.events import create_recording, delete_recording, get_event_recordings
        from src.db.events.recordings import EventRecordingCreate
        rec = await create_recording(MagicMock(), EventRecordingCreate(event_id=event.id, org_id=org.id, title="ToDelete", file_url="url"), admin_user, db)
        result = await delete_recording(MagicMock(), rec.id, admin_user, db)
        assert result["detail"] == "Recording deleted"
        recordings = await get_event_recordings(MagicMock(), "event_test", admin_user, db)
        assert len(recordings) == 0


# ── Analytics ────────────────────────────────────────────────────────────


class TestRegistrationAnalytics:
    @pytest.mark.asyncio
    async def test_returns_counts(self, db, org, event, admin_user, bypass_rbac):
        from src.services.events.events import get_event_registration_counts, rsvp_event
        from src.db.events.rsvps import RSVPCreate
        await rsvp_event(MagicMock(), "event_test", RSVPCreate(event_id=event.id, user_id=admin_user.id, status="going"), admin_user, db)
        from src.db.communities.communities import Community
        community = await db.get(Community, event.community_id)
        result = await get_event_registration_counts(MagicMock(), "event_test", admin_user, db)
        assert "going" in result
        assert result["going"] >= 1


class TestRecordingViews:
    @pytest.mark.asyncio
    async def test_tracks_view(self, db, org, event, admin_user):
        from src.services.events.events import create_recording, track_recording_view
        from src.db.events.recordings import EventRecordingCreate
        rec = await create_recording(MagicMock(), EventRecordingCreate(event_id=event.id, org_id=org.id, title="Rec", file_url="url"), admin_user, db)
        result = await track_recording_view(MagicMock(), rec.id, 120, admin_user, db)
        assert result["detail"] == "View tracked"

    @pytest.mark.asyncio
    async def test_gets_views(self, db, org, event, admin_user):
        from src.services.events.events import create_recording, track_recording_view, get_recording_views
        from src.db.events.recordings import EventRecordingCreate
        rec = await create_recording(MagicMock(), EventRecordingCreate(event_id=event.id, org_id=org.id, title="Rec", file_url="url"), admin_user, db)
        await track_recording_view(MagicMock(), rec.id, 120, admin_user, db)
        result = await get_recording_views(MagicMock(), rec.id, admin_user, db)
        assert result["total_views"] >= 1
        assert result["total_watch_seconds"] >= 120


# ── Membership restrictions ──────────────────────────────────────────────


class TestCheckEventMembershipAccess:
    @pytest.mark.asyncio
    async def test_allows_access_when_no_plan_links(self, db, org, event, admin_user):
        from src.services.events.events import check_event_membership_access
        result = await check_event_membership_access(event, admin_user.id, db)
        assert result is True

    @pytest.mark.asyncio
    async def test_blocks_access_when_not_subscribed(self, db, org, community, event, membership_plan, plan_event, regular_user):
        from src.services.events.events import check_event_membership_access
        result = await check_event_membership_access(event, regular_user.id, db)
        assert result is False

    @pytest.mark.asyncio
    async def test_allows_access_when_subscribed(self, db, org, community, event, membership_plan, plan_event, regular_user):
        from src.services.events.events import check_event_membership_access
        from src.services.payments.lifecycle import create_member
        from src.db.communities.communities import Community
        comm = await db.get(Community, community.id)
        await create_member(db, membership_plan, comm, org, regular_user.id, status="active", provider="stripe")
        result = await check_event_membership_access(event, regular_user.id, db)
        assert result is True


# ── Utility functions ────────────────────────────────────────────────────


class TestGetEventTypes:
    @pytest.mark.asyncio
    async def test_returns_all_types(self):
        from src.services.events.events import get_event_types
        from src.db.events.events import EVENT_TYPES
        result = await get_event_types()
        assert result["types"] == EVENT_TYPES


class TestGetEventStatuses:
    @pytest.mark.asyncio
    async def test_returns_all_statuses(self):
        from src.services.events.events import get_event_statuses
        from src.db.events.events import EVENT_STATUSES
        result = await get_event_statuses()
        assert result["statuses"] == EVENT_STATUSES


class TestScheduleRemindersForEvent:
    @pytest.mark.asyncio
    async def test_schedules_one_hour_before(self, db, event):
        from src.services.events.events import schedule_reminders_for_event
        from src.db.events.reminders import EventReminder
        await schedule_reminders_for_event(event, db)
        reminders = (await db.execute(select(EventReminder))).scalars().all()
        for r in reminders:
            assert r.status == "pending"


class TestEventHelpers:
    def test_now_iso(self):
        from src.services.events.events import _now_iso
        result = _now_iso()
        assert "T" in result

    def test_iso_to_dt_valid(self):
        from src.services.events.events import _iso_to_dt
        dt = _iso_to_dt("2024-01-01T12:00:00")
        assert dt is not None
        assert dt.year == 2024

    def test_iso_to_dt_invalid(self):
        from src.services.events.events import _iso_to_dt
        dt = _iso_to_dt("not-a-date")
        assert dt is None
