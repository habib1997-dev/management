"""Course entity."""

from __future__ import annotations

import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from student_management.db import Base
from student_management.models.enums import (
    GRADE_LEVEL_MAX_LENGTH,
    CourseStatus,
    enum_values,
)


class Course(Base):
    __tablename__ = "courses"
    __table_args__ = (
        CheckConstraint(
            f"status IN ({enum_values([s.value for s in CourseStatus])})",
            name="ck_courses_status",
        ),
    )

    course_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100))
    teacher_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("teachers.teacher_id"), index=True
    )
    grade_level: Mapped[str] = mapped_column(String(GRADE_LEVEL_MAX_LENGTH))
    semester: Mapped[str] = mapped_column(String(20))
    max_students: Mapped[int] = mapped_column(Integer, default=30)
    status: Mapped[str] = mapped_column(String(20), default=CourseStatus.ACTIVE.value)

    teacher: Mapped["Teacher"] = relationship(
        back_populates="courses", foreign_keys=[teacher_id]
    )
    students: Mapped[list["Student"]] = relationship(
        secondary="student_courses", back_populates="courses"
    )
    attendance_records: Mapped[list["Attendance"]] = relationship(back_populates="course")
    grades: Mapped[list["Grade"]] = relationship(back_populates="course")

    def __repr__(self) -> str:
        return f"<Course {self.name}>"