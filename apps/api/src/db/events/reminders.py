from typing import Optional
from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, Index
from sqlmodel import Field, SQLModel


REMINDER_INTERVALS = ["10_minutes", "1_hour", "24_hours"]
REMINDER_CHANNELS = ["in_app", "email", "both"]
REMINDER_STATUSES = ["pending", "sent", "failed"]


class EventReminder(SQLModel, table=True):
    __table_args__ = (
        Index("ix_eventreminder_user_status", "user_id", "status"),
    )
    """A scheduled reminder for an event, sent to a specific user."""
    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: int = Field(
        sa_column=Column(Integer, ForeignKey("event.id", ondelete="CASCADE"), index=True)
    )
    user_id: int = Field(
        sa_column=Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), index=True)
    )
    org_id: int = Field(
        sa_column=Column(Integer, ForeignKey("organization.id", ondelete="CASCADE"), index=True)
    )
    remind_at: str = Field(sa_column=Column(String(30)))
    channel: str = Field(default="both", sa_column=Column(String(10)))
    status: str = Field(default="pending", sa_column=Column(String(10)))
    sent_at: Optional[str] = None
    error_message: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""


class EventReminderCreate(SQLModel):
    event_id: int
    user_id: int
    org_id: int
    remind_at: str
    channel: str = "both"


class EventReminderRead(SQLModel):
    id: int
    event_id: int
    user_id: int
    remind_at: str
    channel: str
    status: str
    sent_at: Optional[str] = None
    created_at: str
