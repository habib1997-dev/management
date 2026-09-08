"""Contract tests for soft-delete / deactivate (teachers, students, parents).

Deactivation is the safe "removal": the record's status flag flips, the person's
login stops working, and they can no longer be assigned new work (courses for
teachers, attendance/grades for students, portal for parents).
"""

import uuid
from copy import deepcopy

from student_management.models import Parent, User

VALID_TEACHER = {
    "name": "Deactiv Teacher",
    "email": "deactiv.teacher@schoolsystem.com",
    "subjects_taught": "Math",
}
VALID_PARENT = {
    "name": "Deactiv Parent",
    "email": "deactiv.parent@family.net",
    "phone": "555-777-8888",
}


def login(client, email, password):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})


def make_student(client, headers, first="Anna", last="Deactiv"):
    resp = client.post(
        "/api/v1/students",
        json={
            "first_name": first,
            "last_name": last,
            "date_of_birth": "2012-04-09",
            "grade_level": "5",
        },
        headers=headers,
    )
    assert resp.status_code == 201
    return resp.json()["student"]["student_id"]


def make_teacher(client, headers, **overrides):
    body = deepcopy(VALID_TEACHER)
    body.update(overrides)
    resp = client.post("/api/v1/teachers", json=body, headers=headers)
    assert resp.status_code == 201
    return resp.json()["teacher"]["teacher_id"]


def make_parent(client, headers, **overrides):
    body = deepcopy(VALID_PARENT)
    body.update(overrides)
    resp = client.post("/api/v1/parents", json=body, headers=headers)
    assert resp.status_code == 201
    parent = resp.json()["parent"]
    return parent["parent_id"], parent["email"]


def make_course(client, headers, teacher_id, **overrides):
    resp = client.post(
        "/api/v1/courses",
        json={
            "name": "Math 9",
            "teacher_id": teacher_id,
            "grade_level": "9",
            "semester": "Fall 2026",
            "max_students": 30,
            **overrides,
        },
        headers=headers,
    )
    assert resp.status_code == 201
    return resp.json()["course"]["course_id"]


# ---------------- Teachers: deactivate / restore ----------------

def test_teacher_deactivate_and_restore(client, make_auth_headers):
    headers = make_auth_headers()
    tid = make_teacher(client, headers)

    off = client.put(f"/api/v1/teachers/{tid}", json={"status": False}, headers=headers)
    assert off.status_code == 200
    body = off.json()
    assert body["success"] is True
    assert body["message"] == "Teacher successfully updated"
    assert body["teacher"]["status"] is False

    on = client.put(f"/api/v1/teachers/{tid}", json={"status": True}, headers=headers)
    assert on.status_code == 200
    assert on.json()["teacher"]["status"] is True


def test_teacher_deactivate_blocks_login(client, make_auth_headers):
    headers = make_auth_headers()
    tid = make_teacher(client, headers, password="teachpw123")
    assert login(client, VALID_TEACHER["email"], "teachpw123").status_code == 200

    client.put(f"/api/v1/teachers/{tid}", json={"status": False}, headers=headers)
    assert login(client, VALID_TEACHER["email"], "teachpw123").status_code == 401

    client.put(f"/api/v1/teachers/{tid}", json={"status": True}, headers=headers)
    assert login(client, VALID_TEACHER["email"], "teachpw123").status_code == 200


def test_teacher_update_errors_and_rbac(client, make_auth_headers):
    headers = make_auth_headers()
    tid = make_teacher(client, headers)

    missing = client.put(
        "/api/v1/teachers/00000000-0000-0000-0000-000000000000",
        json={"status": False},
        headers=headers,
    )
    assert missing.status_code == 404

    malformed = client.put("/api/v1/teachers/not-a-uuid", json={"status": False}, headers=headers)
    assert malformed.status_code == 404

    teacher_headers = make_auth_headers(role="teacher")
    assert (
        client.put(f"/api/v1/teachers/{tid}", json={"status": False}, headers=teacher_headers).status_code
        == 403
    )
    assert client.put(f"/api/v1/teachers/{tid}", json={"status": False}).status_code == 401


# ---------------- Parents: deactivate / restore ----------------

def test_parent_deactivate_and_restore(client, make_auth_headers):
    headers = make_auth_headers()
    pid, _email = make_parent(client, headers)

    off = client.put(f"/api/v1/parents/{pid}", json={"status": False}, headers=headers)
    assert off.status_code == 200
    assert off.json()["parent"]["status"] is False

    on = client.put(f"/api/v1/parents/{pid}", json={"status": True}, headers=headers)
    assert on.status_code == 200
    assert on.json()["parent"]["status"] is True


