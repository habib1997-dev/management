"""Grade entity - a numeric score for a student in a course."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from student_management.db import Base
from student_management.models.enums import (
    AssignmentType,
    enum_values,
)


class Grade(Base):
    __tablename__ = "grades"
    __table_args__ = (
        CheckConstraint("grade_value >= 0 AND grade_value <= 100", name="ck_grades_value"),
        CheckConstraint("date_due >= date_assigned", name="ck_grades_due_after_assigned"),
        CheckConstraint("date_graded >= date_due", name="ck_grades_graded_after_due"),
        CheckConstraint(
            f"assignment_type IN ({enum_values([a.value for a in AssignmentType])})",
            name="ck_grades_assignment_type",
        ),
    )

    grade_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("students.student_id", ondelete="CASCADE"), index=True
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("courses.course_id", ondelete="CASCADE"), index=True
    )
    grade_value: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    assignment_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    date_assigned: Mapped[date] = mapped_column(Date)
    date_due: Mapped[date] = mapped_column(Date)
    date_graded: Mapped[date] = mapped_column(Date, default=date.today)

    student: Mapped["Student"] = relationship(back_populates="grades")
    course: Mapped["Course"] = relationship(back_populates="grades")

    def __repr__(self) -> str:
        return f"<Grade {self.grade_value} for student {self.student_id}>"