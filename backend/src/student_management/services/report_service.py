"""Business logic for report-card PDF generation (ReportLab)."""

import io
import uuid
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
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from sqlalchemy.orm import Session

from student_management.config import settings
from student_management.models import Attendance, Course, Grade, Student
from student_management.services.attendance_service import get_student_or_404
from student_management.services.school_profile import logo_path

REPORT_MEDIA_TYPE = "application/pdf"

ATTENDANCE_STATUSES = ("present", "absent", "late", "excused")

PAGE_WIDTH = 6.77 * inch  # A4 width minus the 0.75in side margins


def _brand_band() -> list[Any]:
    """Letterhead block read from the single branding source.

    Uses the same school name, logo and colours the web app receives from the
    public ``/settings/brand`` endpoint -- never a hardcoded copy.
    """
    primary = colors.HexColor(settings.brand_primary)
    secondary = colors.HexColor(settings.brand_secondary)

    content: list[Any] = []
    logo = logo_path()
    if logo is not None:
        content.append(Image(str(logo), width=0.6 * inch, height=0.6 * inch))

    name_style = ParagraphStyle(
        "BrandName",
        parent=getSampleStyleSheet()["Normal"],
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=19,
        textColor=colors.white,
    )
    tagline_style = ParagraphStyle(
        "BrandTagline",
        parent=getSampleStyleSheet()["Normal"],
        alignment=TA_CENTER,
        fontSize=10,
        leading=13,
        textColor=secondary,
    )
    content.append(Paragraph(settings.school_name, name_style))
    if settings.school_tagline:
        content.append(Paragraph(settings.school_tagline, tagline_style))

    band = Table([[content]], colWidths=[PAGE_WIDTH])
    band.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), primary),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ]
        )
    )

    accent = Table([[""]], colWidths=[PAGE_WIDTH], rowHeights=[0.06 * inch])
    accent.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), secondary),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )

    return [band, accent, Spacer(1, 12)]


def build_report_data(
    db: Session, student_id: str, course_ids: list | None = None
) -> dict[str, Any]:
    """Gather all data a report card needs for a student.

    Course rows are ordered A-Z by name because `grade_level` is free text
    (an alphabetical sort would put "10" before "2"). Callers that need a
    specific academic ordering can sort on a future numeric field.

    When `course_ids` is given, only those courses (and their grades and
    attendance) are included -- used for a teacher's course-scoped report.
    """
    student = get_student_or_404(db, student_id)

    scoped_course_ids = None
    if course_ids:
        scoped_course_ids = [uuid.UUID(str(c)) for c in course_ids]

    course_query = (
        db.query(Course)
        .join(Course.students)
        .filter(Student.student_id == student.student_id)
    )
    if scoped_course_ids:
        course_query = course_query.filter(Course.course_id.in_(scoped_course_ids))
    courses = course_query.order_by(Course.name).all()

    grade_query = db.query(Grade).filter(Grade.student_id == student.student_id)
    attendance_query = db.query(Attendance).filter(
        Attendance.student_id == student.student_id
    )
    if scoped_course_ids:
        grade_query = grade_query.filter(Grade.course_id.in_(scoped_course_ids))
        attendance_query = attendance_query.filter(
            Attendance.course_id.in_(scoped_course_ids)
        )

    grades = grade_query.order_by(Grade.course_id, Grade.date_assigned).all()
    grade_by_course: dict[str, list[Grade]] = defaultdict(list)
    for grade in grades:
        grade_by_course[str(grade.course_id)].append(grade)

    attendance = attendance_query.order_by(
        Attendance.date, Attendance.course_id
    ).all()

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


def build_pdf(
    db: Session,
    student_id: str,
    course_ids: list | None = None,
    scoped: bool = False,
) -> bytes:
    """Return a PDF report for a student as raw bytes.

    `scoped=True` produces a course-scoped "progress report" whose averages and
    attendance totals cover only `course_ids`; otherwise a full report card.
    """
    data = build_report_data(db, student_id, course_ids)
    student: Student = data["student"]

    report_label = "Academic Progress Report" if scoped else "Academic Report Card"
    doc_title = f"Progress Report - {student.first_name} {student.last_name}"
    if not scoped:
        doc_title = f"Report Card - {student.first_name} {student.last_name}"

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        title=doc_title,
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
    story.extend(_brand_band())
    story.append(Paragraph(report_label, title_style))
    subtitle = (
        "Course-scoped - includes only courses taught by this teacher"
        if scoped
        else settings.school_tagline or "Student Management System"
    )
    story.append(Paragraph(subtitle, subtitle_style))

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