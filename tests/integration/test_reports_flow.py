"""End-to-end integration: report-card PDF generation with real data."""

import io

from pypdf import PdfReader


def test_report_card_full_flow(client, db_session, make_auth_headers):
    admin = make_auth_headers(role="admin")

    # 1. Teacher + course + student + roster
    teacher = client.post(
        "/api/v1/teachers",
        json={
            "name": "Alan Turing",
            "email": "alan.reports@schoolsystem.com",
            "subjects_taught": "Math",
        },
        headers=admin,
    )
    tid = teacher.json()["teacher"]["teacher_id"]

    course = client.post(
        "/api/v1/courses",
        json={
            "name": "Algebra",
            "grade_level": "9",
            "semester": "Fall 2026",
            "teacher_id": tid,
        },
        headers=admin,
    )
    cid = course.json()["course"]["course_id"]

    student = client.post(
        "/api/v1/students",
        json={
            "first_name": "Meera",
            "last_name": "Sharma",
            "date_of_birth": "2011-07-12",
            "grade_level": "9",
        },
        headers=admin,
    )
    sid = student.json()["student"]["student_id"]

    roster = client.put(
        f"/api/v1/courses/{cid}/students",
        json={"student_ids": [sid]},
        headers=admin,
    )
    assert roster.status_code == 200

    teacher_headers = make_auth_headers(
        email="alan.teacher@schoolsystem.com", role="teacher", teacher_id=tid
    )

    # 2. A grade and attendance (so the report has content)
    grade = client.post(
        "/api/v1/grades",
        json={
            "student_id": sid,
            "course_id": cid,
            "grade_value": 84.0,
            "assignment_type": "final",
            "date_assigned": "2026-09-01",
            "date_due": "2026-09-10",
        },
        headers=teacher_headers,
    )
    assert grade.status_code == 201

    for day, status in (("2026-09-07", "present"), ("2026-09-08", "late")):
        att = client.post(
            "/api/v1/attendance",
            json={
                "course_id": cid,
                "date": day,
                "records": [{"student_id": sid, "status": status}],
            },
            headers=teacher_headers,
        )
        assert att.status_code == 201

    # 3. Generate the report card as PDF
    resp = client.get(f"/api/v1/reports/{sid}", headers=admin)
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/pdf")
    assert "inline" not in resp.headers.get("content-disposition", "")
    assert b"%PDF-" == resp.content[:5]
    assert resp.content.rstrip().endswith(b"%%EOF")

    # 4. Extract text and validate the actual content
    text = "\n".join(
        page.extract_text() or "" for page in PdfReader(io.BytesIO(resp.content)).pages
    )

    assert "Academic Report Card" in text
    assert "Meera Sharma" in text
    assert "Algebra" in text
    assert "84.00" in text
    assert "B" in text  # letter grade for 84
    assert "Attendance Summary" in text
    assert "Present: 1" in text
    assert "Late: 1" in text