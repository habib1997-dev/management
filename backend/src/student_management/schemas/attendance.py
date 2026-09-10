"""Pydantic schemas for attendance."""

import uuid
from datetime import UTC, date, datetime

import pydantic
from pydantic import BaseModel, ConfigDict, Field

from student_management.models.enums import AttendanceStatus


class AttendanceRecordInput(BaseModel):
    student_id: uuid.UUID
    status: AttendanceStatus


class AttendanceCreate(BaseModel):
    course_id: uuid.UUID
    date: date
    records: list[AttendanceRecordInput] = Field(min_length=1)

    @pydantic.model_validator(mode="after")
    def validate_date_not_future(self) -> "AttendanceCreate":
        if self.date > datetime.now(UTC).date():
            raise ValueError("attendance date cannot be in the future")
        return self


class AttendanceDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    attendance_id: uuid.UUID
    student_id: uuid.UUID
    course_id: uuid.UUID
    course_name: str | None = None
    date: date
    status: str
    marked_by: uuid.UUID | None


class AttendanceResponse(BaseModel):
    success: bool = True
    attendance: list[AttendanceDetail]
    message: str