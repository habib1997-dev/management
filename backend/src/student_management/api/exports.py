"""Admin-only CSV exports.

Spreadsheet-formula injection is neutralized: any cell that starts with ``=``,
``+``, ``-`` or ``@`` is prefixed with a single quote so spreadsheet apps treat
it as plain text instead of executing it as a formula.
"""

import csv
import io

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from student_management.api.deps import require_roles
from student_management.db import get_db
from student_management.models import Grade, Student, User

router = APIRouter(prefix="/api/v1/export", tags=["export"])

FORMULA_PREFIXES = ("=", "+", "-", "@")


def _safe(value) -> str:
    if value is None:
        return ""
    text = str(value)
    if text.startswith(FORMULA_PREFIXES):
        return "'" + text
    return text


def _csv_response(filename: str, header: list[str], rows: list[list]) -> Response:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(header)
    for row in rows:
        writer.writerow([_safe(cell) for cell in row])
    return Response(
        content=buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/students.csv")
def export_students(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_roles("admin")),
) -> Response:
    """Download every student record as CSV (admin-only)."""
    students = (
        db.query(Student).order_by(Student.last_name, Student.first_name).all()
    )
    rows = [
        [
            s.student_id,
            s.first_name,
            s.last_name,
            s.date_of_birth.isoformat(),
            s.grade_level,
            s.enrollment_date.isoformat(),
            s.email or "",
            s.phone or "",
            "active" if s.active else "inactive",
        ]
        for s in students
    ]
    return _csv_response(
        "students.csv",
        [
            "student_id",
            "first_name",
            "last_name",
            "date_of_birth",
            "grade_level",
            "enrollment_date",
            "email",
            "phone",
            "status",
        ],
        rows,
    )


@router.get("/grades.csv")
def export_grades(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_roles("admin")),
) -> Response:
    """Download every grade record as CSV (admin-only)."""
    grades = (
        db.query(Grade)
        .join(Grade.student)
        .order_by(Grade.date_graded, Grade.date_assigned)
        .all()
    )
    rows = [
        [
            g.grade_id,
            g.student.student_id,
            g.student.first_name,
            g.student.last_name,
            g.course.name if g.course else "",
            g.grade_value,
            g.assignment_type or "",
            g.date_assigned.isoformat(),
            g.date_due.isoformat(),
            g.date_graded.isoformat(),
        ]
        for g in grades
    ]
    return _csv_response(
        "grades.csv",
        [
            "grade_id",
            "student_id",
            "first_name",
            "last_name",
            "course_name",
            "grade_value",
            "assignment_type",
            "date_assigned",
            "date_due",
            "date_graded",
        ],
        rows,
    )