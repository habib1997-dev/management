"""Business logic for parent operations."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from student_management.models import Parent, Student, User
from student_management.schemas.parent import ParentCreate, ParentUpdate
from student_management.security import hash_password
from student_management.services.attendance_service import get_student_or_404

STUDENT_MISSING = "One or more students not found"


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

    parent = Parent(
        name=payload.name.strip(),
        email=payload.email.lower(),
        phone=payload.phone,
    )
    if payload.student_ids:
        students = []
        for sid in payload.student_ids:
            try:
                student = db.get(Student, uuid.UUID(str(sid)))
            except (ValueError, AttributeError):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail=STUDENT_MISSING
                )
            if student is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail=STUDENT_MISSING
                )
            students.append(student)
        parent.students = students

    db.add(parent)
    if payload.password:
        db.flush()
        db.add(
            User(
                email=payload.email.lower(),
                password_hash=hash_password(payload.password),
                role="parent",
                parent_id=parent.parent_id,
            )
        )
    db.commit()
    db.refresh(parent)
    return parent


def list_parents(db: Session) -> list[Parent]:
    return db.query(Parent).order_by(Parent.name).all()


def update_parent(db: Session, parent: Parent, payload: ParentUpdate) -> Parent:
    data = payload.model_dump(exclude_unset=True)
    email = data.get("email")
    if email is not None:
        existing = (
            db.query(Parent)
            .filter(
                Parent.parent_id != parent.parent_id,
                func.lower(Parent.email) == email.lower(),
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A parent with this email already exists",
            )
        data["email"] = email.lower()
    if data.get("name"):
        data["name"] = data["name"].strip()
    for field, value in data.items():
        if value is not None:
            setattr(parent, field, value)
    db.flush()
    if "status" in data:
        user = db.query(User).filter(User.parent_id == parent.parent_id).first()
        if user is not None:
            user.active = data["status"]
    db.commit()
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
    students = []
    for sid in student_ids:
        try:
            student = db.get(Student, uuid.UUID(str(sid)))
        except (ValueError, AttributeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=STUDENT_MISSING
            )
        if student is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=STUDENT_MISSING
            )
        students.append(student)
    parent.students = students
    db.commit()
    db.refresh(parent)
    return parent