def test_parent_deactivate_blocks_login_and_portal(client, db_session, make_auth_headers):
    headers = make_auth_headers()
    sid = make_student(client, headers)
    pid, email = make_parent(client, headers, password="parentpw123", student_ids=[sid])
    assert login(client, email, "parentpw123").status_code == 200

    # Deactivate → login is knocked out.
    client.put(f"/api/v1/parents/{pid}", json={"status": False}, headers=headers)
    assert login(client, email, "parentpw123").status_code == 401

    # Defense-in-depth: portal also refuses a deactivated parent directly.
    parent = db_session.get(Parent, uuid.UUID(pid))
    parent.status = False
    user = db_session.query(User).filter(User.parent_id == uuid.UUID(pid)).first()
    user.active = True  # keep login alive so the portal guard (not auth) must refuse
    db_session.commit()
    parent_token_headers = make_auth_headers(role="parent", parent_id=pid)
    portal = client.get(f"/api/v1/parents/{pid}/portal", headers=parent_token_headers)
    assert portal.status_code == 403
    assert "deactivated" in portal.json()["detail"].lower()

    # Restore → everything works again.
    db_session.get(Parent, uuid.UUID(pid)).status = True
    user.active = True
    db_session.commit()
    client.put(f"/api/v1/parents/{pid}", json={"status": True}, headers=headers)
    assert login(client, email, "parentpw123").status_code == 200


def test_parent_update_errors_and_rbac(client, make_auth_headers):
    headers = make_auth_headers()
    pid, _email = make_parent(client, headers)

    missing = client.put(
        "/api/v1/parents/00000000-0000-0000-0000-000000000000",
        json={"status": False},
        headers=headers,
    )
    assert missing.status_code == 404
    assert client.put("/api/v1/parents/not-a-uuid", json={"status": False}, headers=headers).status_code == 404

    parent_headers = make_auth_headers(role="parent")
    assert (
        client.put(f"/api/v1/parents/{pid}", json={"status": False}, headers=parent_headers).status_code == 403
    )
    assert client.put(f"/api/v1/parents/{pid}", json={"status": False}).status_code == 401


# ---------------- Guards: inactive teacher can't take courses ----------------

def test_course_create_rejects_inactive_teacher(client, make_auth_headers):
    headers = make_auth_headers()
    good = make_teacher(client, headers, email="good.teacher@schoolsystem.com")
    bad = make_teacher(client, headers, email="bad.teacher@schoolsystem.com")
    client.put(f"/api/v1/teachers/{bad}", json={"status": False}, headers=headers)

    resp = client.post(
        "/api/v1/courses",
        json={
            "name": "Physics",
            "teacher_id": bad,
            "grade_level": "10",
            "semester": "Fall 2026",
        },
        headers=headers,
    )
    assert resp.status_code == 400
    assert "inactive" in resp.json()["detail"].lower()

    ok = client.post(
        "/api/v1/courses",
        json={
            "name": "Physics",
            "teacher_id": good,
            "grade_level": "10",
            "semester": "Fall 2026",
        },
        headers=headers,
    )
    assert ok.status_code == 201


def test_course_update_rejects_inactive_teacher(client, make_auth_headers):
    headers = make_auth_headers()
    good = make_teacher(client, headers, email="good2@schoolsystem.com")
    bad = make_teacher(client, headers, email="bad2@schoolsystem.com")
    cid = make_course(client, headers, good)
    client.put(f"/api/v1/teachers/{bad}", json={"status": False}, headers=headers)

    resp = client.put(
        f"/api/v1/courses/{cid}", json={"teacher_id": bad}, headers=headers
    )
    assert resp.status_code == 400
    assert "inactive" in resp.json()["detail"].lower()


# ---------------- Guards: inactive student can't get new marks ----------------

def make_course_with_student(client, headers):
    teacher = make_teacher(client, headers, email="roster.teacher@schoolsystem.com")
    sid = make_student(client, headers)
    cid = make_course(client, headers, teacher)
    roster = client.put(
        f"/api/v1/courses/{cid}/students", json={"student_ids": [sid]}, headers=headers
    )
    assert roster.status_code == 200
    return sid, cid


def test_deactivated_student_blocks_attendance(client, make_auth_headers):
    headers = make_auth_headers()
    sid, cid = make_course_with_student(client, headers)

    ok = client.post(
        "/api/v1/attendance",
        json={
            "course_id": cid,
            "date": "2026-09-07",
            "records": [{"student_id": sid, "status": "present"}],
        },
        headers=headers,
    )
    assert ok.status_code == 201

    client.put(f"/api/v1/students/{sid}", json={"active": False}, headers=headers)

    blocked = client.post(
        "/api/v1/attendance",
        json={
            "course_id": cid,
            "date": "2026-09-08",
            "records": [{"student_id": sid, "status": "absent"}],
        },
        headers=headers,
    )
    assert blocked.status_code == 400
    assert "deactivated" in blocked.json()["detail"].lower()


def test_deactivated_student_blocks_grades(client, make_auth_headers):
    headers = make_auth_headers()
    sid, cid = make_course_with_student(client, headers)

    ok = client.post(
        "/api/v1/grades",
        json={
            "student_id": sid,
            "course_id": cid,
            "grade_value": 88,
            "assignment_type": "test",
            "date_assigned": "2026-09-01",
            "date_due": "2026-09-05",
        },
        headers=headers,
    )
    assert ok.status_code == 201

    client.put(f"/api/v1/students/{sid}", json={"active": False}, headers=headers)

    blocked = client.post(
        "/api/v1/grades",
        json={
            "student_id": sid,
            "course_id": cid,
            "grade_value": 55,
            "assignment_type": "homework",
            "date_assigned": "2026-09-01",
            "date_due": "2026-09-06",
        },
        headers=headers,
    )
    assert blocked.status_code == 400
    assert "deactivated" in blocked.json()["detail"].lower()