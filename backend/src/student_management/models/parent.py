"""Parent/guardian entity."""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from student_management.db import Base


class Parent(Base):
    __tablename__ = "parents"

    parent_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    phone: Mapped[str] = mapped_column(String(50))
    status: Mapped[bool] = mapped_column(Boolean, default=True)

    students: Mapped[list["Student"]] = relationship(
        secondary="parent_students", back_populates="parents"
    )

    def __repr__(self) -> str:
        return f"<Parent {self.name}>"