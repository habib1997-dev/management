"""Pydantic schemas for teachers."""

import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator

from student_management.schemas.common import validate_email_lenient
from student_management.schemas.course import CourseSummary


class TeacherCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(max_length=200)
    subjects_taught: str | None = Field(default=None, max_length=100)
    password: str | None = Field(default=None, min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return validate_email_lenient(value)


class TeacherSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    teacher_id: uuid.UUID
    name: str
    email: str
    subjects_taught: str | None
    status: bool


class TeacherUpdate(BaseModel):
    """Admin can update a teacher's profile and/or active status."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    email: str | None = Field(default=None, max_length=200)
    subjects_taught: str | None = Field(default=None, max_length=100)
    status: bool | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return validate_email_lenient(value)


class TeacherDetail(TeacherSummary):
    courses: list[CourseSummary] = []


class TeacherResponse(BaseModel):
    success: bool = True
    teacher: TeacherDetail
    message: str


class TeacherListResponse(BaseModel):
    data: list[TeacherSummary]
    meta: dict