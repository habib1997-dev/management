"""Business logic for parent operations."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from student_management.models import Parent, Student, User
from student_management.schemas.parent import ParentCreate, ParentUpdate
from student_management.security import hash_password
from student_management.services.attendance_service import get_student_or_404
from student_management.services.commit import commit_or_conflict, flush_or_conflict
from student_management.services.user_accounts import (
    assert_email_free,
    user_email_taken,
    user_for_parent,
)

STUDENT_MISSING = "One or more students not found"


def _resolve_students(db: Session, student_ids: list) -> list[Student]:
    """Resolve student ids in ONE batched query (no per-id N+1 lookups)."""
    ids = []
    seen: set[uuid.UUID] = set()
    for sid in student_ids:
        try:
            u = uuid.UUID(str(sid))
        except (ValueError, AttributeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=STUDENT_MISSING
            )
        if u in seen:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Duplicate student IDs are not allowed",
            )
        seen.add(u)
        ids.append(u)
    if not ids:
        return []
    students = db.query(Student).filter(Student.student_id.in_(ids)).all()
    if len(students) != len(ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=STUDENT_MISSING
        )
    return students


def get_parent_or_404(db: Session, parent_id) -> Parent:
    try:
        parent = db.get(Parent, uuid.UUID(str(parent_id).strip()))
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Parent not found"
        )
    if parent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Parent not found"
        )
    return parent


def create_parent(db: Session, payload: ParentCreate) -> Parent:
    existing = (
        db.query(Parent)
        .filter(func.lower(Parent.email) == payload.email.lower())
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A parent with this email already exists",
        )
    if user_email_taken(db, payload.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This email is already used by a login account",
        )

    parent = Parent(
        name=payload.name.strip(),
        email=payload.email.lower(),
        phone=payload.phone,
    )
    if payload.student_ids:
        parent.students = _resolve_students(db, payload.student_ids)

    db.add(parent)
    if payload.password:
        flush_or_conflict(db)
        db.add(
            User(
                email=payload.email.lower(),
                password_hash=hash_password(payload.password),
                role="parent",
                parent_id=parent.parent_id,
            )
        )
    commit_or_conflict(db)
    db.refresh(parent)
    return parent


def list_parents(db: Session) -> list[Parent]:
    return db.query(Parent).order_by(Parent.name).all()


def _parent_email_conflict(db: Session, parent: Parent, email: str) -> bool:
    return (
        db.query(Parent)
        .filter(
            Parent.parent_id != parent.parent_id,
            func.lower(Parent.email) == email.lower(),
        )
        .first()
        is not None
    )


def _apply_email_update(
    db: Session, parent: Parent, data: dict, linked_user: User | None
) -> tuple[dict, User | None]:
    email = data.get("email")
    if email is None:
        return data, linked_user
    if _parent_email_conflict(db, parent, email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A parent with this email already exists",
        )
    assert_email_free(
        db, email, exclude_user_id=linked_user.user_id if linked_user else None
    )
    data["email"] = email.lower()
    if linked_user is not None:
        linked_user.email = email.lower()
    return data, linked_user


def _apply_password_update(
    db: Session, parent: Parent, data: dict, linked_user: User | None
) -> None:
    password = data.pop("password", None)
    if password is None:
        return
    new_email = str(data.get("email", parent.email)).lower()
    if linked_user is None:
        linked_user = User(
            email=new_email,
            password_hash=hash_password(password),
            role="parent",
            parent_id=parent.parent_id,
        )
        db.add(linked_user)
    else:
        linked_user.password_hash = hash_password(password)
        linked_user.email = new_email
        linked_user.auth_version += 1


def _apply_fields(parent: Parent, data: dict) -> None:
    for field, value in data.items():
        if value is not None:
            setattr(parent, field, value)


def update_parent(db: Session, parent: Parent, payload: ParentUpdate) -> Parent:
    data = payload.model_dump(exclude_unset=True)
    linked_user = user_for_parent(db, parent.parent_id)
    data, linked_user = _apply_email_update(db, parent, data, linked_user)
    if data.get("name"):
        data["name"] = data["name"].strip()
    _apply_password_update(db, parent, data, linked_user)
    _apply_fields(parent, data)
    flush_or_conflict(db)
    if "status" in data:
        user = user_for_parent(db, parent.parent_id)
        if user is not None:
            user.active = data["status"]
    commit_or_conflict(db)
    db.refresh(parent)
    return parent


def get_parent_with_children(db: Session, parent_id) -> Parent:
    parent = get_parent_or_404(db, parent_id)
    return (
        db.query(Parent)
        .options(
            selectinload(Parent.students).selectinload(Student.attendance_records),
            selectinload(Parent.students).selectinload(Student.grades),
        )
        .filter(Parent.parent_id == parent.parent_id)
        .first()
    )


def list_parent_students(db: Session, parent_id) -> list[Student]:
    get_parent_or_404(db, parent_id)
    return (
        db.query(Student)
        .join(Student.parents)
        .filter(Parent.parent_id == uuid.UUID(str(parent_id).strip()))
        .order_by(Student.last_name, Student.first_name)
        .all()
    )


def list_student_parents(db: Session, student_id) -> list[Parent]:
    """All parents linked to a student (data-model required query)."""
    get_student_or_404(db, student_id)
    return (
        db.query(Parent)
        .join(Parent.students)
        .filter(Student.student_id == uuid.UUID(str(student_id)))
        .order_by(Parent.name)
        .all()
    )


def update_parent_students(
    db: Session, parent: Parent, student_ids: list
) -> Parent:
    """Replace the parent's linked children (swap pattern like course roster)."""
    parent.students = _resolve_students(db, student_ids)
    db.commit()
    db.refresh(parent)
    return parent