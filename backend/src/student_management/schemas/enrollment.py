"""Pydantic schemas for enrollment records."""

import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from student_management.models.enums import EnrollmentStatus


class EnrollmentCreate(BaseModel):
    student_id: uuid.UUID
    enrolled_by: str = Field(min_length=1, max_length=100)
    status: EnrollmentStatus = EnrollmentStatus.ACTIVE


class EnrollmentDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    enrollment_id: uuid.UUID
    student_id: uuid.UUID
    enrolled_by: str
    enrollment_date: date
    status: str


class EnrollmentResponse(BaseModel):
    success: bool = True
    enrollment: EnrollmentDetail
    message: str