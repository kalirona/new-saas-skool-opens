from typing import Optional, Dict, Any
from sqlalchemy import Column, ForeignKey, Integer, Text, String, JSON, Index
from sqlmodel import Field, SQLModel


RECORDING_TYPES = ["recording", "slides", "resource", "transcript"]


class EventRecording(SQLModel, table=True):
    __table_args__ = (
    )
    """Recording, slide deck, resource file, or transcript attached to a past event."""
    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: int = Field(
        sa_column=Column(Integer, ForeignKey("event.id", ondelete="CASCADE"), index=True)
    )
    org_id: int = Field(
        sa_column=Column(Integer, ForeignKey("organization.id", ondelete="CASCADE"), index=True)
    )
    recording_type: str = Field(default="recording", sa_column=Column(String(20)))
    title: str
    description: Optional[str] = Field(default=None, sa_column=Column(Text))
    file_url: Optional[str] = None
    file_size: Optional[int] = None
    file_mime: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration_seconds: Optional[int] = None
    course_id: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("course.id", ondelete="SET NULL"), nullable=True, index=True),
    )
    activity_id: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("activity.id", ondelete="SET NULL"), nullable=True, index=True),
    )
    metadata: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON, nullable=True))
    created_at: str = ""
    updated_at: str = ""


class EventRecordingCreate(SQLModel):
    event_id: int
    org_id: int
    recording_type: str = "recording"
    title: str
    description: Optional[str] = None
    file_url: Optional[str] = None
    file_size: Optional[int] = None
    file_mime: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration_seconds: Optional[int] = None
    course_id: Optional[int] = None
    activity_id: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class EventRecordingRead(SQLModel):
    id: int
    event_id: int
    recording_type: str
    title: str
    description: Optional[str] = None
    file_url: Optional[str] = None
    file_size: Optional[int] = None
    file_mime: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration_seconds: Optional[int] = None
    course_id: Optional[int] = None
    activity_id: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: str
    updated_at: str
