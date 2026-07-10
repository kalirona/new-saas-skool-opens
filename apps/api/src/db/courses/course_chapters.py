from typing import Optional
from sqlalchemy import Column, ForeignKey, Integer, Index
from sqlmodel import Field, SQLModel


class CourseChapter(SQLModel, table=True):
    __table_args__ = (
        Index("ix_coursechapter_course_order", "course_id", "order"),
    )
    id: Optional[int] = Field(default=None, primary_key=True)
    order: int
    course_id: int = Field(
        sa_column=Column(Integer, ForeignKey("course.id", ondelete="CASCADE"), index=True)
    )
    chapter_id: int = Field(
        sa_column=Column(Integer, ForeignKey("chapter.id", ondelete="CASCADE"), index=True)
    )
    org_id: int = Field(
        sa_column=Column(Integer, ForeignKey("organization.id", ondelete="CASCADE"), index=True)
    )
    creation_date: str
    update_date: str
