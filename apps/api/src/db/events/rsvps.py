from typing import Optional
from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, Index
from sqlmodel import Field, SQLModel


RSVP_STATUSES = ["going", "maybe", "not_going", "waitlist"]


class RSVP(SQLModel, table=True):
    __table_args__ = (
        Index("ix_rsvp_event_user", "event_id", "user_id"),
        Index("ix_rsvp_event_status", "event_id", "status"),
        Index("ix_rsvp_user", "user_id"),
    )
    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: int = Field(
        sa_column=Column(Integer, ForeignKey("event.id", ondelete="CASCADE"))
    )
    user_id: int = Field(
        sa_column=Column(Integer, ForeignKey("user.id", ondelete="CASCADE"))
    )
    status: str = Field(default="going", sa_column=Column(String(20)))
    attended: bool = False
    attended_at: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""


class RSVPCreate(SQLModel):
    event_id: int
    user_id: int
    status: str = "going"


class RSVPUpdate(SQLModel):
    status: str


class RSVPRead(SQLModel):
    id: int
    event_id: int
    user_id: int
    status: str
    attended: bool
    attended_at: Optional[str] = None
    created_at: str
    updated_at: str
