"""Enrollment entity - registers a student into the system with administrative oversight."""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import CheckConstraint, Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from student_management.db import Base
from student_management.models.enums import (
    EnrollmentStatus,
    enum_values,
)


class Enrollment(Base):
    __tablename__ = "enrollments"
    __table_args__ = (
        CheckConstraint(
            f"status IN ({enum_values([s.value for s in EnrollmentStatus])})",
            name="ck_enrollments_status",
        ),
    )

    enrollment_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("students.student_id", ondelete="CASCADE"), index=True
    )
    enrolled_by: Mapped[str] = mapped_column(String(100))
    enrollment_date: Mapped[date] = mapped_column(Date, default=date.today)
    status: Mapped[str] = mapped_column(String(20), default=EnrollmentStatus.ACTIVE.value)

    student: Mapped["Student"] = relationship(back_populates="enrollments")

    def __repr__(self) -> str:
        return f"<Enrollment {self.enrollment_id} for student {self.student_id}>"