"""Pydantic schemas for parents."""

import re
import uuid

import pydantic
from pydantic import BaseModel, ConfigDict, Field

from student_management.schemas.attendance import AttendanceDetail
from student_management.schemas.common import validate_email_lenient
from student_management.schemas.grade import GradeDetail
from student_management.schemas.student import PHONE_PATTERN


class ParentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(max_length=200)
    phone: str = Field(max_length=50)
    password: str | None = Field(default=None, min_length=8, max_length=128)
    student_ids: list[uuid.UUID] = Field(default_factory=list)

    @pydantic.field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return validate_email_lenient(value)

    @pydantic.field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        if not re.fullmatch(PHONE_PATTERN, value):
            raise ValueError("phone must be a valid phone number")
        return value.strip()


class ParentStudentsUpdate(BaseModel):
    student_ids: list[uuid.UUID] = Field(default_factory=list)


class ParentUpdate(BaseModel):
    """Admin can update a parent's profile and/or active status."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    email: str | None = Field(default=None, max_length=200)
    phone: str | None = Field(default=None, max_length=50)
    status: bool | None = None

    @pydantic.field_validator("email")
    @classmethod
    def normalize_email(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return validate_email_lenient(value)

    @pydantic.field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if not re.fullmatch(PHONE_PATTERN, value):
            raise ValueError("phone must be a valid phone number")
        return value.strip()


class ParentSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    parent_id: uuid.UUID
    name: str
    email: str
    phone: str
    status: bool


class ParentResponse(BaseModel):
    success: bool = True
    parent: ParentSummary
    message: str


class ParentListResponse(BaseModel):
    data: list[ParentSummary]
    meta: dict


class PortalChild(BaseModel):
    student_id: uuid.UUID
    first_name: str
    last_name: str
    grade_level: str | None
    attendance: list[AttendanceDetail]
    grades: list[GradeDetail]


class PortalParent(BaseModel):
    parent_id: uuid.UUID
    name: str
    email: str
    children: list[PortalChild]


class ParentPortal(BaseModel):
    success: bool = True
    parents: list[PortalParent]