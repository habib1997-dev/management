"""Pydantic schemas for students and enrollments."""

import re
import uuid
from datetime import UTC, date, datetime

import pydantic
from email_validator import EmailNotValidError, validate_email
from pydantic import BaseModel, ConfigDict, Field

PHONE_PATTERN = r"^[\d\s()+\-]{7,20}$"


def validate_email_lenient(value: str) -> str:
    """Validate an email without requiring the domain to exist on the internet.

    Schools routinely type fictional addresses (e.g. jane@myschool.edu); rejecting
    them purely because the domain has no DNS records would be wrong for this app.
    """
    try:
        email = validate_email(value.strip(), check_deliverability=False)
    except EmailNotValidError as exc:
        raise ValueError(str(exc)) from exc
    return email.normalized


class StudentEnrollment(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    date_of_birth: date
    grade_level: str = Field(min_length=1, max_length=20)
    email: str | None = None
    phone: str | None = Field(default=None, max_length=50)

    @pydantic.field_validator("grade_level")
    @classmethod
    def strip_grade_level(cls, value: str) -> str:
        return value.strip()

    @pydantic.model_validator(mode="after")
    def validate_dates(self) -> "StudentEnrollment":
        if self.date_of_birth >= datetime.now(UTC).date():
            raise ValueError("date_of_birth must be a past date")
        return self

    @pydantic.field_validator("email")
    @classmethod
    def validate_email_field(cls, value: str | None) -> str | None:
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
        return value


class StudentUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    date_of_birth: date | None = None
    grade_level: str | None = Field(default=None, min_length=1, max_length=20)
    email: str | None = None
    phone: str | None = Field(default=None, max_length=50)
    active: bool | None = None

    @pydantic.field_validator("email")
    @classmethod
    def validate_email_field(cls, value: str | None) -> str | None:
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
        return value

    @pydantic.field_validator("grade_level")
    @classmethod
    def strip_grade_level(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("grade_level must not be blank")
        return stripped

    @pydantic.model_validator(mode="after")
    def validate_dates(self) -> "StudentUpdate":
        if self.date_of_birth is not None and self.date_of_birth >= datetime.now(
            UTC
        ).date():
            raise ValueError("date_of_birth must be a past date")
        return self


class StudentSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    student_id: uuid.UUID
    first_name: str
    last_name: str
    grade_level: str
    active: bool
    enrollment_date: date


class StudentDetail(StudentSummary):
    date_of_birth: date
    email: str | None
    phone: str | None


class StudentResponse(BaseModel):
    success: bool = True
    student: StudentDetail
    message: str


class StudentListResponse(BaseModel):
    data: list[StudentDetail]
    meta: dict


class StudentListQuery(BaseModel):
    page: int = Field(default=1, ge=1)
    pageSize: int = Field(default=20, ge=1, le=100)
    search: str | None = None
    gradeLevel: str | None = Field(default=None, min_length=1, max_length=20)
    active: bool | None = None