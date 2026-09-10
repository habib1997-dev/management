"""Contract tests for /api/v1 attendance endpoints."""

from copy import deepcopy

VALID_COURSE = {"name": "Biology", "grade_level": "9", "semester": "Fall 2026"}


def make_teacher_with_course(client, db_session, make_auth_headers):
    """Create a teacher + their course + a linked teacher User account.

    Returns (teacher_id, course_id, [student_ids], admin_headers, teacher_headers).
    """
    admin = make_auth_headers(role="admin")

    teacher_resp = client.post(
        "/api/v1/teachers",
        json={
            "name": "Marie Curie",
            "email": "marie.science@schoolsystem.com",
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

    student_ids = []
    for first, last in (("Rosa", "Parks"), ("Ada", "Lovelace")):
        resp = client.post(
            "/api/v1/students",
            json={
                "first_name": first,
                "last_name": last,
                "date_of_birth": "2012-04-09",
                "grade_level": "9",
            },
            headers=admin,
        )
        student_ids.append(resp.json()["student"]["student_id"])

    roster = client.put(
        f"/api/v1/courses/{cid}/students",
        json={"student_ids": student_ids},
        headers=admin,
    )
    assert roster.status_code == 200

    teacher_headers = make_auth_headers(
        email="marie.teacher@schoolsystem.com", role="teacher", teacher_id=tid
    )
    return tid, cid, student_ids, admin, teacher_headers


def test_mark_attendance_contract_shape(client, db_session, make_auth_headers):
    _, cid, student_ids, _, teacher = make_teacher_with_course(
        client, db_session, make_auth_headers
    )
    payload = {
        "course_id": cid,
        "date": "2026-09-07",
        "records": [
            {"student_id": student_ids[0], "status": "present"},
            {"student_id": student_ids[1], "status": "absent"},
        ],
    }
    resp = client.post("/api/v1/attendance", json=payload, headers=teacher)
    assert resp.status_code == 201
    body = resp.json()
    assert body["success"] is True
    assert body["message"] == "Attendance successfully recorded"
    records = body["attendance"]
    assert len(records) == 2
    for record in records:
        assert set(record.keys()) == {
            "attendance_id",
            "student_id",
            "course_id",
            "course_name",
            "date",
            "status",
            "marked_by",
        }
        assert record["date"] == "2026-09-07"
    by_student = {r["student_id"]: r["status"] for r in records}
    assert by_student[student_ids[0]] == "present"
    assert by_student[student_ids[1]] == "absent"


def test_mark_attendance_requires_status_validation(client, db_session, make_auth_headers):
    _, cid, student_ids, _, teacher = make_teacher_with_course(
        client, db_session, make_auth_headers
    )
    bad = {
        "course_id": cid,
        "date": "2026-09-07",
        "records": [{"student_id": student_ids[0], "status": "frog"}],
    }
    assert client.post("/api/v1/attendance", json=bad, headers=teacher).status_code == 422

    empty = {
        "course_id": cid,
        "date": "2026-09-07",
        "records": [],
    }
    assert client.post("/api/v1/attendance", json=empty, headers=teacher).status_code == 422

    future = {
        "course_id": cid,
        "date": "2100-01-01",
        "records": [{"student_id": student_ids[0], "status": "present"}],
    }
    assert client.post("/api/v1/attendance", json=future, headers=teacher).status_code == 422


def test_mark_attendance_rejects_students_not_in_course(client, db_session, make_auth_headers):
    _, cid, _student_ids, admin, teacher = make_teacher_with_course(
        client, db_session, make_auth_headers
    )
    outsider_resp = client.post(
        "/api/v1/students",
        json={
            "first_name": "Xavier",
            "last_name": "Outside",
            "date_of_birth": "2011-01-01",
            "grade_level": "9",
        },
        headers=admin,
    )
    outsider = outsider_resp.json()["student"]["student_id"]

    payload = {
        "course_id": cid,
        "date": "2026-09-07",
        "records": [{"student_id": outsider, "status": "present"}],
    }
    resp = client.post("/api/v1/attendance", json=payload, headers=teacher)
    assert resp.status_code == 400
    assert "not assigned to this course" in resp.json()["detail"]

    fake = {
        "course_id": cid,
        "date": "2026-09-07",
        "records": [
            {"student_id": "00000000-0000-0000-0000-000000000000", "status": "present"}
        ],
    }
    assert client.post("/api/v1/attendance", json=fake, headers=teacher).status_code == 400


def test_mark_attendance_requires_teacher_own_course(client, db_session, make_auth_headers):
    _, cid, student_ids, admin, _ = make_teacher_with_course(
        client, db_session, make_auth_headers
    )
    other_tid = client.post(
        "/api/v1/teachers",
        json={
            "name": "Other Teacher",
            "email": "other@schoolsystem.com",
            "subjects_taught": "History",
        },
        headers=admin,
    ).json()["teacher"]["teacher_id"]
    intruder = make_auth_headers(role="teacher", teacher_id=other_tid)

    payload = {
        "course_id": cid,
        "date": "2026-09-07",
        "records": [{"student_id": student_ids[0], "status": "present"}],
    }
    resp = client.post("/api/v1/attendance", json=payload, headers=intruder)
    assert resp.status_code == 403

    assert client.post("/api/v1/attendance", json=payload, headers=admin).status_code == 201


def test_mark_attendance_upserts_same_day(client, db_session, make_auth_headers):
    _, cid, student_ids, _, teacher = make_teacher_with_course(
        client, db_session, make_auth_headers
    )
    payload = {
        "course_id": cid,
        "date": "2026-09-07",
        "records": [{"student_id": student_ids[0], "status": "late"}],
    }
    first = client.post("/api/v1/attendance", json=payload, headers=teacher)
    assert first.status_code == 201
    first_id = first.json()["attendance"][0]["attendance_id"]

    payload["records"][0]["status"] = "absent"
    second = client.post("/api/v1/attendance", json=payload, headers=teacher)
    assert second.status_code == 201
    assert len(second.json()["attendance"]) == 1
    assert second.json()["attendance"][0]["attendance_id"] == first_id
    assert second.json()["attendance"][0]["status"] == "absent"


def test_list_course_attendance_with_date_filter(client, db_session, make_auth_headers):
    _, cid, student_ids, _, teacher = make_teacher_with_course(
        client, db_session, make_auth_headers
    )
    for day, status in (("2026-09-01", "present"), ("2026-09-02", "absent")):
        client.post(
            "/api/v1/attendance",
            json={
                "course_id": cid,
                "date": day,
                "records": [{"student_id": student_ids[0], "status": status}],
            },
            headers=teacher,
        )

    all_records = client.get(f"/api/v1/attendance/{cid}", headers=teacher)
    assert all_records.status_code == 200
    assert all_records.json()["meta"]["total"] == 2

    day_records = client.get(f"/api/v1/attendance/{cid}?date=2026-09-02", headers=teacher)
    assert day_records.status_code == 200
    assert day_records.json()["meta"]["total"] == 1
    assert day_records.json()["data"][0]["status"] == "absent"

    missing = client.get(
        "/api/v1/attendance/00000000-0000-0000-0000-000000000000", headers=teacher
    )
    assert missing.status_code == 404


def test_student_attendance_view_and_teacher_scoping(client, db_session, make_auth_headers):
    _, cid, student_ids, admin, teacher = make_teacher_with_course(
        client, db_session, make_auth_headers
    )
    client.post(
        "/api/v1/attendance",
        json={
            "course_id": cid,
            "date": "2026-09-01",
            "records": [{"student_id": student_ids[0], "status": "present"}],
        },
        headers=teacher,
    )

    # Teacher of the course can see the student's record
    view = client.get(f"/api/v1/students/{student_ids[0]}/attendance", headers=teacher)
    assert view.status_code == 200
    assert view.json()["meta"]["total"] == 1
    assert view.json()["data"][0]["student_id"] == student_ids[0]

    # Admin can view too
    admin_view = client.get(f"/api/v1/students/{student_ids[0]}/attendance", headers=admin)
    assert admin_view.status_code == 200
    assert admin_view.json()["meta"]["total"] == 1

    # Teacher NOT teaching this student gets 403
    other_tid = client.post(
        "/api/v1/teachers",
        json={"name": "Intruder", "email": "intruder@schoolsystem.com", "subjects_taught": "X"},
        headers=admin,
    ).json()["teacher"]["teacher_id"]
    intruder = make_auth_headers(role="teacher", teacher_id=other_tid)
    blocked = client.get(f"/api/v1/students/{student_ids[0]}/attendance", headers=intruder)
    assert blocked.status_code == 403

    missing = client.get(
        "/api/v1/students/00000000-0000-0000-0000-000000000000/attendance", headers=admin
    )
    assert missing.status_code == 404


def test_attendance_auth_required(client, db_session, make_auth_headers):
    _, cid, student_ids, _, _ = make_teacher_with_course(
        client, db_session, make_auth_headers
    )
    payload = {
        "course_id": cid,
        "date": "2026-09-07",
        "records": [{"student_id": student_ids[0], "status": "present"}],
    }
    assert client.post("/api/v1/attendance", json=payload).status_code == 401
    parent = make_auth_headers(role="parent")
    assert client.post("/api/v1/attendance", json=payload, headers=parent).status_code == 403


def test_student_attendance_teacher_sees_only_own_courses(
    client, db_session, make_auth_headers
):
    """A teacher viewing a student they teach sees only their own course's records."""
    admin = make_auth_headers(role="admin")
    tid_a = client.post(
        "/api/v1/teachers",
        json={
            "name": "Att Teacher A",
            "email": "att.a@schoolsystem.com",
            "subjects_taught": "Math",
        },
        headers=admin,
    ).json()["teacher"]["teacher_id"]
    tid_b = client.post(
        "/api/v1/teachers",
        json={
            "name": "Att Teacher B",
            "email": "att.b@schoolsystem.com",
            "subjects_taught": "Chem",
        },
        headers=admin,
    ).json()["teacher"]["teacher_id"]
    cid_a = client.post(
        "/api/v1/courses",
        json={"name": "Math", "teacher_id": tid_a, "grade_level": "9", "semester": "Fall 2026"},
        headers=admin,
    ).json()["course"]["course_id"]
    cid_b = client.post(
        "/api/v1/courses",
        json={"name": "Chem", "teacher_id": tid_b, "grade_level": "9", "semester": "Fall 2026"},
        headers=admin,
    ).json()["course"]["course_id"]

    sid = client.post(
        "/api/v1/students",
        json={
            "first_name": "Shared",
            "last_name": "Student",
            "date_of_birth": "2012-01-05",
            "grade_level": "9",
        },
        headers=admin,
    ).json()["student"]["student_id"]
    client.put(f"/api/v1/courses/{cid_a}/students", json={"student_ids": [sid]}, headers=admin)
    client.put(f"/api/v1/courses/{cid_b}/students", json={"student_ids": [sid]}, headers=admin)

    client.post(
        "/api/v1/attendance",
        json={
            "course_id": cid_a,
            "date": "2026-09-01",
            "records": [{"student_id": sid, "status": "present"}],
        },
        headers=admin,
    )
    client.post(
        "/api/v1/attendance",
        json={
            "course_id": cid_b,
            "date": "2026-09-02",
            "records": [{"student_id": sid, "status": "absent"}],
        },
        headers=admin,
    )

    teacher_a = make_auth_headers(
        email="att.a.teacher@schoolsystem.com", role="teacher", teacher_id=tid_a
    )
    view = client.get(f"/api/v1/students/{sid}/attendance", headers=teacher_a)
    assert view.status_code == 200
    assert view.json()["meta"]["total"] == 1
    assert view.json()["data"][0]["course_id"] == cid_a

    admin_view = client.get(f"/api/v1/students/{sid}/attendance", headers=admin)
    assert admin_view.status_code == 200
    assert admin_view.json()["meta"]["total"] == 2