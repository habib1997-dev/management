"""Business logic for login accounts for teachers and parents."""

import uuid
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from student_management.models import User
from student_management.security import hash_password
from student_management.services.parent_service import get_parent_or_404
from student_management.services.teacher_service import get_teacher_or_404


def create_user_for(
    db: Session,
    *,
    email: str,
    role: str,
    password: str,
    teacher_id: uuid.UUID | None = None,
    parent_id: uuid.UUID | None = None,
) -> User:
    user = User(
        email=email.lower(),
        password_hash=hash_password(password),
        role=role,
        teacher_id=teacher_id,
        parent_id=parent_id,
    )
    db.add(user)
    return user


def _existing_account(db: Session, **filters: Any) -> User | None:
    return db.query(User).filter_by(**filters).first()


def create_teacher_account(db: Session, teacher_id, password: str) -> User:
    teacher = get_teacher_or_404(db, teacher_id)
    if _existing_account(db, teacher_id=teacher.teacher_id) is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A login already exists for this teacher",
        )
    user = create_user_for(
        db, email=teacher.email, role="teacher", password=password, teacher_id=teacher.teacher_id
    )
    db.commit()
    db.refresh(user)
    return user


def create_parent_account(db: Session, parent_id, password: str) -> User:
    parent = get_parent_or_404(db, parent_id)
    if _existing_account(db, parent_id=parent.parent_id) is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A login already exists for this parent",
        )
    user = create_user_for(
        db, email=parent.email, role="parent", password=password, parent_id=parent.parent_id
    )
    db.commit()
    db.refresh(user)
    return user


def get_user_or_404(db: Session, user_id) -> User:
    try:
        user = db.get(User, uuid.UUID(str(user_id).strip()))
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


def list_users(db: Session) -> list[User]:
    return db.query(User).order_by(User.email).all()


def update_user_account(
    db: Session, user: User, *, password: str | None = None, active: bool | None = None
) -> User:
    if password is not None:
        user.password_hash = hash_password(password)
    if active is not None:
        user.active = active
    db.commit()
    db.refresh(user)
    return user