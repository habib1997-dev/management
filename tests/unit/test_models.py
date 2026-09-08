"""Unit tests for the data model: creation, constraints, and relationships."""

from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError
from student_management.models import (
    Attendance,
    Course,
    Enrollment,
    Grade,
    Parent,
    Student,
    Teacher,
    User,
)


def test_student_created_with_required_fields(db_session):
    student = Student(
        first_name="John",
        last_name="Doe",
        date_of_birth=date(2010, 5, 15),
        grade_level="9",
    )
    db_session.add(student)
    db_session.commit()
    assert student.student_id is not None
    assert student.active is True
    assert student.enrollment_date == date.today()


def test_student_accepts_custom_grade_level_label(db_session):
    student = Student(
        first_name="John",
        last_name="Doe",
        date_of_birth=date(2010, 5, 15),
        grade_level="K-1",
    )
    db_session.add(student)
    db_session.commit()
    assert student.grade_level == "K-1"


def test_student_email_is_unique(db_session):
    db_session.add(
        Student(
            first_name="John",
            last_name="Doe",
            date_of_birth=date(2010, 5, 15),
            grade_level="9",
            email="john@school.edu",
        )
    )
    db_session.commit()
    db_session.add(
        Student(
            first_name="Jane",
            last_name="Roe",
            date_of_birth=date(2010, 5, 15),
            grade_level="9",
            email="john@school.edu",
        )
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_enrollment_links_to_student(db_session):
    student = Student(
        first_name="John", last_name="Doe", date_of_birth=date(2010, 5, 15), grade_level="9"
    )
    db_session.add(student)
    db_session.flush()
    enrollment = Enrollment(student_id=student.student_id, enrolled_by="Admin")
    db_session.add(enrollment)
    db_session.commit()
    assert enrollment.student is student
    assert student.enrollments[0] is enrollment


def test_teacher_and_course_relationship(db_session):
    teacher = Teacher(name="Jane Smith", email="jane@school.edu")
    db_session.add(teacher)
    db_session.flush()
    course = Course(
        name="Algebra I",
        teacher_id=teacher.teacher_id,
        grade_level="9",
        semester="Fall 2026",
    )
    db_session.add(course)
    db_session.commit()
    assert course.teacher is teacher
    assert teacher.courses == [course]


def test_student_course_many_to_many(db_session):
    teacher = Teacher(name="Jane Smith", email="jane@school.edu")
    db_session.add(teacher)
    db_session.flush()
    course = Course(
        name="Algebra I",
        teacher_id=teacher.teacher_id,
        grade_level="9",
        semester="Fall 2026",
    )
    db_session.add(course)
    db_session.flush()
    student = Student(
        first_name="John", last_name="Doe", date_of_birth=date(2010, 5, 15), grade_level="9"
    )
    db_session.add(student)
    student.courses.append(course)
    db_session.commit()
    assert course.students == [student]
    assert student.courses == [course]


def test_student_parent_many_to_many(db_session):
    student = Student(
        first_name="John", last_name="Doe", date_of_birth=date(2010, 5, 15), grade_level="9"
    )
    db_session.add(student)
    db_session.flush()
    parent = Parent(name="Maria Doe", email="maria@family.net", phone="555-222-3333")
    db_session.add(parent)
    parent.students.append(student)
    db_session.commit()
    assert student.parents == [parent]
    assert parent.students == [student]


def test_attendance_unique_per_student_course_date(db_session):
    teacher = Teacher(name="Jane Smith", email="jane@school.edu")
    db_session.add(teacher)
    db_session.flush()
    course = Course(
        name="Algebra I",
        teacher_id=teacher.teacher_id,
        grade_level="9",
        semester="Fall 2026",
    )
    student = Student(
        first_name="John", last_name="Doe", date_of_birth=date(2010, 5, 15), grade_level="9"
    )
    db_session.add_all([course, student])
    db_session.flush()
    db_session.add(
        Attendance(
            student_id=student.student_id,
            course_id=course.course_id,
            date=date(2026, 9, 7),
            status="present",
            marked_by=teacher.teacher_id,
        )
    )
    db_session.commit()
    db_session.add(
        Attendance(
            student_id=student.student_id,
            course_id=course.course_id,
            date=date(2026, 9, 7),
            status="absent",
            marked_by=teacher.teacher_id,
        )
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_grade_value_must_be_between_0_and_100(db_session):
    teacher = Teacher(name="Jane Smith", email="jane@school.edu")
    db_session.add(teacher)
    db_session.flush()
    course = Course(
        name="Algebra I",
        teacher_id=teacher.teacher_id,
        grade_level="9",
        semester="Fall 2026",
    )
    student = Student(
        first_name="John", last_name="Doe", date_of_birth=date(2010, 5, 15), grade_level="9"
    )
    db_session.add_all([course, student])
    db_session.flush()
    db_session.add(
        Grade(
            student_id=student.student_id,
            course_id=course.course_id,
            grade_value=101,
            assignment_type="test",
            date_assigned=date(2026, 9, 1),
            date_due=date(2026, 9, 5),
        )
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_user_created_with_role(db_session):
    user = User(email="admin@school.edu", password_hash="hash", role="admin")
    db_session.add(user)
    db_session.commit()
    assert user.user_id is not None
    assert user.active is True