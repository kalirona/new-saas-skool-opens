from typing import Optional
from sqlalchemy import Column, ForeignKey, Integer, BigInteger, Index
from sqlmodel import Field, SQLModel


class EventRegistrationCount(SQLModel, table=True):
    __table_args__ = (
        Index("ix_eventregcount_event", "event_id"),
        Index("ix_eventregcount_org", "org_id"),
    )
    """Daily snapshot of event registration counts."""
    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: int = Field(
        sa_column=Column(Integer, ForeignKey("event.id", ondelete="CASCADE"))
    )
    org_id: int = Field(
        sa_column=Column(Integer, ForeignKey("organization.id", ondelete="CASCADE"))
    )
    total_rsvps: int = 0
    going_count: int = 0
    maybe_count: int = 0
    waitlist_count: int = 0
    not_going_count: int = 0
    attended_count: int = 0
    snapshot_date: str = ""
    created_at: str = ""


class EventRecordingView(SQLModel, table=True):
    __table_args__ = (
        Index("ix_eventrecordingview_recording", "recording_id"),
        Index("ix_eventrecordingview_user", "user_id"),
        Index("ix_eventrecordingview_org", "org_id"),
    )
    """Tracks views of event recordings."""
    id: Optional[int] = Field(default=None, primary_key=True)
    recording_id: int = Field(
        sa_column=Column(Integer, ForeignKey("eventrecording.id", ondelete="CASCADE"))
    )
    user_id: int = Field(
        sa_column=Column(Integer, ForeignKey("user.id", ondelete="CASCADE"))
    )
    org_id: int = Field(
        sa_column=Column(Integer, ForeignKey("organization.id", ondelete="CASCADE"))
    )
    watch_seconds: int = 0
    viewed_at: str = ""
    created_at: str = ""


class EventRSVPSnapshot(SQLModel, table=True):
    __table_args__ = (
        Index("ix_eventrsvpsnapshot_event", "event_id"),
    )
    """Tracks RSVP changes over time for trend analysis."""
    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: int = Field(
        sa_column=Column(Integer, ForeignKey("event.id", ondelete="CASCADE"))
    )
    going: int = 0
    maybe: int = 0
    waitlist: int = 0
    not_going: int = 0
    snapshot_date: str = ""
    created_at: str = ""
