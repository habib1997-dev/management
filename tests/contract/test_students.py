"""Contract tests for /api/v1 students and enrollments endpoints."""

from copy import deepcopy

VALID_STUDENT = {
    "first_name": "Ada",
    "last_name": "Lovelace",
    "date_of_birth": "2010-03-15",
    "grade_level": "5",
}


def register_valid_student(client, headers):
    return client.post(
        "/api/v1/students", json=VALID_STUDENT, headers=headers
    )


def test_enroll_student_returns_contract_shape(client, make_auth_headers):
    headers = make_auth_headers(role="admin")
    response = register_valid_student(client, headers)
    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "Student successfully enrolled"
    student = body["student"]
    assert set(student.keys()) == {
        "student_id",
        "first_name",
        "last_name",
        "grade_level",
        "active",
        "enrollment_date",
        "date_of_birth",
        "email",
        "phone",
    }
    assert student["first_name"] == "Ada"
    assert student["grade_level"] == "5"
    assert student["active"] is True
    assert student["email"] is None
    assert student["enrollment_date"] is not None


def test_enroll_student_requires_admin(client, make_auth_headers):
    headers = make_auth_headers(role="teacher")
    assert client.post("/api/v1/students", json=VALID_STUDENT, headers=headers).status_code == 403
    assert client.post("/api/v1/students", json=VALID_STUDENT).status_code == 401


def test_enroll_student_accepts_custom_grade_label(client, make_auth_headers):
    headers = make_auth_headers()
    custom = deepcopy(VALID_STUDENT)
    custom["grade_level"] = "K-1"
    assert client.post("/api/v1/students", json=custom, headers=headers).status_code == 201
    too_long = deepcopy(VALID_STUDENT)
    too_long["grade_level"] = "G" * 21
    assert client.post("/api/v1/students", json=too_long, headers=headers).status_code == 422


def test_enroll_student_rejects_future_dob(client, make_auth_headers):
    bad = deepcopy(VALID_STUDENT)
    bad["date_of_birth"] = "2100-01-01"
    response = client.post("/api/v1/students", json=bad, headers=make_auth_headers())
    assert response.status_code == 422
    assert "date_of_birth" in response.json()["detail"][0]["msg"]


def test_enroll_student_rejects_bad_email_and_phone(client, make_auth_headers):
    bad = deepcopy(VALID_STUDENT)
    bad["email"] = "not-an-email"
    assert client.post("/api/v1/students", json=bad, headers=make_auth_headers()).status_code == 422
    bad2 = deepcopy(VALID_STUDENT)
    bad2["phone"] = "abc"
    assert client.post("/api/v1/students", json=bad2, headers=make_auth_headers()).status_code == 422


def test_enroll_student_duplicate_email(client, make_auth_headers):
    headers = make_auth_headers()
    first = deepcopy(VALID_STUDENT)
    first["email"] = "ada@test.edu"
    assert client.post("/api/v1/students", json=first, headers=headers).status_code == 201
    resp = client.post("/api/v1/students", json=first, headers=headers)
    assert resp.status_code == 400
    assert "email" in resp.json()["detail"].lower()


