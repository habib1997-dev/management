"""Business logic for grade operations."""

import uuid
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from student_management.models import Course, Grade, Student
from student_management.schemas.grade import GradeCreate
from student_management.services.attendance_service import get_student_or_404
from student_management.services.course_service import get_course_or_404

STUDENT_NOT_IN_COURSE = "Student is not assigned to this course"


def record_grade(
    db: Session, payload: GradeCreate, recorded_by: uuid.UUID | None
) -> Grade:
    course = db.get(Course, payload.course_id)
    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Course not found"
        )

    student = db.get(Student, payload.student_id)
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Student not found"
        )

    if student not in course.students:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=STUDENT_NOT_IN_COURSE
        )

    grade = Grade(
        student_id=payload.student_id,
        course_id=payload.course_id,
        grade_value=payload.grade_value,
        assignment_type=(
            payload.assignment_type.value if payload.assignment_type else None
        ),
        date_assigned=payload.date_assigned,
        date_due=payload.date_due,
        date_graded=max(date.today(), payload.date_due),
    )
    db.add(grade)
    db.commit()
    db.refresh(grade)
    return grade


def list_student_grades(
    db: Session, student_id, course_id: uuid.UUID | None = None
) -> list[Grade]:
    get_student_or_404(db, student_id)
    query = db.query(Grade).filter(Grade.student_id == uuid.UUID(str(student_id)))
    if course_id is not None:
        query = query.filter(Grade.course_id == course_id)
    return query.order_by(Grade.date_assigned.desc(), Grade.course_id).all()


def list_course_grades(db: Session, course_id) -> list[Grade]:
    get_course_or_404(db, course_id)
    return (
        db.query(Grade)
        .filter(Grade.course_id == uuid.UUID(str(course_id)))
        .order_by(Grade.student_id, Grade.date_assigned)
        .all()
    )