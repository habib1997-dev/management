"""Contract tests for GET /api/v1/courses/{course_id}/parents.

Teachers may reach guardians of students in their own courses so they can
call about absences or poor performance; nobody outside that scope sees it.
"""


def _make_teacher(client, admin, name, email):
    resp = client.post(
        "/api/v1/teachers",
        json={"name": name, "email": email, "subjects_taught": "Math"},
        headers=admin,
    )
    assert resp.status_code == 201
    return resp.json()["teacher"]["teacher_id"]


def _make_course(client, admin, teacher_id, name):
    resp = client.post(
        "/api/v1/courses",
        json={"name": name, "teacher_id": teacher_id, "grade_level": "9", "semester": "Fall 2026"},
        headers=admin,
    )
    assert resp.status_code == 201
    return resp.json()["course"]["course_id"]


def test_course_parents_own_course_and_foreign(client, make_auth_headers):
    admin = make_auth_headers(role="admin")
    tid = _make_teacher(client, admin, "Course Parent Teacher", "cp.teacher@schoolsystem.com")
    other_tid = _make_teacher(client, admin, "Foreign Teacher", "cp.foreign@schoolsystem.com")
    cid = _make_course(client, admin, tid, "Algebra")
    other_cid = _make_course(client, admin, other_tid, "English")

    def make_student(first):
        resp = client.post(
            "/api/v1/students",
            json={"first_name": first, "last_name": "Pedro", "date_of_birth": "2012-01-01", "grade_level": "9"},
            headers=admin,
        )
        return resp.json()["student"]["student_id"]

    sid_own = make_student("Mine")
    sid_other = make_student("Theirs")
    client.put(f"/api/v1/courses/{cid}/students", json={"student_ids": [sid_own]}, headers=admin)
    client.put(f"/api/v1/courses/{other_cid}/students", json={"student_ids": [sid_other]}, headers=admin)
    pid = client.post(
        "/api/v1/parents",
        json={
            "name": "Guardian Doe",
            "email": "guardian.doe@family.net",
            "phone": "555-100-2000",
            "student_ids": [sid_own],
        },
        headers=admin,
    ).json()["parent"]["parent_id"]

    teacher = make_auth_headers(
        email="cp.own.teacher@schoolsystem.com", role="teacher", teacher_id=tid
    )

    resp = client.get(f"/api/v1/courses/{cid}/parents", headers=teacher)
    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["total"] == 1
    row = body["data"][0]
    assert row["student_id"] == sid_own
    assert row["student_name"] == "Mine Pedro"
    assert [p["parent_id"] for p in row["parents"]] == [pid]
    parent = row["parents"][0]
    assert parent["name"] == "Guardian Doe"
    assert parent["email"] == "guardian.doe@family.net"
    assert parent["phone"] == "555-100-2000"

    # A course the teacher does not own -> 403.
    foreign = make_auth_headers(
        email="cp.foreign.teacher@schoolsystem.com", role="teacher", teacher_id=other_tid
    )

    assert client.get(f"/api/v1/courses/{cid}/parents", headers=foreign).status_code == 403
    assert client.get(f"/api/v1/courses/{other_cid}/parents", headers=teacher).status_code == 403

    # Both teachers see parents for their own courses only (student without a parent -> empty list).
    other_row = client.get(f"/api/v1/courses/{other_cid}/parents", headers=foreign).json()["data"][0]
    assert other_row["student_id"] == sid_other
    assert other_row["parents"] == []

    # Admin can view any course; parents and anonymous get nowhere.
    assert client.get(f"/api/v1/courses/{cid}/parents", headers=admin).status_code == 200
    assert client.get(f"/api/v1/courses/{cid}/parents", headers=make_auth_headers(role="parent")).status_code == 403
    assert client.get(f"/api/v1/courses/{cid}/parents").status_code == 401

    assert client.get("/api/v1/courses/00000000-0000-0000-0000-000000000000/parents", headers=admin).status_code == 404