def test_list_students_pagination_meta(client, make_auth_headers):
    headers = make_auth_headers()
    for i in range(3):
        s = deepcopy(VALID_STUDENT)
        s["first_name"] = f"Student{i}"
        assert client.post("/api/v1/students", json=s, headers=headers).status_code == 201

    response = client.get("/api/v1/students?page=1&pageSize=2", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert len(body["data"]) == 2
    assert body["meta"] == {"page": 1, "pageSize": 2, "total": 3}


def test_list_students_search_filter(client, make_auth_headers):
    headers = make_auth_headers()
    s1 = deepcopy(VALID_STUDENT)
    s1["first_name"] = "Maria"
    s1["last_name"] = "Jones"
    client.post("/api/v1/students", json=s1, headers=headers)

    response = client.get("/api/v1/students?search=jones", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["meta"]["total"] == 1
    assert body["data"][0]["last_name"] == "Jones"


def test_list_students_grade_level_and_active_filter(client, make_auth_headers):
    headers = make_auth_headers()
    first = register_valid_student(client, headers)
    sid = first.json()["student"]["student_id"]
    client.put(f"/api/v1/students/{sid}", json={"active": False}, headers=headers)

    active = client.get("/api/v1/students?active=true", headers=headers).json()
    inactive = client.get("/api/v1/students?active=false", headers=headers).json()
    assert active["meta"]["total"] == 0
    assert inactive["meta"]["total"] == 1

    grade5 = client.get("/api/v1/students?gradeLevel=5", headers=headers).json()
    grade6 = client.get("/api/v1/students?gradeLevel=6", headers=headers).json()
    assert grade5["meta"]["total"] == 1
    assert grade6["meta"]["total"] == 0


def test_get_student_by_id_and_404(client, make_auth_headers):
    headers = make_auth_headers()
    sid = register_valid_student(client, headers).json()["student"]["student_id"]

    detail = client.get(f"/api/v1/students/{sid}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["first_name"] == "Ada"

    missing = client.get("/api/v1/students/00000000-0000-0000-0000-000000000000", headers=headers)
    assert missing.status_code == 404
    assert missing.json()["detail"] == "Student not found"


def test_update_student(client, make_auth_headers):
    headers = make_auth_headers()
    sid = register_valid_student(client, headers).json()["student"]["student_id"]

    response = client.put(
        f"/api/v1/students/{sid}",
        json={"last_name": "Lovelace-Byron", "phone": "+1 (555) 0102"},
        headers=headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["student"]["last_name"] == "Lovelace-Byron"
    assert body["student"]["phone"] == "+1 (555) 0102"


def test_update_student_date_of_birth_and_grade_level(client, make_auth_headers):
    headers = make_auth_headers()
    sid = register_valid_student(client, headers).json()["student"]["student_id"]

    response = client.put(
        f"/api/v1/students/{sid}",
        json={"date_of_birth": "2011-06-20", "grade_level": "O-Level"},
        headers=headers,
    )
    assert response.status_code == 200
    student = response.json()["student"]
    assert student["date_of_birth"] == "2011-06-20"
    assert student["grade_level"] == "O-Level"

    future = client.put(
        f"/api/v1/students/{sid}", json={"date_of_birth": "2030-01-01"}, headers=headers
    )
    assert future.status_code == 422
    assert "date_of_birth" in future.json()["detail"][0]["msg"]

    blank = client.put(
        f"/api/v1/students/{sid}", json={"grade_level": "   "}, headers=headers
    )
    assert blank.status_code == 422


def test_update_student_requires_admin_and_404(client, make_auth_headers):
    headers = make_auth_headers()
    sid = register_valid_student(client, headers).json()["student"]["student_id"]

    forbidden = client.put(
        f"/api/v1/students/{sid}", json={"last_name": "Nope"}, headers=make_auth_headers(role="teacher")
    )
    assert forbidden.status_code == 403

    missing = client.put(
        "/api/v1/students/00000000-0000-0000-0000-000000000000",
        json={"last_name": "Nope"},
        headers=headers,
    )
    assert missing.status_code == 404


def test_create_enrollment(client, make_auth_headers):
    headers = make_auth_headers()
    sid = register_valid_student(client, headers).json()["student"]["student_id"]

    response = client.post(
        "/api/v1/enrollments",
        json={"student_id": sid, "enrolled_by": "admin@test.edu", "status": "active"},
        headers=headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["enrollment"]["student_id"] == sid


def test_create_enrollment_rejects_missing_student(client, make_auth_headers):
    response = client.post(
        "/api/v1/enrollments",
        json={
            "student_id": "00000000-0000-0000-0000-000000000000",
            "enrolled_by": "admin@test.edu",
        },
        headers=make_auth_headers(),
    )
    assert response.status_code == 404


def test_teacher_list_students_scoped_to_own_courses(client, db_session, make_auth_headers):
    admin = make_auth_headers(role="admin")
    tid = client.post(
        "/api/v1/teachers",
        json={
            "name": "Scoped Teacher",
            "email": "scoped.t@schoolsystem.com",
            "subjects_taught": "Math",
        },
        headers=admin,
    ).json()["teacher"]["teacher_id"]
    cid = client.post(
        "/api/v1/courses",
        json={"name": "Algebra", "teacher_id": tid, "grade_level": "9", "semester": "Fall 2026"},
        headers=admin,
    ).json()["course"]["course_id"]

    sids = []
    for i in range(3):
        resp = client.post(
            "/api/v1/students",
            json={
                "first_name": f"Child{i}",
                "last_name": "One",
                "date_of_birth": "2012-01-01",
                "grade_level": "9",
            },
            headers=admin,
        )
        sids.append(resp.json()["student"]["student_id"])
    client.post(
        "/api/v1/students",
        json={
            "first_name": "Elsewhere",
            "last_name": "Two",
            "date_of_birth": "2012-01-01",
            "grade_level": "9",
        },
        headers=admin,
    )

    client.put(f"/api/v1/courses/{cid}/students", json={"student_ids": sids}, headers=admin)

    teacher = make_auth_headers(
        email="scoped.t.teacher@schoolsystem.com", role="teacher", teacher_id=tid
    )
    resp = client.get("/api/v1/students", headers=teacher)
    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["total"] == 3
    names = {s["first_name"] for s in body["data"]}
    assert names == {"Child0", "Child1", "Child2"}
    assert "Elsewhere" not in names

    # A student in TWO of the teacher's courses still appears exactly once.
    cid2 = client.post(
        "/api/v1/courses",
        json={"name": "Geometry", "teacher_id": tid, "grade_level": "9", "semester": "Fall 2026"},
        headers=admin,
    ).json()["course"]["course_id"]
    client.put(f"/api/v1/courses/{cid2}/students", json={"student_ids": [sids[0]]}, headers=admin)
    rerun = client.get("/api/v1/students", headers=teacher)
    assert rerun.json()["meta"]["total"] == 3

    # Search/grade filters still apply WITHIN the teacher's roster.
    searched = client.get("/api/v1/students?search=Elsewhere", headers=teacher)
    assert searched.json()["meta"]["total"] == 0
    found = client.get("/api/v1/students?search=Child1", headers=teacher)
    assert found.json()["meta"]["total"] == 1

    # Admin still sees everyone.
    admin_all = client.get("/api/v1/students", headers=admin)
    assert admin_all.json()["meta"]["total"] == 4


def test_get_student_profile_teacher_gate(client, db_session, make_auth_headers):
    """Teachers can read a full profile ONLY for students they teach; otherwise 403."""
    admin = make_auth_headers(role="admin")
    tid = client.post(
        "/api/v1/teachers",
        json={
            "name": "Profile Teacher",
            "email": "profile.t@schoolsystem.com",
            "subjects_taught": "Math",
        },
        headers=admin,
    ).json()["teacher"]["teacher_id"]
    cid = client.post(
        "/api/v1/courses",
        json={"name": "Algebra", "teacher_id": tid, "grade_level": "9", "semester": "Fall 2026"},
        headers=admin,
    ).json()["course"]["course_id"]

    own = client.post(
        "/api/v1/students",
        json={
            "first_name": "Mine",
            "last_name": "Student",
            "date_of_birth": "2012-01-01",
            "grade_level": "9",
        },
        headers=admin,
    ).json()["student"]["student_id"]
    others = client.post(
        "/api/v1/students",
        json={
            "first_name": "Theirs",
            "last_name": "Student",
            "date_of_birth": "2012-01-01",
            "grade_level": "9",
        },
        headers=admin,
    ).json()["student"]["student_id"]
    client.put(f"/api/v1/courses/{cid}/students", json={"student_ids": [own]}, headers=admin)

    teacher = make_auth_headers(
        email="profile.t.teacher@schoolsystem.com", role="teacher", teacher_id=tid
    )
    own_resp = client.get(f"/api/v1/students/{own}", headers=teacher)
    assert own_resp.status_code == 200
    assert own_resp.json()["email"] is not None or "student_id" in own_resp.json()
    assert own_resp.json()["student_id"] == own

    # Existing-but-not-taught -> 403
    assert client.get(f"/api/v1/students/{others}", headers=teacher).status_code == 403

    # Unknown and unauthorized are indistinguishable for teachers -> 403
    unknown = client.get(
        "/api/v1/students/00000000-0000-0000-0000-000000000000", headers=teacher
    )
    assert unknown.status_code == 403

    # Parents get no access to student profiles.
    parent = make_auth_headers(role="parent")
    assert client.get(f"/api/v1/students/{own}", headers=parent).status_code == 403

    # Admin: full access for any student, 404 only for genuinely unknown ids.
    assert client.get(f"/api/v1/students/{others}", headers=admin).status_code == 200
    admin_unknown = client.get(
        "/api/v1/students/00000000-0000-0000-0000-000000000000", headers=admin
    )
    assert admin_unknown.status_code == 404


def test_student_list_contact_admin_only(client, make_auth_headers):
    """Admins see student email/phone in the list; teachers get null."""
    admin = make_auth_headers(role="admin")
    tid = client.post(
        "/api/v1/teachers",
        json={"name": "Contact Teacher", "email": "contact.t@schoolsystem.com", "subjects_taught": "Math"},
        headers=admin,
    ).json()["teacher"]["teacher_id"]
    cid = client.post(
        "/api/v1/courses",
        json={"name": "Algebra", "teacher_id": tid, "grade_level": "9", "semester": "Fall 2026"},
        headers=admin,
    ).json()["course"]["course_id"]
    sid = client.post(
        "/api/v1/students",
        json={
            "first_name": "Contact",
            "last_name": "Kid",
            "date_of_birth": "2012-01-01",
            "grade_level": "9",
            "email": "kid@schoolsystem.com",
            "phone": "555-100-2000",
        },
        headers=admin,
    ).json()["student"]["student_id"]
    client.put(f"/api/v1/courses/{cid}/students", json={"student_ids": [sid]}, headers=admin)

    admin_list = client.get("/api/v1/students?search=Contact", headers=admin).json()
    row = admin_list["data"][0]
    assert row["email"] == "kid@schoolsystem.com"
    assert row["phone"] == "555-100-2000"

    teacher = make_auth_headers(
        email="contact.t.teacher@schoolsystem.com", role="teacher", teacher_id=tid
    )
    teacher_list = client.get("/api/v1/students?search=Contact", headers=teacher).json()
    trow = teacher_list["data"][0]
    assert trow["first_name"] == "Contact"
    assert trow["email"] is None
    assert trow["phone"] is None


def test_student_detail_contact_admin_only(client, make_auth_headers):
    """Teachers get the profile but never the student's own email/phone."""
    admin = make_auth_headers(role="admin")
    tid = client.post(
        "/api/v1/teachers",
        json={"name": "Profile Teacher", "email": "profile.contact.t@schoolsystem.com", "subjects_taught": "Math"},
        headers=admin,
    ).json()["teacher"]["teacher_id"]
    cid = client.post(
        "/api/v1/courses",
        json={"name": "Algebra", "teacher_id": tid, "grade_level": "9", "semester": "Fall 2026"},
        headers=admin,
    ).json()["course"]["course_id"]
    sid = client.post(
        "/api/v1/students",
        json={
            "first_name": "Detail",
            "last_name": "Kid",
            "date_of_birth": "2012-01-01",
            "grade_level": "9",
            "email": "detail@schoolsystem.com",
            "phone": "555-300-4000",
        },
        headers=admin,
    ).json()["student"]["student_id"]
    client.put(f"/api/v1/courses/{cid}/students", json={"student_ids": [sid]}, headers=admin)

    teacher = make_auth_headers(
        email="profile.contact.t.teacher@schoolsystem.com", role="teacher", teacher_id=tid
    )
    resp = client.get(f"/api/v1/students/{sid}", headers=teacher)
    assert resp.status_code == 200
    body = resp.json()
    assert body["first_name"] == "Detail"
    assert body["email"] is None
    assert body["phone"] is None

    admin_body = client.get(f"/api/v1/students/{sid}", headers=admin).json()
    assert admin_body["email"] == "detail@schoolsystem.com"
    assert admin_body["phone"] == "555-300-4000"
