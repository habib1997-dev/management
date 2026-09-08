"""Shared enumerations used across the data model."""

import enum


class EnrollmentStatus(str, enum.Enum):
    ACTIVE = "active"
    WITHDRAWN = "withdrawn"
    TRANSFERRING = "transferring"


class CourseStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    FULL = "full"


class AttendanceStatus(str, enum.Enum):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    EXCUSED = "excused"


class AssignmentType(str, enum.Enum):
    QUIZ = "quiz"
    TEST = "test"
    HOMEWORK = "homework"
    FINAL = "final"


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    TEACHER = "teacher"
    PARENT = "parent"


GRADE_LEVEL_MAX_LENGTH = 20


def enum_values(values: list[str]) -> str:
    """Render a comma-separated quoted list for check constraints."""
    return ", ".join(f"'{v}'" for v in values)