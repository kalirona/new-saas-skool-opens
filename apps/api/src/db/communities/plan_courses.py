from typing import Optional
from sqlalchemy import Column, ForeignKey, Integer
from sqlmodel import Field, SQLModel


class PlanCourseBase(SQLModel):
    plan_id: int
    course_id: int


class PlanCourse(PlanCourseBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    plan_id: int = Field(
        sa_column=Column(Integer, ForeignKey("membershipplan.id", ondelete="CASCADE"))
    )
    course_id: int = Field(
        sa_column=Column(Integer, ForeignKey("course.id", ondelete="CASCADE"))
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
