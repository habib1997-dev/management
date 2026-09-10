"""Pydantic schemas for authentication."""

import uuid

from pydantic import BaseModel, EmailStr, field_validator


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email", mode="before")
    @classmethod
    def strip_email(cls, value):
        if isinstance(value, str):
            value = value.strip()
        if value == "":
            raise ValueError("email must not be blank")
        return value


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: str
    email: str
    teacher_id: uuid.UUID | None = None
    parent_id: uuid.UUID | None = None