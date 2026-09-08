"""Student entity."""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import Boolean, Date, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from student_management.db import Base
from student_management.models.enums import GRADE_LEVEL_MAX_LENGTH


class Student(Base):
    __tablename__ = "students"

    student_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    first_name: Mapped[str] = mapped_column(String(100), index=True)
    last_name: Mapped[str] = mapped_column(String(100), index=True)
    date_of_birth: Mapped[date] = mapped_column(Date)
    grade_level: Mapped[str] = mapped_column(String(GRADE_LEVEL_MAX_LENGTH))
    enrollment_date: Mapped[date] = mapped_column(Date, default=date.today)
    email: Mapped[str | None] = mapped_column(String(200), unique=True, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    enrollments: Mapped[list["Enrollment"]] = relationship(back_populates="student")
    attendance_records: Mapped[list["Attendance"]] = relationship(back_populates="student")
    grades: Mapped[list["Grade"]] = relationship(back_populates="student")
    courses: Mapped[list["Course"]] = relationship(
        secondary="student_courses", back_populates="students"
    )
    parents: Mapped[list["Parent"]] = relationship(
        secondary="parent_students", back_populates="students"
    )

    def __repr__(self) -> str:
        return f"<Student {self.first_name} {self.last_name}>"