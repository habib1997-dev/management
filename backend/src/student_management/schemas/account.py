"""Pydantic schemas for login accounts (teachers/parents)."""

import uuid

from pydantic import BaseModel, Field


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