"""Development seed script.

Creates an admin account (and, with --demo, sample data for trying the system).

No passwords are committed to the repository. Passwords come from the
environment:

    ADMIN_PASSWORD        admin login   (admin@schoolsystem.com)
    DEMO_TEACHER_PASSWORD demo teacher  (jane.smith@schoolsystem.com)
    DEMO_PARENT_PASSWORD  demo parent   (maria.doe@family.net)

Without the env vars the seed aborts; add ``--interactive`` to be prompted for
the missing passwords on a terminal instead.

Usage:
    python -m scripts.seed                 # admin only
    python -m scripts.seed --demo          # admin + sample students/teacher/course/parents
    python -m scripts.seed --demo --interactive   # prompt for any missing password
"""

from __future__ import annotations

import getpass
import os
import sys
from datetime import date

from student_management.db import Base, SessionLocal, engine
from student_management.models import Course, Parent, Student, Teacher, User
from student_management.security import hash_password

ADMIN_EMAIL = "admin@schoolsystem.com"
DEMO_TEACHER_LOGIN = ("jane.smith@schoolsystem.com", "Demo teacher")
DEMO_PARENT_LOGIN = ("maria.doe@family.net", "Demo parent")


def _read_password(name: str, prompt: str) -> str:
    """Return the password from the ``name`` env var (no committed defaults).

    If it is missing, prompt for it only when ``--interactive`` was passed and
    stdin is a terminal; otherwise abort so non-interactive runs never hang.
    """
    value = (os.environ.get(name) or "").strip()
    if not value and "--interactive" in sys.argv and sys.stdin.isatty():
        try:
            value = (getpass.getpass(prompt) or "").strip()
        except EOFError:
            value = ""
    if not value:
        raise SystemExit(
            f"{name} is not set — supply it via the environment "
            "(or run with --interactive to be prompted). Aborting."
        )
    return value


def ensure_schema() -> None:
    """Create tables if they do not exist (development convenience)."""
    import student_management.models  # noqa: F401 - registers all tables

    Base.metadata.create_all(bind=engine)


def seed_admin(session, password: str | None = None) -> User:
    email = (os.environ.get("ADMIN_EMAIL") or ADMIN_EMAIL).strip()
    password = password or _read_password("ADMIN_PASSWORD", "Admin password (hidden): ")
    admin = session.query(User).filter(User.email == email.lower()).first()
    if admin is None:
        admin = User(
            email=email.lower(),
            password_hash=hash_password(password),
            role="admin",
        )
        session.add(admin)
        session.flush()
        print(f"Created admin account: {email}")
    else:
        print(f"Admin account already exists: {email} (password left unchanged)")
    return admin


def seed_demo(session) -> None:
    teacher = Teacher(name="Jane Smith", email=DEMO_TEACHER_LOGIN[0], subjects_taught="Mathematics")
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

    teacher_password = _read_password("DEMO_TEACHER_PASSWORD", f"{DEMO_TEACHER_LOGIN[1]} password (hidden): ")
    teacher_user = User(
        email=DEMO_TEACHER_LOGIN[0],
        password_hash=hash_password(teacher_password),
        role="teacher",
        teacher_id=teacher.teacher_id,
    )
    session.add(teacher_user)

    parent = Parent(name="Maria Doe", email=DEMO_PARENT_LOGIN[0], phone="555-222-3333")
    session.add(parent)
    parent.students.append(students[0])
    session.flush()

    parent_password = _read_password("DEMO_PARENT_PASSWORD", f"{DEMO_PARENT_LOGIN[1]} password (hidden): ")
    parent_user = User(
        email=DEMO_PARENT_LOGIN[0],
        password_hash=hash_password(parent_password),
        role="parent",
        parent_id=parent.parent_id,
    )
    session.add(parent_user)
    print(
        "Demo data created.\n"
        f"Teacher: {DEMO_TEACHER_LOGIN[0]}\n"
        f"Parent: {DEMO_PARENT_LOGIN[0]}\n"
        "(passwords are the ones you supplied via the DEMO_* env vars / prompt)"
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