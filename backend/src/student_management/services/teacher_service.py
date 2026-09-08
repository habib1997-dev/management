"""Business logic for teacher operations."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from student_management.models import Teacher, User
from student_management.schemas.teacher import TeacherCreate
from student_management.security import hash_password


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
    teacher = Teacher(
        name=payload.name.strip(),
        email=payload.email.lower(),
        subjects_taught=payload.subjects_taught.strip() if payload.subjects_taught else None,
    )
    db.add(teacher)
    if payload.password:
        db.flush()
        db.add(
            User(
                email=payload.email.lower(),
                password_hash=hash_password(payload.password),
                role="teacher",
                teacher_id=teacher.teacher_id,
            )
        )
    db.commit()
    db.refresh(teacher)
    return teacher


def list_teachers(db: Session) -> list[Teacher]:
    return db.query(Teacher).order_by(Teacher.name).all()


def get_teacher_with_courses(db: Session, teacher_id) -> Teacher:
    teacher = get_teacher_or_404(db, teacher_id)
    return (
        db.query(Teacher)
        .options(selectinload(Teacher.courses))
        .filter(Teacher.teacher_id == teacher.teacher_id)
        .first()
    )