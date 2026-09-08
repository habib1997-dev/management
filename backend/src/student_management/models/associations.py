"""Association tables for many-to-many relationships."""

from __future__ import annotations

from datetime import date

from sqlalchemy import Column, Date, ForeignKey, Table, Uuid

from student_management.db import Base

student_courses = Table(
    "student_courses",
    Base.metadata,
    Column(
        "student_id",
        Uuid,
        ForeignKey("students.student_id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "course_id",
        Uuid,
        ForeignKey("courses.course_id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("enrolled_date", Date, default=date.today),
)

parent_students = Table(
    "parent_students",
    Base.metadata,
    Column(
        "parent_id",
        Uuid,
        ForeignKey("parents.parent_id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "student_id",
        Uuid,
        ForeignKey("students.student_id", ondelete="CASCADE"),
        primary_key=True,
    ),
)