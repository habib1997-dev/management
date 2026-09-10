"""Large demo-data seed for manual testing.

Adds ~24 students plus teachers, courses, parents, attendance and grades on top
of the base seed (admin + Jane Smith + Maria Doe).

Idempotent: exits early if already seeded (guarded by Alice Cohen's email).

Usage (from the backend/ directory):
    python -m scripts.seed_demo_large
"""

from __future__ import annotations

import sys
import time
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.exc import OperationalError
from student_management.db import Base, SessionLocal, engine
from student_management.models import (
    Attendance,
    Course,
    Grade,
    Parent,
    Student,
    Teacher,
    User,
)
from student_management.models.enums import (
    AssignmentType,
    AttendanceStatus,
    CourseStatus,
)
from student_management.security import hash_password

TEACHER_PASSWORD = "teacher123"
PARENT_PASSWORD = "parent123"
GUARD_EMAIL = "alice.cohen@schoolsystem.com"

NEW_TEACHERS = [
    {
        "name": "Alice Cohen",
        "email": "alice.cohen@schoolsystem.com",
        "subjects": "Science",
    },
    {
        "name": "Bob Thompson",
        "email": "bob.thompson@schoolsystem.com",
        "subjects": "History",
    },
    {
        "name": "Priya Sharma",
        "email": "priya.sharma@schoolsystem.com",
        "subjects": "English",
    },
]

COURSES = [
    ("[DEMO] Algebra II", "9", "Jane Smith"),
    ("[DEMO] Biology", "9", "Alice Cohen"),
    ("[DEMO] Geometry", "10", "Jane Smith"),
    ("[DEMO] World History", "10", "Bob Thompson"),
    ("[DEMO] Physics", "11", "Alice Cohen"),
    ("[DEMO] English Literature", "11", "Priya Sharma"),
]

STUDENTS = {
    "9": [
        ("Ethan", "Miller", 2011, 3, 12),
        ("Sophia", "Rodriguez", 2011, 6, 28),
        ("Liam", "Chen", 2011, 1, 19),
        ("Olivia", "Davis", 2011, 9, 4),
        ("Noah", "Wilson", 2011, 12, 2),
        ("Emma", "Martinez", 2011, 4, 22),
        ("Mason", "Lee", 2011, 7, 9),
        ("Ava", "Brown", 2011, 10, 30),
    ],
    "10": [
        ("Lucas", "Anderson", 2010, 2, 14),
        ("Isabella", "Thomas", 2010, 5, 25),
        ("Benjamin", "Taylor", 2010, 8, 8),
        ("Mia", "Hernandez", 2010, 11, 17),
        ("Alexander", "White", 2010, 1, 30),
        ("Charlotte", "Clark", 2010, 6, 5),
        ("James", "Lewis", 2010, 9, 21),
        ("Amelia", "Robinson", 2010, 12, 11),
    ],
    "11": [
        ("Elijah", "Walker", 2009, 3, 3),
        ("Harper", "Hall", 2009, 7, 15),
        ("Daniel", "Young", 2009, 9, 29),
        ("Sofia", "King", 2009, 4, 1),
        ("Matthew", "Wright", 2009, 8, 19),
        ("Grace", "Scott", 2009, 11, 24),
        ("Samuel", "Green", 2009, 2, 6),
        ("Emily", "Baker", 2009, 10, 8),
    ],
}

# (name, email, phone) -> list of student full names it links to
NEW_PARENTS = [
    ("Rosa Martinez", "rosa.martinez@demo.school", "555-020-1001", ["Liam Chen", "Isabella Thomas"]),
    ("David Nguyen", "david.nguyen@demo.school", "555-020-1002", ["Ethan Miller"]),
    ("Fatima Hassan", "fatima.hassan@demo.school", "555-020-1003", ["Sophia Rodriguez"]),
    ("George Kapoor", "george.kapoor@demo.school", "555-020-1004", ["Lucas Anderson"]),
    ("Hannah Fischer", "hannah.fischer@demo.school", "555-020-1005", ["Elijah Walker"]),
    ("Ivan Petrov", "ivan.petrov@demo.school", "555-020-1006", ["Emily Baker"]),
]

ASSIGNMENTS = [
    (AssignmentType.QUIZ.value, 21, 14),
    (AssignmentType.HOMEWORK.value, 14, 7),
    (AssignmentType.TEST.value, 7, 2),
]


def recent_school_days(n: int, today: date) -> list[date]:
    """Return the last n weekdays up to (and including) yesterday."""
    days: list[date] = []
    cursor = today - timedelta(days=1)
    while len(days) < n:
        if cursor.weekday() < 5:
            days.append(cursor)
        cursor -= timedelta(days=1)
    return days


def already_seeded(session) -> bool:
    return (
        session.query(Teacher).filter(Teacher.email == GUARD_EMAIL).first() is not None
    )


