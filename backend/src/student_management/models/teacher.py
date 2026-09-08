"""Teacher entity."""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from student_management.db import Base


class Teacher(Base):
    __tablename__ = "teachers"

    teacher_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    subjects_taught: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[bool] = mapped_column(Boolean, default=True)

    courses: Mapped[list["Course"]] = relationship(
        back_populates="teacher", foreign_keys="Course.teacher_id"
    )
    attendance_records: Mapped[list["Attendance"]] = relationship(
        back_populates="teacher", foreign_keys="Attendance.marked_by"
    )

    def __repr__(self) -> str:
        return f"<Teacher {self.name}>"