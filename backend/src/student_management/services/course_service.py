"""Business logic for course operations."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, selectinload

from student_management.models import Course, Student, Teacher
from student_management.schemas.course import CourseCreate, CourseUpdate


def get_course_or_404(db: Session, course_id) -> Course:
    try:
        course = db.get(Course, uuid.UUID(str(course_id).strip()))
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Course not found"
        )
    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Course not found"
        )
    return course


def _validate_teacher(db: Session, teacher_id) -> Teacher:
    teacher = db.get(Teacher, teacher_id)
    if teacher is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Teacher not found",
        )
    if not teacher.status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot assign an inactive teacher",
        )
    return teacher


def create_course(db: Session, payload: CourseCreate) -> Course:
    _validate_teacher(db, payload.teacher_id)
    course = Course(
        name=payload.name.strip(),
        teacher_id=payload.teacher_id,
        grade_level=payload.grade_level,
        semester=payload.semester.strip(),
        max_students=payload.max_students,
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


def list_courses(
    db: Session,
    teacher_id: str | None,
    grade_level: str | None,
    own_teacher_id: uuid.UUID | None = None,
) -> list[Course]:
    query = db.query(Course)
    if own_teacher_id is not None:
        query = query.filter(Course.teacher_id == own_teacher_id)
    elif teacher_id:
        query = query.filter(Course.teacher_id == uuid.UUID(teacher_id))
    if grade_level:
        query = query.filter(Course.grade_level == grade_level)
    return query.order_by(Course.name).all()


def get_course_with_reads(db: Session, course_id) -> Course:
    course = get_course_or_404(db, course_id)
    return (
        db.query(Course)
        .options(selectinload(Course.students))
        .filter(Course.course_id == course.course_id)
        .first()
    )


def update_course(db: Session, course: Course, payload: CourseUpdate) -> Course:
    data = payload.model_dump(exclude_unset=True)
    if "teacher_id" in data and data["teacher_id"] is not None:
        _validate_teacher(db, data["teacher_id"])
    for field, value in data.items():
        if value is not None:
            setattr(course, field, value)
    db.commit()
    db.refresh(course)
    return course


def list_course_students(db: Session, course_id) -> list[Student]:
    course = get_course_or_404(db, course_id)
    return (
        db.query(Student)
        .join(Student.courses)
        .filter(Course.course_id == course.course_id)
        .order_by(Student.last_name, Student.first_name)
        .all()
    )


def assign_course_students(db: Session, course: Course, student_ids: list) -> Course:
    """Replace the course roster (link students to the course).

    Enforces the course's max_students capacity.
    """
    if course.max_students is not None and len(student_ids) > course.max_students:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Course capacity exceeded (max {course.max_students})",
        )
    students = []
    for sid in student_ids:
        try:
            student = db.get(Student, uuid.UUID(str(sid)))
        except (ValueError, AttributeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more student IDs are invalid",
            )
        if student is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more students not found",
            )
        students.append(student)
    course.students = students
    db.commit()
    db.refresh(course)
    return course