def build(session) -> None:
    teachers: dict[str, Teacher] = {}
    for spec in NEW_TEACHERS:
        teacher = Teacher(
            name=spec["name"],
            email=spec["email"],
            subjects_taught=spec["subjects"],
        )
        session.add(teacher)
        session.flush()
        teachers[spec["name"]] = teacher
        session.add(
            User(
                email=spec["email"],
                password_hash=hash_password(TEACHER_PASSWORD),
                role="teacher",
                teacher_id=teacher.teacher_id,
            )
        )

    jane = session.query(Teacher).filter(Teacher.name == "Jane Smith").first()

    students_by_grade: dict[str, list[Student]] = {}
    n = 0
    for grade, roster in STUDENTS.items():
        bucket: list[Student] = []
        for first, last, year, month, day in roster:
            n += 1
            student = Student(
                first_name=first,
                last_name=last,
                date_of_birth=date(year, month, day),
                grade_level=grade,
                email=f"student{n:02d}@demo.school",
                phone=f"555-010-{n:04d}",
            )
            session.add(student)
            bucket.append(student)
        students_by_grade[grade] = bucket
    session.flush()

    courses: dict[str, Course] = {}
    for name, grade, teacher_name in COURSES:
        teacher = teachers.get(teacher_name) or jane
        course = Course(
            name=name,
            teacher_id=teacher.teacher_id,
            grade_level=grade,
            semester="Fall 2026",
            max_students=30,
            status=CourseStatus.ACTIVE.value,
        )
        course.students = list(students_by_grade[grade])
        session.add(course)
        session.flush()
        courses[name] = course

    parents: list[Parent] = []
    for name, email, phone, child_names in NEW_PARENTS:
        parent = Parent(name=name, email=email, phone=phone)
        parent.students = [
            s for bucket in students_by_grade.values() for s in bucket
            if f"{s.first_name} {s.last_name}" in child_names
        ]
        session.add(parent)
        session.flush()
        parents.append(parent)
        session.add(
            User(
                email=email,
                password_hash=hash_password(PARENT_PASSWORD),
                role="parent",
                parent_id=parent.parent_id,
            )
        )

    today = date.today()
    days = recent_school_days(10, today)
    for course in courses.values():
        roster = course.students
        for day_index, day in enumerate(days):
            for student_index, student in enumerate(roster):
                key = day_index + student_index
                if key % 13 == 0:
                    status = AttendanceStatus.ABSENT.value
                elif key % 7 == 0:
                    status = AttendanceStatus.LATE.value
                elif key % 11 == 0:
                    status = AttendanceStatus.EXCUSED.value
                else:
                    status = AttendanceStatus.PRESENT.value
                session.add(
                    Attendance(
                        student_id=student.student_id,
                        course_id=course.course_id,
                        date=day,
                        status=status,
                        marked_by=course.teacher_id,
                    )
                )

    for name, course in courses.items():
        roster = course.students
        for assigned_offset, (assignment_type, assigned_delta, due_delta) in enumerate(ASSIGNMENTS):
            date_assigned = today - timedelta(days=assigned_delta)
            date_due = today - timedelta(days=due_delta)
            for student_index, student in enumerate(roster):
                value = Decimal(((student_index + assigned_offset) * 7) % 41 + 55)
                session.add(
                    Grade(
                        student_id=student.student_id,
                        course_id=course.course_id,
                        grade_value=value,
                        assignment_type=assignment_type,
                        date_assigned=date_assigned,
                        date_due=date_due,
                        date_graded=date_due,
                    )
                )

    student_count = sum(len(v) for v in students_by_grade.values())
    print(f"{student_count} students created")
    print(f"{len(courses)} courses created")
    print(f"{len(NEW_PARENTS)} parents created ({len(students_by_grade['9'])} + {len(students_by_grade['10'])} + {len(students_by_grade['11'])} per grade)")
    print(f"attendance: {len(days)} school days x {len(courses)} courses")
    print(f"grades: {len(ASSIGNMENTS)} assignments x {len(courses)} courses x 8 students/course")
    print(
        "New logins — teachers: "
        + ", ".join(f"{t['email']} / {TEACHER_PASSWORD}" for t in NEW_TEACHERS)
        + "; parents: "
        + ", ".join(f"{email} / {PARENT_PASSWORD}" for _, email, _, _ in NEW_PARENTS)
    )


def main() -> None:
    import student_management.models  # noqa: F401 - registers all tables

    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        if already_seeded(session):
            print("Demo data already exists (Alice Cohen found) - nothing to do.")
            return
        build(session)
        for attempt in range(5):
            try:
                session.commit()
                print("Committed.")
                return
            except OperationalError:
                session.rollback()
                if attempt == 4:
                    raise
                print("Database briefly locked, retrying...")
                time.sleep(0.5 + attempt)
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())