"""Shared authentication and role-based access control dependencies."""

from __future__ import annotations

import uuid
from collections.abc import Callable

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from student_management.db import get_db
from student_management.models import User
from student_management.security import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)

CREDENTIALS_ERROR = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise CREDENTIALS_ERROR
    try:
        payload = decode_access_token(credentials.credentials)
    except jwt.PyJWTError:
        raise CREDENTIALS_ERROR from None

    user_id = payload.get("sub")
    try:
        uid = uuid.UUID(user_id) if user_id else None
    except ValueError:
        uid = None
    if uid is None:
        raise CREDENTIALS_ERROR

    user = db.get(User, uid)
    if user is None or not user.active:
        raise CREDENTIALS_ERROR
    return user


def require_roles(*roles: str) -> Callable[..., User]:
    """Return a dependency that allows only the given roles."""

    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return user

    return dependency


def assert_can_access_course(course, user: User) -> None:
    """Admins see all courses; teachers only their own."""
    if user.role == "teacher" and course.teacher_id != user.teacher_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own courses",
        )