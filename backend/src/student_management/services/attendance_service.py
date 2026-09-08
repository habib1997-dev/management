"""Business logic for attendance operations."""

import uuid
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from student_management.models import Attendance, Course, Student
from student_management.schemas.attendance import AttendanceCreate

STUDENT_MISSING = "One or more students not found"
STUDENT_NOT_IN_COURSE = "One or more students are not assigned to this course"
STUDENT_INACTIVE = "One or more students are deactivated"
DUPLICATE_STUDENT = "Duplicate student entries are not allowed"


def mark_attendance(
    db: Session, payload: AttendanceCreate, marked_by: uuid.UUID | None
) -> list[Attendance]:
    course = db.get(Course, payload.course_id)
    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Course not found"
        )

    student_ids = [r.student_id for r in payload.records]
    if len(student_ids) != len(set(student_ids)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=DUPLICATE_STUDENT
        )

    roster = {s.student_id for s in course.students}
    for record in payload.records:
        student = db.get(Student, record.student_id)
        if student is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=STUDENT_MISSING
            )
        if not student.active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=STUDENT_INACTIVE
            )
        if record.student_id not in roster:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=STUDENT_NOT_IN_COURSE
            )

    attendance = []
    for record in payload.records:
        existing = (
            db.query(Attendance)
            .filter(
                Attendance.student_id == record.student_id,
                Attendance.course_id == payload.course_id,
                Attendance.date == payload.date,
            )
            .first()
        )
        if existing is not None:
            existing.status = record.status.value
            existing.marked_by = marked_by
            attendance.append(existing)
        else:
            entry = Attendance(
                student_id=record.student_id,
                course_id=payload.course_id,
                date=payload.date,
                status=record.status.value,
                marked_by=marked_by,
            )
            db.add(entry)
            attendance.append(entry)

    db.commit()
    for entry in attendance:
        db.refresh(entry)
    return attendance


def list_course_attendance(
    db: Session, course_id, date_: date | None = None
) -> list[Attendance]:
    query = db.query(Attendance).filter(Attendance.course_id == uuid.UUID(str(course_id)))
    if date_ is not None:
        query = query.filter(Attendance.date == date_)
    return query.order_by(Attendance.date.desc(), Attendance.student_id).all()


def get_student_or_404(db: Session, student_id) -> Student:
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


def list_student_attendance(db: Session, student_id) -> list[Attendance]:
    get_student_or_404(db, student_id)
    return (
        db.query(Attendance)
        .filter(Attendance.student_id == uuid.UUID(str(student_id)))
        .order_by(Attendance.course_id, Attendance.date)
        .all()
    )


def student_in_teacher_courses(db: Session, student_id, teacher_id) -> bool:
    """True if the given teacher teaches a course the student is assigned to."""
    if teacher_id is None:
        return False
    count = (
        db.query(Course)
        .join(Course.students)
        .filter(
            Course.teacher_id == teacher_id,
            Student.student_id == uuid.UUID(str(student_id)),
        )
        .count()
    )
    return count > 0