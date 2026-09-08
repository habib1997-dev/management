"""Contract tests for /api/v1 teachers and courses endpoints."""

from copy import deepcopy

VALID_TEACHER = {
    "name": "Marie Curie",
    "email": "marie.curie@schoolsystem.com",
    "subjects_taught": "Science",
}

VALID_COURSE = {
    "name": "Biology",
    "grade_level": "9",
    "semester": "Fall 2026",
}


def make_teacher(client, headers, **overrides):
    body = deepcopy(VALID_TEACHER)
    body.update(overrides)
    return client.post("/api/v1/teachers", json=body, headers=headers)


def make_course(client, headers, teacher_id, **overrides):
    body = deepcopy(VALID_COURSE)
    body["teacher_id"] = teacher_id
    body.update(overrides)
    return client.post("/api/v1/courses", json=body, headers=headers)


# ---------------- Teachers ----------------


def test_create_teacher_contract_shape(client, make_auth_headers):
    response = make_teacher(client, make_auth_headers())
    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "Teacher successfully created"
    teacher = body["teacher"]
    assert set(teacher.keys()) == {
        "teacher_id",
        "name",
        "email",
        "subjects_taught",
        "status",
        "courses",
    }
    assert teacher["name"] == "Marie Curie"
    assert teacher["email"] == "marie.curie@schoolsystem.com"
    assert teacher["status"] is True


def test_create_teacher_requires_valid_email(client, make_auth_headers):
    resp = make_teacher(client, make_auth_headers(), email="not-an-email")
    assert resp.status_code == 422
    missing_name = deepcopy(VALID_TEACHER)
    missing_name.pop("name")
    assert client.post("/api/v1/teachers", json=missing_name, headers=make_auth_headers()).status_code == 422


def test_create_teacher_duplicate_email(client, make_auth_headers):
    headers = make_auth_headers()
    assert make_teacher(client, headers).status_code == 201
    resp = make_teacher(client, headers)
    assert resp.status_code == 400
    assert "email" in resp.json()["detail"].lower()


