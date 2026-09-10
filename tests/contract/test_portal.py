"""Contract tests for the parent portal endpoint."""

from copy import deepcopy

VALID_COURSE = {"name": "Biology", "grade_level": "9", "semester": "Fall 2026"}


def make_parent_with_data(client, make_auth_headers):
    """Build teacher+course+students+attendance+grade, then a linked parent with a login.

    Returns (admin, parent_headers, parent_id, student_ids).
    """
    admin = make_auth_headers()
    tid = client.post(
        "/api/v1/teachers",
        json={"name": "Marie Curie", "email": "marie.portal@schoolsystem.com", "subjects_taught": "Science"},
        headers=admin,
    ).json()["teacher"]["teacher_id"]
    cid = client.post(
        "/api/v1/courses", json=deepcopy(VALID_COURSE) | {"teacher_id": tid}, headers=admin
    ).json()["course"]["course_id"]

    student_ids = []
    for first, last in (("Anna", "Khan"), ("Omar", "Khan")):
        r = client.post(
            "/api/v1/students",
            json={"first_name": first, "last_name": last, "date_of_birth": "2012-04-09", "grade_level": "9"},
            headers=admin,
        )
        student_ids.append(r.json()["student"]["student_id"])
    client.put(f"/api/v1/courses/{cid}/students", json={"student_ids": student_ids}, headers=admin)

    client.post(
        "/api/v1/attendance",
        json={"course_id": cid, "date": "2026-09-07", "records": [{"student_id": student_ids[0], "status": "present"}]},
        headers=admin,
    )
    client.post(
        "/api/v1/grades",
        json={
            "student_id": student_ids[0],
            "course_id": cid,
            "grade_value": 88.0,
            "assignment_type": "quiz",
            "date_assigned": "2026-09-01",
            "date_due": "2026-09-04",
        },
        headers=admin,
    )

    pid = client.post(
        "/api/v1/parents",
        json={"name": "Rashid Khan", "email": "rashid.portal@family.net", "phone": "555-111-2222", "student_ids": student_ids},
        headers=admin,
    ).json()["parent"]["parent_id"]
    client.post(f"/api/v1/parents/{pid}/account", json={"password": "parentpw123"}, headers=admin)

    login = client.post(
        "/api/v1/auth/login", json={"email": "rashid.portal@family.net", "password": "parentpw123"}
    )
    assert login.status_code == 200
    parent_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    return admin, parent_headers, pid, student_ids


def test_portal_returns_own_children_with_data(client, db_session, make_auth_headers):
    _, parent_headers, pid, student_ids = make_parent_with_data(client, make_auth_headers)

    resp = client.get(f"/api/v1/parents/{pid}/portal", headers=parent_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert len(body["parents"]) == 1
    portal = body["parents"][0]
    assert portal["parent_id"] == pid
    assert {c["student_id"] for c in portal["children"]} == set(student_ids)

    first = next(c for c in portal["children"] if c["student_id"] == student_ids[0])
    assert first["grade_level"] == "9"
    assert len(first["attendance"]) == 1
    assert first["attendance"][0]["status"] == "present"
    assert first["attendance"][0]["course_name"] == "Biology"
    assert len(first["grades"]) == 1
    assert first["grades"][0]["grade_value"] == 88.0
    assert first["grades"][0]["assignment_type"] == "quiz"
    assert first["grades"][0]["course_name"] == "Biology"


def test_portal_denies_other_parent(client, db_session, make_auth_headers):
    _, parent_headers, _, _ = make_parent_with_data(client, make_auth_headers)

    admin = make_auth_headers()
    other_pid = client.post(
        "/api/v1/parents",
        json={"name": "Other Parent", "email": "other.portal@family.net", "phone": "555-999-8888"},
        headers=admin,
    ).json()["parent"]["parent_id"]

    blocked = client.get(f"/api/v1/parents/{other_pid}/portal", headers=parent_headers)
    assert blocked.status_code == 403


def test_portal_blocks_admin_and_teacher(client, db_session, make_auth_headers):
    _, _, pid, _ = make_parent_with_data(client, make_auth_headers)

    admin = make_auth_headers()
    assert client.get(f"/api/v1/parents/{pid}/portal", headers=admin).status_code == 403

    teacher = make_auth_headers(role="teacher")
    assert client.get(f"/api/v1/parents/{pid}/portal", headers=teacher).status_code == 403


def test_portal_404_and_auth(client, db_session, make_auth_headers):
    _, parent_headers, _, _ = make_parent_with_data(client, make_auth_headers)

    assert (
        client.get(
            "/api/v1/parents/00000000-0000-0000-0000-000000000000/portal", headers=parent_headers
        ).status_code
        == 404
    )
    assert client.get("/api/v1/parents/00000000-0000-0000-0000-000000000000/portal").status_code == 401