from typing import Optional, List, Dict, Any
from sqlalchemy import Column, ForeignKey, Integer, BigInteger, Text, String, JSON, Boolean, Index
from sqlmodel import Field, SQLModel


EVENT_TYPES = [
    "live_session",
    "webinar",
    "workshop",
    "group_coaching",
    "office_hours",
    "ama",
    "meetup",
    "course_lesson_live",
]

EVENT_STATUSES = ["scheduled", "live", "ended", "cancelled"]

REPEAT_INTERVALS = ["none", "daily", "weekly", "biweekly", "monthly", "custom"]


class EventBase(SQLModel):
    title: str
    description: Optional[str] = Field(default=None, sa_column=Column(Text))
    cover_image: Optional[str] = None
    event_type: str = Field(default="live_session", sa_column=Column(String(30)))
    status: str = Field(default="scheduled", sa_column=Column(String(20)))
    host_name: Optional[str] = None
    host_id: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("user.id", ondelete="SET NULL"), nullable=True),
    )
    start_date: str = Field(default="", sa_column=Column(String(20)))
    end_date: Optional[str] = Field(default=None, sa_column=Column(String(20)))
    timezone: Optional[str] = Field(default=None, sa_column=Column(String(50)))
    duration_minutes: Optional[int] = None
    capacity: Optional[int] = None
    repeat_interval: str = "none"
    repeat_end_date: Optional[str] = Field(default=None, sa_column=Column(String(20)))
    recurring_rule: Optional[str] = Field(default=None, sa_column=Column(Text))
    meeting_url: Optional[str] = None
    meeting_provider: Optional[str] = Field(default=None, sa_column=Column(String(30)))
    recording_url: Optional[str] = None
    attachments: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON, nullable=True))
    visibility: str = Field(default="private", sa_column=Column(String(20)))
    locked: bool = False
    rsvp_enabled: bool = True


class Event(EventBase, table=True):
    __table_args__ = (
        Index("ix_event_org_start", "org_id", "start_date"),
        Index("ix_event_org_type", "org_id", "event_type"),
        Index("ix_event_org_status", "org_id", "status"),
        Index("ix_event_org_community", "org_id", "community_id"),
    )
    id: Optional[int] = Field(default=None, primary_key=True)
    org_id: int = Field(
        sa_column=Column(BigInteger, ForeignKey("organization.id", ondelete="CASCADE"))
    )
    community_id: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("community.id", ondelete="SET NULL"), nullable=True),
    )
    space_id: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("space.id", ondelete="SET NULL"), nullable=True),
    )
    author_id: int = Field(
        sa_column=Column(Integer, ForeignKey("user.id", ondelete="CASCADE"))
    )
    event_uuid: str = Field(default="", index=True)
    creation_date: str = ""
    update_date: str = ""


class EventCreate(EventBase):
    org_id: int
    author_id: int
    community_id: Optional[int] = None
    space_id: Optional[int] = None


class EventUpdate(SQLModel):
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


class EventRead(EventBase):
    id: int
    org_id: int
    community_id: Optional[int] = None
    space_id: Optional[int] = None
    author_id: int
    event_uuid: str
    creation_date: str
    update_date: str


class EventDetailRead(EventRead):
    """Extended read with joined data."""
    community_name: Optional[str] = None
    community_uuid: Optional[str] = None
    space_name: Optional[str] = None
    space_uuid: Optional[str] = None
    author_name: Optional[str] = None
    author_avatar: Optional[str] = None
    attendee_count: int = 0
    rsvp_status: Optional[str] = None
