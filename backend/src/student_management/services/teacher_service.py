"""Business logic for teacher operations."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from student_management.models import Teacher, User
from student_management.schemas.teacher import TeacherCreate, TeacherUpdate
from student_management.security import hash_password
from student_management.services.commit import commit_or_conflict, flush_or_conflict
from student_management.services.user_accounts import (
    assert_email_free,
    user_email_taken,
    user_for_teacher,
)


def get_teacher_or_404(db: Session, teacher_id) -> Teacher:
    try:
        teacher = db.get(Teacher, uuid.UUID(str(teacher_id)))
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found"
        )
    if teacher is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found"
        )
    return teacher


def create_teacher(db: Session, payload: TeacherCreate) -> Teacher:
    existing = (
        db.query(Teacher).filter(func.lower(Teacher.email) == payload.email.lower()).first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A teacher with this email already exists",
        )
    if user_email_taken(db, payload.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This email is already used by a login account",
        )
    teacher = Teacher(
        name=payload.name.strip(),
        email=payload.email.lower(),
        subjects_taught=payload.subjects_taught.strip() if payload.subjects_taught else None,
    )
    db.add(teacher)
    if payload.password:
        flush_or_conflict(db)
        db.add(
            User(
                email=payload.email.lower(),
                password_hash=hash_password(payload.password),
                role="teacher",
                teacher_id=teacher.teacher_id,
            )
        )
    commit_or_conflict(db)
    db.refresh(teacher)
    return teacher


def list_teachers(db: Session) -> list[Teacher]:
    return db.query(Teacher).order_by(Teacher.name).all()


def update_teacher(db: Session, teacher: Teacher, payload: TeacherUpdate) -> Teacher:
    data = payload.model_dump(exclude_unset=True)
    email = data.get("email")
    linked_user = user_for_teacher(db, teacher.teacher_id)
    if email is not None:
        existing = (
            db.query(Teacher)
            .filter(
                Teacher.teacher_id != teacher.teacher_id,
                func.lower(Teacher.email) == email.lower(),
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A teacher with this email already exists",
            )
        assert_email_free(
            db, email, exclude_user_id=linked_user.user_id if linked_user else None
        )
        data["email"] = email.lower()
        if linked_user is not None:
            linked_user.email = email.lower()
    if data.get("name"):
        data["name"] = data["name"].strip()
    if "subjects_taught" in data:
        data["subjects_taught"] = (data["subjects_taught"] or "").strip() or None
    password = data.pop("password", None)
    if password is not None:
        user = linked_user or user_for_teacher(db, teacher.teacher_id)
        new_email = str(data.get("email", teacher.email)).lower()
        if user is None:
            user = User(
                email=new_email,
                password_hash=hash_password(password),
                role="teacher",
                teacher_id=teacher.teacher_id,
            )
            db.add(user)
        else:
            user.password_hash = hash_password(password)
            user.email = new_email
            user.auth_version += 1
    for field, value in data.items():
        if field == "subjects_taught":
            setattr(teacher, field, data["subjects_taught"])
        elif value is not None:
            setattr(teacher, field, value)
    flush_or_conflict(db)
    if "status" in data:
        user = user_for_teacher(db, teacher.teacher_id)
        if user is not None:
            user.active = data["status"]
    commit_or_conflict(db)
    db.refresh(teacher)
    return teacher


def get_teacher_with_courses(db: Session, teacher_id) -> Teacher:
    teacher = get_teacher_or_404(db, teacher_id)
    return (
        db.query(Teacher)
        .options(selectinload(Teacher.courses))
        .filter(Teacher.teacher_id == teacher.teacher_id)
        .first()
    )