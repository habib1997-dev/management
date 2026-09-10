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


def test_parent_can_download_own_child_report(client, db_session, make_auth_headers):
    sid, _cid, admin, _ = make_student_with_data(
        client, db_session, make_auth_headers
    )
    parent_resp = client.post(
        "/api/v1/parents",
        json={
            "name": "Report Parent",
            "email": "report.parent.portal@family.net",
            "phone": "555-100-2000",
            "student_ids": [sid],
        },
        headers=admin,
    )
    pid = parent_resp.json()["parent"]["parent_id"]
    parent = make_auth_headers(role="parent", parent_id=pid)

    resp = client.get(f"/api/v1/reports/portal/{sid}", headers=parent)
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/pdf")
    assert resp.content[:5] == b"%PDF-"


def test_parent_cannot_download_unlinked_child_report(
    client, db_session, make_auth_headers
):
    sid, _cid, admin, _ = make_student_with_data(
        client, db_session, make_auth_headers
    )
    # Create a parent linked to NO children.
    parent_resp = client.post(
        "/api/v1/parents",
        json={
            "name": "Unlinked Parent",
            "email": "report.unlinked@family.net",
            "phone": "555-300-4000",
        },
        headers=admin,
    )
    pid = parent_resp.json()["parent"]["parent_id"]
    parent = make_auth_headers(role="parent", parent_id=pid)

    resp = client.get(f"/api/v1/reports/portal/{sid}", headers=parent)
    assert resp.status_code == 403
    assert "own children" in resp.json()["detail"].lower()


def test_teacher_report_is_course_scoped_progress_report(
    client, db_session, make_auth_headers
):
    """A teacher's PDF covers ONLY their courses and is labelled as a progress report."""
    from student_management.services import report_service

    admin = make_auth_headers(role="admin")
    tid_a = client.post(
        "/api/v1/teachers",
        json={
            "name": "Rep Teacher A",
            "email": "rep.a@schoolsystem.com",
            "subjects_taught": "Math",
        },
        headers=admin,
    ).json()["teacher"]["teacher_id"]
    tid_b = client.post(
        "/api/v1/teachers",
        json={
            "name": "Rep Teacher B",
            "email": "rep.b@schoolsystem.com",
            "subjects_taught": "Chem",
        },
        headers=admin,
    ).json()["teacher"]["teacher_id"]
    cid_a = client.post(
        "/api/v1/courses",
        json={"name": "Math", "teacher_id": tid_a, "grade_level": "11", "semester": "Fall 2026"},
        headers=admin,
    ).json()["course"]["course_id"]
    cid_b = client.post(
        "/api/v1/courses",
        json={"name": "Chem", "teacher_id": tid_b, "grade_level": "11", "semester": "Fall 2026"},
        headers=admin,
    ).json()["course"]["course_id"]

    sid = client.post(
        "/api/v1/students",
        json={
            "first_name": "Report",
            "last_name": "Kid",
            "date_of_birth": "2010-06-01",
            "grade_level": "11",
        },
        headers=admin,
    ).json()["student"]["student_id"]
    client.put(f"/api/v1/courses/{cid_a}/students", json={"student_ids": [sid]}, headers=admin)
    client.put(f"/api/v1/courses/{cid_b}/students", json={"student_ids": [sid]}, headers=admin)

    grade_payload = {
        "assignment_type": "test",
        "date_assigned": "2026-09-01",
        "date_due": "2026-09-05",
    }
    client.post(
        "/api/v1/grades",
        json={"student_id": sid, "course_id": cid_a, "grade_value": 95.0, **grade_payload},
        headers=admin,
    )
    client.post(
        "/api/v1/grades",
        json={"student_id": sid, "course_id": cid_b, "grade_value": 40.0, **grade_payload},
        headers=admin,
    )
    for cid in (cid_a, cid_b):
        client.post(
            "/api/v1/attendance",
            json={
                "course_id": cid,
                "date": "2026-09-07",
                "records": [{"student_id": sid, "status": "present"}],
            },
            headers=admin,
        )

    # Scoped data: only teacher A's course, its grade, and its attendance.
    scoped = report_service.build_report_data(db_session, sid, course_ids=[cid_a])
    assert len(scoped["courses"]) == 1
    assert str(scoped["courses"][0].course_id) == cid_a
    assert list(scoped["grades_by_course"].keys()) == [str(cid_a)]
    assert len(scoped["grades_by_course"][str(cid_a)]) == 1
    assert len(scoped["attendance"]) == 1
    assert str(scoped["attendance"][0].course_id) == cid_a

    # Admin data: everything.
    full = report_service.build_report_data(db_session, sid)
    assert len(full["courses"]) == 2
    assert sum(len(v) for v in full["grades_by_course"].values()) == 2

    # Teacher's PDF is labelled a progress report and named accordingly.
    teacher_a = make_auth_headers(
        email="rep.a.teacher@schoolsystem.com", role="teacher", teacher_id=tid_a
    )
    teacher_pdf = client.get(f"/api/v1/reports/{sid}", headers=teacher_a)
    assert teacher_pdf.status_code == 200
    assert b"Progress Report" in teacher_pdf.content
    assert teacher_pdf.headers["content-disposition"].startswith(
        'attachment; filename="progress_report_'
    )

    # Admin's PDF remains the full report card.
    admin_pdf = client.get(f"/api/v1/reports/{sid}", headers=admin)
    assert admin_pdf.status_code == 200
    assert b"Report Card" in admin_pdf.content
    assert admin_pdf.headers["content-disposition"].startswith(
        'attachment; filename="report_card_'
    )

    # A teacher not involved gets 403.
    tid_c = client.post(
        "/api/v1/teachers",
        json={
            "name": "Rep Teacher C",
            "email": "rep.c@schoolsystem.com",
            "subjects_taught": "History",
        },
        headers=admin,
    ).json()["teacher"]["teacher_id"]
    outsider = make_auth_headers(
        email="rep.c.teacher@schoolsystem.com", role="teacher", teacher_id=tid_c
    )
    assert client.get(f"/api/v1/reports/{sid}", headers=outsider).status_code == 403
