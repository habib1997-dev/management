"""Business logic for student and enrollment operations."""

import uuid
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from student_management.models import Enrollment, Student
from student_management.schemas.enrollment import EnrollmentCreate
from student_management.schemas.student import StudentEnrollment, StudentUpdate


def get_student_or_404(db: Session, student_id: uuid.UUID) -> Student:
    try:
        student = db.get(Student, uuid.UUID(str(student_id)))
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Student not found"
        )
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Student not found"
        )
    return student


def create_student(
    db: Session, payload: StudentEnrollment, enrolled_by: str
) -> Student:
    if payload.email:
        existing = (
            db.query(Student)
            .filter(func.lower(Student.email) == payload.email.lower())
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A student with this email already exists",
            )
    student = Student(
        first_name=payload.first_name.strip(),
        last_name=payload.last_name.strip(),
        date_of_birth=payload.date_of_birth,
        grade_level=payload.grade_level,
        email=payload.email.lower() if payload.email else None,
        phone=payload.phone,
        enrollment_date=date.today(),
    )
    db.add(student)
    db.flush()
    db.add(
        Enrollment(
            student_id=student.student_id,
            enrolled_by=enrolled_by,
            enrollment_date=student.enrollment_date,
        )
    )
    db.commit()
    db.refresh(student)
    return student


def list_students(
    db: Session,
    page: int,
    page_size: int,
    search: str | None,
    grade_level: str | None,
    active: bool | None,
) -> tuple[list[Student], int]:
    query = db.query(Student)
    if search:
        term = f"%{search.strip().lower()}%"
        query = query.filter(
            or_(
                func.lower(Student.first_name).like(term),
                func.lower(Student.last_name).like(term),
            )
        )
    if grade_level:
        query = query.filter(Student.grade_level == grade_level)
    if active is not None:
        query = query.filter(Student.active == active)

    total = query.count()
    items = (
        query.order_by(Student.last_name, Student.first_name)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items, total


def update_student(db: Session, student: Student, payload: StudentUpdate) -> Student:
    if payload.email is not None:
        existing = (
            db.query(Student)
            .filter(
                Student.student_id != student.student_id,
                func.lower(Student.email) == payload.email.lower(),
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A student with this email already exists",
            )
    data = payload.model_dump(exclude_unset=True)
    if data.get("email"):
        data["email"] = data["email"].lower()
    for field, value in data.items():
        if value is not None:
            setattr(student, field, value)
    db.commit()
    db.refresh(student)
    return student


def create_enrollment(db: Session, payload: EnrollmentCreate) -> Enrollment:
    get_student_or_404(db, payload.student_id)
    enrollment = Enrollment(
        student_id=payload.student_id,
        enrolled_by=payload.enrolled_by,
        enrollment_date=date.today(),
        status=payload.status.value,
    )
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return enrollment