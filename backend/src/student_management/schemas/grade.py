"""Pydantic schemas for grades."""

import uuid
from datetime import date

import pydantic
from pydantic import BaseModel, ConfigDict, Field

from student_management.models.enums import AssignmentType


class GradeCreate(BaseModel):
    student_id: uuid.UUID
    course_id: uuid.UUID
    grade_value: float = Field(ge=0, le=100)
    assignment_type: AssignmentType | None = None
    date_assigned: date
    date_due: date

    @pydantic.model_validator(mode="after")
    def validate_date_order(self) -> "GradeCreate":
        if self.date_due < self.date_assigned:
            raise ValueError("date_due cannot be before date_assigned")
        return self


class GradeDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    grade_id: uuid.UUID
    student_id: uuid.UUID
    course_id: uuid.UUID
    grade_value: float
    assignment_type: str | None
    date_assigned: date
    date_due: date
    date_graded: date


class GradeResponse(BaseModel):
    success: bool = True
    grade: GradeDetail
    message: str