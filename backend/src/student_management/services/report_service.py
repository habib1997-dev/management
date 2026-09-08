"""Business logic for report-card PDF generation (ReportLab)."""

import io
from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from sqlalchemy.orm import Session

from student_management.models import Attendance, Course, Grade, Student
from student_management.services.attendance_service import get_student_or_404

REPORT_MEDIA_TYPE = "application/pdf"

ATTENDANCE_STATUSES = ("present", "absent", "late", "excused")


def build_report_data(db: Session, student_id: str) -> dict[str, Any]:
    """Gather all data a report card needs for a student.

    Course rows are ordered A-Z by name because `grade_level` is free text
    (an alphabetical sort would put "10" before "2"). Callers that need a
    specific academic ordering can sort on a future numeric field.
    """
    student = get_student_or_404(db, student_id)

    courses = (
        db.query(Course)
        .join(Course.students)
        .filter(Student.student_id == student.student_id)
        .order_by(Course.name)
        .all()
    )

    grades = (
        db.query(Grade)
        .filter(Grade.student_id == student.student_id)
        .order_by(Grade.course_id, Grade.date_assigned)
        .all()
    )
    grade_by_course: dict[str, list[Grade]] = defaultdict(list)
    for grade in grades:
        grade_by_course[str(grade.course_id)].append(grade)

    attendance = (
        db.query(Attendance)
        .filter(Attendance.student_id == student.student_id)
        .order_by(Attendance.date, Attendance.course_id)
        .all()
    )

    return {
        "student": student,
        "courses": courses,
        "grades_by_course": grade_by_course,
        "attendance": attendance,
    }


def _letter_grade(value: float) -> str:
    if value >= 90:
        return "A"
    if value >= 80:
        return "B"
    if value >= 70:
        return "C"
    if value >= 60:
        return "D"
    return "F"


def _average(values: list[Decimal]) -> float:
    if not values:
        return 0.0
    return round(sum(float(v) for v in values) / len(values), 2)


def _course_average(grades: list[Grade]) -> float:
    return _average([g.grade_value for g in grades])


def _attendance_counts(attendance: list[Attendance]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for record in attendance:
        counts[record.status] += 1
    for status_name in ATTENDANCE_STATUSES:
        counts.setdefault(status_name, 0)
    return dict(counts)


def build_pdf(db: Session, student_id: str) -> bytes:
    """Return a PDF report card for a student as raw bytes."""
    data = build_report_data(db, student_id)
    student: Student = data["student"]

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        title=f"Report Card - {student.first_name} {student.last_name}",
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=18,
        spaceAfter=2,
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=10,
        textColor=colors.grey,
        spaceAfter=12,
    )
    section_style = ParagraphStyle(
        "SectionHeading", parent=styles["Heading2"], spaceBefore=14, spaceAfter=6
    )
    footer_style = ParagraphStyle(
        "Footer", parent=styles["Normal"], fontSize=8, textColor=colors.grey
    )

    story: list[Any] = []
    story.append(Paragraph("Academic Report Card", title_style))
    story.append(Paragraph("Student Management System", subtitle_style))

    student_info = Table(
        [
            ["Student", f"{student.first_name} {student.last_name}"],
            ["Grade Level", student.grade_level or "-"],
            ["Date of Birth", student.date_of_birth.isoformat()],
            ["Enrollment Date", student.enrollment_date.isoformat()],
            ["Student ID", str(student.student_id)],
        ],
        colWidths=[1.7 * inch, 4.8 * inch],
    )
    info_style = TableStyle(
        [
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("BOX", (0, 0), (-1, -1), 0.75, colors.black),
            ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
        ]
    )
    student_info.setStyle(info_style)
    story.append(student_info)

    story.append(Paragraph("Courses & Grades", section_style))

    grade_rows: list[list[Any]] = [
        ["Course", "Grade Level", "Assignments", "Average", "Letter"]
    ]
    overall_values: list[Decimal] = []
    for course in data["courses"]:
        course_grades = data["grades_by_course"].get(str(course.course_id), [])
        avg = _course_average(course_grades)
        overall_values.extend(g.grade_value for g in course_grades)
        grade_rows.append(
            [
                course.name,
                course.grade_level or "-",
                str(len(course_grades)),
                f"{avg:.2f}" if course_grades else "-",
                _letter_grade(avg) if course_grades else "-",
            ]
        )

    if len(grade_rows) == 1:
        grade_rows.append(["No courses assigned", "", "", "-", ""])

    if overall_values:
        overall = _average(overall_values)
        grade_rows.append(
            [
                "Overall",
                "",
                "",
                f"{overall:.2f}",
                _letter_grade(overall),
            ]
        )

    grade_table = Table(
        grade_rows,
        colWidths=[2.4 * inch, 1.2 * inch, 1.2 * inch, 1.0 * inch, 0.9 * inch],
    )
    grade_style = TableStyle(
        [
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ALIGN", (2, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]
    )
    if overall_values:
        last_row = len(grade_rows) - 1
        grade_style.add("BACKGROUND", (0, last_row), (-1, last_row), colors.lightgrey)
        grade_style.add("FONTNAME", (0, last_row), (-1, last_row), "Helvetica-Bold")
    grade_table.setStyle(grade_style)
    story.append(grade_table)
    story.append(Spacer(1, 10))

    attendance_counts = _attendance_counts(data["attendance"])
    total_attendance = sum(attendance_counts.values())
    story.append(Paragraph("Attendance Summary", section_style))
    attendance_body = (
        f"Total records: {total_attendance}  |  "
        f"Present: {attendance_counts['present']}  |  "
        f"Absent: {attendance_counts['absent']}  |  "
        f"Late: {attendance_counts['late']}  |  "
        f"Excused: {attendance_counts['excused']}"
    )
    story.append(Paragraph(attendance_body, styles["Normal"]))

    story.append(Spacer(1, 18))
    story.append(
        Paragraph(
            f"Generated on {date.today().isoformat()}",
            footer_style,
        )
    )

    doc.build(story)
    return buf.getvalue()