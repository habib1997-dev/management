"""Shared login-account helpers (user email uniqueness and profile links)."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from student_management.models import User

EMAIL_TAKEN = "This email is already used by a login account"


def user_email_taken(
    db: Session, email: str, exclude_user_id: uuid.UUID | None = None
) -> bool:
    """True if a login account already uses this email.

    `exclude_user_id` lets an edit of a profile keep the email it is already
    linked to (its own login must not count as a collision).
    """
    query = db.query(User).filter(func.lower(User.email) == email.lower())
    if exclude_user_id is not None:
        query = query.filter(User.user_id != exclude_user_id)
    return query.first() is not None


def assert_email_free(
    db: Session, email: str, exclude_user_id: uuid.UUID | None = None
) -> None:
    """Raise a 400 if the email is taken by a login account."""
    if user_email_taken(db, email, exclude_user_id=exclude_user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=EMAIL_TAKEN
        )


def user_for_teacher(db: Session, teacher_id) -> User | None:
    return db.query(User).filter(User.teacher_id == teacher_id).first()


def user_for_parent(db: Session, parent_id) -> User | None:
    return db.query(User).filter(User.parent_id == parent_id).first()