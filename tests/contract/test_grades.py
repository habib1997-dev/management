"""Contract tests for /api/v1 grade endpoints."""

from copy import deepcopy

VALID_COURSE = {"name": "Physics", "grade_level": "11", "semester": "Fall 2026"}


def make_teacher_with_course(client, db_session, make_auth_headers):
    """Create a teacher + their course + a linked teacher User account.

    Returns (teacher_id, course_id, [student_ids], admin_headers, teacher_headers).
    """
    admin = make_auth_headers(role="admin")

    teacher_resp = client.post(
        "/api/v1/teachers",
        json={
            "name": "Albert Einstein",
            "email": "albert.physics@schoolsystem.com",
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
    for first, last in (("Marie", "Curie"), ("Niels", "Bohr")):
        resp = client.post(
            "/api/v1/students",
            json={
                "first_name": first,
                "last_name": last,
                "date_of_birth": "2011-05-14",
                "grade_level": "11",
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
        email="albert.teacher@schoolsystem.com", role="teacher", teacher_id=tid
    )
    return tid, cid, student_ids, admin, teacher_headers


def make_grade_payload(cid, student_id, **overrides):
    payload = {
        "student_id": student_id,
        "course_id": cid,
        "grade_value": 92.5,
        "assignment_type": "test",
        "date_assigned": "2026-09-01",
        "date_due": "2026-09-05",
    }
    payload.update(overrides)
    return payload


def test_record_grade_contract_shape(client, db_session, make_auth_headers):
    _, cid, student_ids, _, teacher = make_teacher_with_course(
        client, db_session, make_auth_headers
    )
    resp = client.post(
        "/api/v1/grades",
        json=make_grade_payload(cid, student_ids[0]),
        headers=teacher,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["success"] is True
    assert body["message"] == "Grade successfully recorded"
    grade = body["grade"]
    assert set(grade.keys()) == {
        "grade_id",
        "student_id",
        "course_id",
        "grade_value",
        "assignment_type",
        "date_assigned",
        "date_due",
        "date_graded",
    }
    assert grade["student_id"] == student_ids[0]
    assert grade["course_id"] == cid
    assert grade["grade_value"] == 92.5
    assert grade["assignment_type"] == "test"
    assert grade["date_assigned"] == "2026-09-01"
    assert grade["date_due"] == "2026-09-05"
    assert grade["date_graded"] == "2026-09-05" or grade["date_graded"] >= "2026-09-05"


def test_record_grade_validation(client, db_session, make_auth_headers):
    _, cid, student_ids, _, teacher = make_teacher_with_course(
        client, db_session, make_auth_headers
    )
    for bad_value, label in ((-1, "negative"), (101, "above 100")):
        resp = client.post(
            "/api/v1/grades",
            json=make_grade_payload(cid, student_ids[0], grade_value=bad_value),
            headers=teacher,
        )
        assert resp.status_code == 422, f"{label} grade_value should be rejected"

    bad_type = client.post(
        "/api/v1/grades",
        json=make_grade_payload(cid, student_ids[0], assignment_type="frog"),
        headers=teacher,
    )
    assert bad_type.status_code == 422

    bad_dates = client.post(
        "/api/v1/grades",
        json=make_grade_payload(
            cid,
            student_ids[0],
            date_assigned="2026-09-10",
            date_due="2026-09-05",
        ),
        headers=teacher,
    )
    assert bad_dates.status_code == 422


def test_record_grade_rejects_students_not_in_course(client, db_session, make_auth_headers):
    _, cid, _student_ids, admin, teacher = make_teacher_with_course(
        client, db_session, make_auth_headers
    )
    outsider_resp = client.post(
        "/api/v1/students",
        json={
            "first_name": "Yuri",
            "last_name": "Gagarin",
            "date_of_birth": "2010-01-01",
            "grade_level": "11",
        },
        headers=admin,
    )
    outsider = outsider_resp.json()["student"]["student_id"]

    resp = client.post(
        "/api/v1/grades",
        json=make_grade_payload(cid, outsider),
        headers=teacher,
    )
    assert resp.status_code == 400
    assert "not assigned" in resp.json()["detail"]

    fake = client.post(
        "/api/v1/grades",
        json=make_grade_payload(cid, "00000000-0000-0000-0000-000000000000"),
        headers=teacher,
    )
    assert fake.status_code == 400


def test_record_grade_requires_teacher_own_course(client, db_session, make_auth_headers):
    _, cid, student_ids, admin, _ = make_teacher_with_course(
        client, db_session, make_auth_headers
    )
    other_tid = client.post(
        "/api/v1/teachers",
        json={
            "name": "Other Teacher",
            "email": "other.grades@schoolsystem.com",
            "subjects_taught": "History",
        },
        headers=admin,
    ).json()["teacher"]["teacher_id"]
    intruder = make_auth_headers(role="teacher", teacher_id=other_tid)

    payload = make_grade_payload(cid, student_ids[0])
    resp = client.post("/api/v1/grades", json=payload, headers=intruder)
    assert resp.status_code == 403

    assert client.post("/api/v1/grades", json=payload, headers=admin).status_code == 201

    missing_course = client.post(
        "/api/v1/grades",
        json=make_grade_payload("00000000-0000-0000-0000-000000000000", student_ids[0]),
        headers=admin,
    )
    assert missing_course.status_code == 404


def test_student_grades_view_with_course_filter(client, db_session, make_auth_headers):
    _, cid, student_ids, admin, teacher = make_teacher_with_course(
        client, db_session, make_auth_headers
    )
    other_tid = client.post(
        "/api/v1/teachers",
        json={
            "name": "Chemistry Teacher",
            "email": "chemistry.teacher@schoolsystem.com",
            "subjects_taught": "Chemistry",
        },
        headers=admin,
    ).json()["teacher"]["teacher_id"]
    other_course = client.post(
        "/api/v1/courses",
        json={"name": "Chemistry", "teacher_id": other_tid, "grade_level": "11", "semester": "Fall 2026"},
        headers=admin,
    )
    cid2 = other_course.json()["course"]["course_id"]

    client.put(
        f"/api/v1/courses/{cid2}/students",
        json={"student_ids": [student_ids[0]]},
        headers=admin,
    )

    client.post(
        "/api/v1/grades",
        json=make_grade_payload(cid, student_ids[0], grade_value=90.0),
        headers=teacher,
    )
    client.post(
        "/api/v1/grades",
        json=make_grade_payload(cid2, student_ids[0], grade_value=85.0),
        headers=admin,
    )

    all_grades = client.get(f"/api/v1/students/{student_ids[0]}/grades", headers=teacher)
    assert all_grades.status_code == 200
    assert all_grades.json()["meta"]["total"] == 2

    filtered = client.get(
        f"/api/v1/students/{student_ids[0]}/grades?courseId={cid2}", headers=teacher
    )
    assert filtered.status_code == 200
    assert filtered.json()["meta"]["total"] == 1
    assert filtered.json()["data"][0]["course_id"] == cid2

    missing = client.get(
        "/api/v1/students/00000000-0000-0000-0000-000000000000/grades", headers=admin
    )
    assert missing.status_code == 404


def test_course_grades_view_and_teacher_scoping(client, db_session, make_auth_headers):
    _, cid, student_ids, admin, teacher = make_teacher_with_course(
        client, db_session, make_auth_headers
    )
    client.post(
        "/api/v1/grades",
        json=make_grade_payload(cid, student_ids[0], grade_value=90.0),
        headers=teacher,
    )
    client.post(
        "/api/v1/grades",
        json=make_grade_payload(cid, student_ids[1], grade_value=75.5),
        headers=teacher,
    )

    course_grades = client.get(f"/api/v1/courses/{cid}/grades", headers=teacher)
    assert course_grades.status_code == 200
    assert course_grades.json()["meta"]["total"] == 2

    admin_view = client.get(f"/api/v1/courses/{cid}/grades", headers=admin)
    assert admin_view.status_code == 200
    assert admin_view.json()["meta"]["total"] == 2

    other_tid = client.post(
        "/api/v1/teachers",
        json={
            "name": "Intruder",
            "email": "intruder.grades@schoolsystem.com",
            "subjects_taught": "X",
        },
        headers=admin,
    ).json()["teacher"]["teacher_id"]
    intruder = make_auth_headers(role="teacher", teacher_id=other_tid)
    blocked = client.get(f"/api/v1/courses/{cid}/grades", headers=intruder)
    assert blocked.status_code == 403

    blocked_student = client.get(f"/api/v1/students/{student_ids[0]}/grades", headers=intruder)
    assert blocked_student.status_code == 403

    missing = client.get(
        "/api/v1/courses/00000000-0000-0000-0000-000000000000/grades", headers=admin
    )
    assert missing.status_code == 404


def test_grades_auth_required(client, db_session, make_auth_headers):
    _, cid, student_ids, _, _ = make_teacher_with_course(
        client, db_session, make_auth_headers
    )
    payload = make_grade_payload(cid, student_ids[0])
    assert client.post("/api/v1/grades", json=payload).status_code == 401
    parent = make_auth_headers(role="parent")
    assert client.post("/api/v1/grades", json=payload, headers=parent).status_code == 403