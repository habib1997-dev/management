"""Contract tests for /api/v1/reports/{student_id} report card PDF."""

from copy import deepcopy

VALID_COURSE = {"name": "Physics", "grade_level": "11", "semester": "Fall 2026"}


def make_student_with_data(client, db_session, make_auth_headers):
    """Create a teacher + course + student + a grade + attendance records.

    Returns (student_id, course_id, admin_headers, teacher_headers).
    """
    admin = make_auth_headers(role="admin")

    teacher_resp = client.post(
        "/api/v1/teachers",
        json={
            "name": "Isaac Newton",
            "email": "isaac.reports@schoolsystem.com",
            "subjects_taught": "Science",
        },
        headers=admin,
    )
    tid = teacher_resp.json()["teacher"]["teacher_id"]

    course_resp = client.post(
        "/api/v1/courses",
        json=deepcopy(VALID_COURSE) | {"teacher_id": tid},
        headers=admin,
    )
    cid = course_resp.json()["course"]["course_id"]

    student_resp = client.post(
        "/api/v1/students",
        json={
            "first_name": "Galileo",
            "last_name": "Galilei",
            "date_of_birth": "2010-02-15",
            "grade_level": "11",
        },
        headers=admin,
    )
    sid = student_resp.json()["student"]["student_id"]

    roster = client.put(
        f"/api/v1/courses/{cid}/students",
        json={"student_ids": [sid]},
        headers=admin,
    )
    assert roster.status_code == 200

    client.post(
        "/api/v1/grades",
        json={
            "student_id": sid,
            "course_id": cid,
            "grade_value": 92.5,
            "assignment_type": "test",
            "date_assigned": "2026-09-01",
            "date_due": "2026-09-05",
        },
        headers=admin,
    )
    client.post(
        "/api/v1/attendance",
        json={
            "course_id": cid,
            "date": "2026-09-07",
            "records": [{"student_id": sid, "status": "present"}],
        },
        headers=admin,
    )
    client.post(
        "/api/v1/attendance",
        json={
            "course_id": cid,
            "date": "2026-09-08",
            "records": [{"student_id": sid, "status": "absent"}],
        },
        headers=admin,
    )

    teacher_headers = make_auth_headers(
        email="isaac.teacher@schoolsystem.com", role="teacher", teacher_id=tid
    )
    return sid, cid, admin, teacher_headers


def test_report_pdf_contract_shape(client, db_session, make_auth_headers):
    sid, _cid, admin, _ = make_student_with_data(
        client, db_session, make_auth_headers
    )
    resp = client.get(f"/api/v1/reports/{sid}", headers=admin)
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/pdf")
    assert resp.content[:5] == b"%PDF-"
    assert len(resp.content) > 500


def test_report_pdf_accessible_by_teacher(client, db_session, make_auth_headers):
    sid, _cid, _admin, teacher = make_student_with_data(
        client, db_session, make_auth_headers
    )
    resp = client.get(f"/api/v1/reports/{sid}", headers=teacher)
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/pdf")
    assert resp.content[:5] == b"%PDF-"


def test_report_requires_staff_and_student_exists(
    client, db_session, make_auth_headers
):
    sid, _cid, admin, _ = make_student_with_data(
        client, db_session, make_auth_headers
    )
    assert client.get(f"/api/v1/reports/{sid}").status_code == 401

    parent = make_auth_headers(role="parent")
    assert client.get(f"/api/v1/reports/{sid}", headers=parent).status_code == 403

    missing = client.get(
        "/api/v1/reports/00000000-0000-0000-0000-000000000000", headers=admin
    )
    assert missing.status_code == 404


def test_report_teacher_scoped_to_own_students(client, db_session, make_auth_headers):
    sid, _cid, admin, _ = make_student_with_data(
        client, db_session, make_auth_headers
    )
    other_tid = client.post(
        "/api/v1/teachers",
        json={
            "name": "Not Their Teacher",
            "email": "other.reports@schoolsystem.com",
            "subjects_taught": "History",
        },
        headers=admin,
    ).json()["teacher"]["teacher_id"]
    intruder = make_auth_headers(role="teacher", teacher_id=other_tid)

    resp = client.get(f"/api/v1/reports/{sid}", headers=intruder)
    assert resp.status_code == 403

    admin_resp = client.get(f"/api/v1/reports/{sid}", headers=admin)
    assert admin_resp.status_code == 200
