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
