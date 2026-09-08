"""Pydantic schemas for login accounts (teachers/parents)."""

import uuid

from pydantic import BaseModel, ConfigDict, Field


class AccountCreate(BaseModel):
    password: str = Field(min_length=8, max_length=128)


class AccountDetail(BaseModel):
    email: str
    role: str
    user_id: uuid.UUID


class AccountResponse(BaseModel):
    success: bool = True
    account: AccountDetail
    message: str


class UserAdminUpdate(BaseModel):
    active: bool | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserAdminDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    email: str
    role: str
    active: bool


class UserAdminResponse(BaseModel):
    success: bool = True
    user: UserAdminDetail
    message: str