from typing import Optional
from sqlalchemy import Column, ForeignKey, Integer, Index
from sqlmodel import Field, SQLModel


class PlanCourseBase(SQLModel):
    plan_id: int
    course_id: int


class PlanCourse(PlanCourseBase, table=True):
    __table_args__ = (
        Index("ix_plancourse_plan_course", "plan_id", "course_id", unique=True),
    )
    id: Optional[int] = Field(default=None, primary_key=True)
    plan_id: int = Field(
        sa_column=Column(Integer, ForeignKey("membershipplan.id", ondelete="CASCADE"), index=True)
    )
    course_id: int = Field(
        sa_column=Column(Integer, ForeignKey("course.id", ondelete="CASCADE"), index=True)
    )
    creation_date: str = ""
    update_date: str = ""


class PlanCourseCreate(SQLModel):
    plan_id: int
    course_id: int


class PlanCourseRead(PlanCourseBase):
    id: int
    creation_date: str
    update_date: str
