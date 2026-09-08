"""Pydantic schemas for courses."""

import uuid

import pydantic
from pydantic import BaseModel, ConfigDict, Field

from student_management.models.enums import CourseStatus
from student_management.schemas.student import StudentSummary


class CourseSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    course_id: uuid.UUID
    name: str
    teacher_id: uuid.UUID
    grade_level: str
    semester: str
    status: str


class CourseDetail(CourseSummary):
    max_students: int | None
    students: list[StudentSummary] = []


class CourseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    teacher_id: uuid.UUID
    grade_level: str = Field(min_length=1, max_length=20)
    semester: str = Field(min_length=1, max_length=20)
    max_students: int = Field(default=30, ge=1, le=500)

    @pydantic.field_validator("grade_level")
    @classmethod
    def strip_grade_level(cls, value: str) -> str:
        return value.strip()


class CourseUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    teacher_id: uuid.UUID | None = None
    max_students: int | None = Field(default=None, ge=1, le=500)
    status: CourseStatus | None = None


class CourseResponse(BaseModel):
    success: bool = True
    course: CourseDetail
    message: str


class CourseListResponse(BaseModel):
    data: list[CourseSummary]
    meta: dict


class CourseRosterUpdate(BaseModel):
    student_ids: list[uuid.UUID] = Field(default_factory=list)