"""Commit/flush helpers that turn database constraint violations into 400s.

The profile tables and the users table all have a UNIQUE constraint on email.
Those unique checks are also performed with a pre-query in the service layer,
but a concurrent request can slip between the check and the write. Catching the
resulting IntegrityError here keeps the API contract stable (a 400, not a 500)
and rolls back the session so the request ends cleanly.
"""

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

EMAIL_IN_USE = "This email is already in use"


def commit_or_conflict(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=EMAIL_IN_USE
        ) from None


def flush_or_conflict(db: Session) -> None:
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=EMAIL_IN_USE
        ) from None