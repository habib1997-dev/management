"""Development seed script.

Creates an admin account (and, with --demo, sample data for trying the system).

Usage:
    python -m scripts.seed                 # admin only
    python -m scripts.seed --demo          # admin + sample students/teacher/course/parents
"""

from __future__ import annotations

import sys
from datetime import date

from student_management.db import Base, SessionLocal, engine
from student_management.models import Course, Parent, Student, Teacher, User
from student_management.security import hash_password

DEFAULT_ADMIN = {"email": "admin@schoolsystem.com", "password": "changeme123"}


def ensure_schema() -> None:
    """Create tables if they do not exist (development convenience)."""
    import student_management.models  # noqa: F401 - registers all tables

    Base.metadata.create_all(bind=engine)


def seed_admin(session) -> User:
    admin = (
        session.query(User)
        .filter(User.email == DEFAULT_ADMIN["email"].lower())
        .first()
    )
    if admin is None:
        admin = User(
            email=DEFAULT_ADMIN["email"],
            password_hash=hash_password(DEFAULT_ADMIN["password"]),
            role="admin",
        )
        session.add(admin)
        session.flush()
        print(f"Created admin account: {DEFAULT_ADMIN['email']} / {DEFAULT_ADMIN['password']}")
    else:
        print(f"Admin account already exists: {DEFAULT_ADMIN['email']}")
    return admin


def seed_demo(session) -> None:
    teacher = Teacher(name="Jane Smith", email="jane.smith@schoolsystem.com", subjects_taught="Mathematics")
    session.add(teacher)
    session.flush()

    course = Course(
        name="Algebra I",
        teacher_id=teacher.teacher_id,
        grade_level="9",
        semester="Fall 2026",
    )
    session.add(course)
    session.flush()

    students = [
        Student(
            first_name="John",
            last_name="Doe",
            date_of_birth=date(2010, 5, 15),
            grade_level="9",
            email="john.doe@schoolsystem.com",
            phone="555-123-4567",
        ),
        Student(
            first_name="Maria",
            last_name="Garcia",
            date_of_birth=date(2010, 11, 2),
            grade_level="9",
            email="maria.garcia@schoolsystem.com",
            phone="555-111-2222",
        ),
    ]
    session.add_all(students)
    session.flush()
    for student in students:
        student.courses.append(course)

    teacher_user = User(
        email="jane.smith@schoolsystem.com",
        password_hash=hash_password("teacher123"),
        role="teacher",
        teacher_id=teacher.teacher_id,
    )
    session.add(teacher_user)

    parent = Parent(name="Maria Doe", email="maria.doe@family.net", phone="555-222-3333")
    session.add(parent)
    parent.students.append(students[0])
    session.flush()

    parent_user = User(
        email="maria.doe@family.net",
        password_hash=hash_password("parent123"),
        role="parent",
        parent_id=parent.parent_id,
    )
    session.add(parent_user)
    print(
        "Demo data created. Teacher: jane.smith@schoolsystem.com / teacher123\n"
        "Parent: maria.doe@family.net / parent123"
    )


def main() -> None:
    demo = "--demo" in sys.argv
    ensure_schema()
    session = SessionLocal()
    try:
        seed_admin(session)
        if demo:
            seed_demo(session)
        session.commit()
    finally:
        session.close()


if __name__ == "__main__":
    main()