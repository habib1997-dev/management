"""Attendance entity - one row per student per course per day."""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from student_management.db import Base
from student_management.models.enums import (
    AttendanceStatus,
    enum_values,
)


class Attendance(Base):
    __tablename__ = "attendance"
    __table_args__ = (
        UniqueConstraint(
            "student_id", "course_id", "date", name="uq_attendance_student_course_date"
        ),
        CheckConstraint(
            f"status IN ({enum_values([s.value for s in AttendanceStatus])})",
            name="ck_attendance_status",
        ),
    )

    attendance_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("students.student_id", ondelete="CASCADE"), index=True
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("courses.course_id", ondelete="CASCADE"), index=True
    )
    date: Mapped[date] = mapped_column(Date, index=True)
    status: Mapped[str] = mapped_column(String(10))
    marked_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("teachers.teacher_id"), nullable=True
    )

    student: Mapped["Student"] = relationship(back_populates="attendance_records")
    course: Mapped["Course"] = relationship(back_populates="attendance_records")
    teacher: Mapped["Teacher"] = relationship(
        back_populates="attendance_records", foreign_keys=[marked_by]
    )

    def __repr__(self) -> str:
        return f"<Attendance {self.student_id} {self.course_id} {self.date}: {self.status}>"