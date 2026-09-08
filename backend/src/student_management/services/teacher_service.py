"""Business logic for teacher operations."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from student_management.models import Teacher, User
from student_management.schemas.teacher import TeacherCreate, TeacherUpdate
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


def update_teacher(db: Session, teacher: Teacher, payload: TeacherUpdate) -> Teacher:
    data = payload.model_dump(exclude_unset=True)
    email = data.get("email")
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
        data["email"] = email.lower()
    if data.get("name"):
        data["name"] = data["name"].strip()
    if "subjects_taught" in data:
        data["subjects_taught"] = (data["subjects_taught"] or "").strip() or None
    for field, value in data.items():
        if field == "subjects_taught":
            setattr(teacher, field, data["subjects_taught"])
        elif value is not None:
            setattr(teacher, field, value)
    db.flush()
    if "status" in data:
        user = db.query(User).filter(User.teacher_id == teacher.teacher_id).first()
        if user is not None:
            user.active = data["status"]
    db.commit()
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