def test_list_teachers_shape(client, make_auth_headers):
    headers = make_auth_headers()
    make_teacher(client, headers, name="Albert Einstein", email="albert@schoolsystem.com")
    make_teacher(client, headers, name="Marie Curie", email="marie.curie@schoolsystem.com")

    resp = client.get("/api/v1/teachers", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["total"] == 2
    names = {t["name"] for t in body["data"]}
    assert names == {"Albert Einstein", "Marie Curie"}


def test_get_teacher_by_id_and_404(client, make_auth_headers):
    headers = make_auth_headers()
    tid = make_teacher(client, headers).json()["teacher"]["teacher_id"]

    detail = client.get(f"/api/v1/teachers/{tid}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["name"] == "Marie Curie"

    missing = client.get(
        "/api/v1/teachers/00000000-0000-0000-0000-000000000000", headers=headers
    )
    assert missing.status_code == 404
    assert missing.json()["detail"] == "Teacher not found"


def test_teachers_admin_only(client, make_auth_headers):
    teacher_headers = make_auth_headers(role="teacher")
    parent_headers = make_auth_headers(role="parent")
    assert client.get("/api/v1/teachers", headers=teacher_headers).status_code == 403
    assert client.get("/api/v1/teachers", headers=parent_headers).status_code == 403
    assert make_teacher(client, teacher_headers).status_code == 403
    assert client.get("/api/v1/teachers").status_code == 401


# ---------------- Courses ----------------


def create_student_for_course(client, headers):
    resp = client.post(
        "/api/v1/students",
        json={
            "first_name": "Rosa",
            "last_name": "Parks",
            "date_of_birth": "2012-04-09",
            "grade_level": "9",
        },
        headers=headers,
    )
    return resp.json()["student"]["student_id"]


def test_create_course_contract_shape(client, make_auth_headers):
    headers = make_auth_headers()
    tid = make_teacher(client, headers).json()["teacher"]["teacher_id"]

    resp = make_course(client, headers, tid)
    assert resp.status_code == 201
    body = resp.json()
    assert body["success"] is True
    assert body["message"] == "Course successfully created"
    course = body["course"]
    assert {
        "course_id",
        "name",
        "teacher_id",
        "grade_level",
        "semester",
        "status",
        "max_students",
        "students",
    } <= set(course.keys())
    assert course["name"] == "Biology"
    assert course["grade_level"] == "9"
    assert course["teacher_id"] == tid
    assert course["max_students"] == 30


def test_create_course_accepts_custom_grade_label(client, make_auth_headers):
    headers = make_auth_headers()
    tid = make_teacher(client, headers).json()["teacher"]["teacher_id"]

    custom = make_course(client, headers, tid, name="Combined Class", grade_level="K-1")
    assert custom.status_code == 201
    assert custom.json()["course"]["grade_level"] == "K-1"

    graded = make_course(client, headers, tid, name="Secondary", grade_level="Grade 9")
    assert graded.status_code == 201
    assert graded.json()["course"]["grade_level"] == "Grade 9"

    stripped = make_course(client, headers, tid, name="Trimmed", grade_level="  10  ")
    assert stripped.status_code == 201
    assert stripped.json()["course"]["grade_level"] == "10"

    empty = make_course(client, headers, tid, grade_level="")
    assert empty.status_code == 422
    too_long = make_course(client, headers, tid, grade_level="G" * 21)
    assert too_long.status_code == 422

    missing_teacher = make_course(
        client, headers, "00000000-0000-0000-0000-000000000000"
    )
    assert missing_teacher.status_code == 400
    assert missing_teacher.json()["detail"] == "Teacher not found"


def test_list_courses_and_filters(client, make_auth_headers):
    headers = make_auth_headers()
    t1 = make_teacher(client, headers, name="T One", email="t1@schoolsystem.com").json()["teacher"]["teacher_id"]
    t2 = make_teacher(client, headers, name="T Two", email="t2@schoolsystem.com").json()["teacher"]["teacher_id"]
    make_course(client, headers, t1, name="Biology", grade_level="9")
    make_course(client, headers, t2, name="Chemistry", grade_level="10")

    all_courses = client.get("/api/v1/courses", headers=headers).json()
    assert all_courses["meta"]["total"] == 2

    by_teacher = client.get(f"/api/v1/courses?teacherId={t1}", headers=headers).json()
    assert by_teacher["meta"]["total"] == 1
    assert by_teacher["data"][0]["name"] == "Biology"

    by_grade = client.get("/api/v1/courses?gradeLevel=10", headers=headers).json()
    assert by_grade["meta"]["total"] == 1
    assert by_grade["data"][0]["name"] == "Chemistry"


def test_get_update_course(client, make_auth_headers):
    headers = make_auth_headers()
    tid = make_teacher(client, headers).json()["teacher"]["teacher_id"]
    cid = make_course(client, headers, tid).json()["course"]["course_id"]

    detail = client.get(f"/api/v1/courses/{cid}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["name"] == "Biology"

    updated = client.put(
        f"/api/v1/courses/{cid}",
        json={"name": "Biology Honors", "max_students": 25, "status": "active"},
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json()["course"]["name"] == "Biology Honors"
    assert updated.json()["course"]["max_students"] == 25

    missing = client.put(
        "/api/v1/courses/00000000-0000-0000-0000-000000000000",
        json={"name": "Ghost"},
        headers=headers,
    )
    assert missing.status_code == 404


def test_get_course_404_for_unknown_or_malformed_id(client, make_auth_headers):
    headers = make_auth_headers()
    tid = make_teacher(client, headers).json()["teacher"]["teacher_id"]
    cid = make_course(client, headers, tid).json()["course"]["course_id"]

    ok = client.get(f"/api/v1/courses/{cid}", headers=headers)
    assert ok.status_code == 200

    unknown = client.get(
        "/api/v1/courses/00000000-0000-0000-0000-000000000000", headers=headers
    )
    assert unknown.status_code == 404

    malformed = client.get("/api/v1/courses/not-a-uuid", headers=headers)
    assert malformed.status_code == 404

    with_newline = client.get(f"/api/v1/courses/{cid}%0A", headers=headers)
    assert with_newline.status_code == 200

    unknown_with_newline = client.get(
        "/api/v1/courses/00000000-0000-0000-0000-000000000000%20%09%0A",
        headers=headers,
    )
    assert unknown_with_newline.status_code == 404


def test_course_management_admin_only(client, make_auth_headers):
    headers = make_auth_headers()
    tid = make_teacher(client, headers).json()["teacher"]["teacher_id"]
    cid = make_course(client, headers, tid).json()["course"]["course_id"]

    teacher_headers = make_auth_headers(role="teacher")
    assert make_course(client, teacher_headers, tid).status_code == 403
    assert client.put(f"/api/v1/courses/{cid}", json={"name": "x"}, headers=teacher_headers).status_code == 403
    assert client.post(
        "/api/v1/courses", json=deepcopy(VALID_COURSE) | {"teacher_id": tid}, headers=make_auth_headers(role="parent")
    ).status_code == 403


def test_course_students_enforce_max_capacity(client, make_auth_headers):
    headers = make_auth_headers()
    tid = make_teacher(client, headers).json()["teacher"]["teacher_id"]
    cid = make_course(client, headers, tid, max_students=2).json()["course"]["course_id"]
    sids = [create_student_for_course(client, headers) for _ in range(3)]

    assign = client.put(
        f"/api/v1/courses/{cid}/students",
        json={"student_ids": sids},
        headers=headers,
    )
    assert assign.status_code == 400
    assert "capacity" in assign.json()["detail"].lower()

    # Exactly at capacity is allowed
    ok = client.put(
        f"/api/v1/courses/{cid}/students",
        json={"student_ids": sids[:2]},
        headers=headers,
    )
    assert ok.status_code == 200
    assert ok.json()["max_students"] == 2


def test_course_students_assign_and_list(client, make_auth_headers):
    headers = make_auth_headers()
    tid = make_teacher(client, headers).json()["teacher"]["teacher_id"]
    sid1 = create_student_for_course(client, headers)
    sid2 = create_student_for_course(client, headers)

    cid = make_course(client, headers, tid).json()["course"]["course_id"]

    empty = client.get(f"/api/v1/courses/{cid}/students", headers=headers).json()
    assert empty["meta"]["total"] == 0

    assigned = client.put(
        f"/api/v1/courses/{cid}/students",
        json={"student_ids": [sid1, sid2]},
        headers=headers,
    )
    assert assigned.status_code == 200
    assert {s["student_id"] for s in assigned.json()["students"]} == {sid1, sid2}

    roster = client.get(f"/api/v1/courses/{cid}/students", headers=headers).json()
    assert roster["meta"]["total"] == 2
    assert {s["student_id"] for s in roster["data"]} == {sid1, sid2}

    bad = client.put(
        f"/api/v1/courses/{cid}/students",
        json={"student_ids": ["00000000-0000-0000-0000-000000000000"]},
        headers=headers,
    )
    assert bad.status_code == 400

    forbidden = client.put(
        f"/api/v1/courses/{cid}/students",
        json={"student_ids": [sid1]},
        headers=make_auth_headers(role="teacher"),
    )
    assert forbidden.status_code == 403

    missing = client.get(
        "/api/v1/courses/00000000-0000-0000-0000-000000000000/students",
        headers=headers,
    )
    assert missing.status_code == 404