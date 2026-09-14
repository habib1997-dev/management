"""Business logic for grade operations."""

import uuid
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from student_management.models import Course, Grade, Student
from student_management.schemas.grade import GradeCreate, GradeUpdate
from student_management.services.attendance_service import get_student_or_404
from student_management.services.course_service import get_course_or_404

STUDENT_NOT_IN_COURSE = "Student is not assigned to this course"
STUDENT_INACTIVE = "Student is deactivated"
GRADE_NOT_FOUND = "Grade not found"


def get_grade_or_404(db: Session, grade_id) -> Grade:
    try:
        grade = db.get(Grade, uuid.UUID(str(grade_id)))
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=GRADE_NOT_FOUND
        )
    if grade is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=GRADE_NOT_FOUND
        )
    return grade


def _validate_student_for_course(db: Session, student_id, course: Course) -> None:
    student = db.get(Student, student_id)
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Student not found"
        )
    if not student.active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=STUDENT_INACTIVE
        )
    if student not in course.students:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=STUDENT_NOT_IN_COURSE
        )


def record_grade(
    db: Session, payload: GradeCreate, _recorded_by: uuid.UUID | None
) -> Grade:
    course = db.get(Course, payload.course_id)
    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Course not found"
        )

    _validate_student_for_course(db, payload.student_id, course)

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


def update_grade(
    db: Session, grade: Grade, payload: GradeUpdate
) -> Grade:
    """Edit an existing grade in place (student and course stay fixed)."""
    course = grade.course if grade.course is not None else db.get(Course, grade.course_id)
    _validate_student_for_course(db, grade.student_id, course)

    data = payload.model_dump(exclude_unset=True)
    date_assigned = data.get("date_assigned", grade.date_assigned)
    date_due = data.get("date_due", grade.date_due)
    if date_due < date_assigned:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="date_due cannot be before date_assigned",
        )

    if "grade_value" in data:
        grade.grade_value = data["grade_value"]
    if "assignment_type" in data:
        grade.assignment_type = data["assignment_type"].value if data["assignment_type"] else None
    if "date_assigned" in data:
        grade.date_assigned = data["date_assigned"]
    if "date_due" in data:
        grade.date_due = data["date_due"]
        grade.date_graded = max(grade.date_graded, date.today(), data["date_due"])
    db.commit()
    db.refresh(grade)
    return grade


def list_student_grades(
    db: Session,
    student_id,
    course_id: uuid.UUID | None = None,
    course_ids: list[uuid.UUID] | None = None,
) -> list[Grade]:
    get_student_or_404(db, student_id)
    query = db.query(Grade).filter(Grade.student_id == uuid.UUID(str(student_id)))
    if course_id is not None:
        query = query.filter(Grade.course_id == course_id)
    if course_ids:
        query = query.filter(Grade.course_id.in_(course_ids))
    return query.order_by(Grade.date_assigned.desc(), Grade.course_id).all()


def list_course_grades(db: Session, course_id) -> list[Grade]:
    get_course_or_404(db, course_id)
    return (
        db.query(Grade)
        .filter(Grade.course_id == uuid.UUID(str(course_id)))
        .order_by(Grade.student_id, Grade.date_assigned)
        .all()
    )