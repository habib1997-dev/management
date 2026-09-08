"""Contract tests for /api/v1 parents endpoints."""

from copy import deepcopy

VALID_PARENT = {
    "name": "Maria Doe",
    "email": "maria.contract@family.net",
    "phone": "555-222-3333",
}


def make_parent(client, headers, **overrides):
    body = deepcopy(VALID_PARENT)
    body.update(overrides)
    return client.post("/api/v1/parents", json=body, headers=headers)


def make_student(client, headers, first="Anna", last="Student"):
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


# ---------------- Create parent ----------------


def test_create_parent_contract_shape(client, make_auth_headers):
    headers = make_auth_headers()
    resp = make_parent(client, headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["success"] is True
    assert body["message"] == "Parent successfully created"
    parent = body["parent"]
    assert set(parent.keys()) == {"parent_id", "name", "email", "phone", "status"}
    assert parent["name"] == "Maria Doe"
    assert parent["email"] == "maria.contract@family.net"
    assert parent["phone"] == "555-222-3333"
    assert parent["status"] is True


def test_create_parent_validation(client, make_auth_headers):
    headers = make_auth_headers()
    bad_email = make_parent(client, headers, email="not-an-email")
    assert bad_email.status_code == 422

    missing_phone = deepcopy(VALID_PARENT)
    missing_phone.pop("phone")
    assert (
        client.post("/api/v1/parents", json=missing_phone, headers=headers).status_code
        == 422
    )

    missing_name = deepcopy(VALID_PARENT)
    missing_name.pop("name")
    assert (
        client.post("/api/v1/parents", json=missing_name, headers=headers).status_code
        == 422
    )


def test_create_parent_duplicate_email(client, make_auth_headers):
    headers = make_auth_headers()
    assert make_parent(client, headers).status_code == 201
    resp = make_parent(client, headers)
    assert resp.status_code == 400
    assert "email" in resp.json()["detail"].lower()


# ---------------- Link to students ----------------


def test_create_parent_links_students(client, make_auth_headers):
    headers = make_auth_headers()
    sid1 = make_student(client, headers, first="Ali", last="Khan")
    sid2 = make_student(client, headers, first="Sara", last="Khan")

    resp = make_parent(client, headers, student_ids=[sid1, sid2])
    assert resp.status_code == 201

    children = client.get(f"/api/v1/parents/{resp.json()['parent']['parent_id']}/students", headers=headers)
    assert children.status_code == 200
    data = children.json()["data"]
    assert {s["student_id"] for s in data} == {sid1, sid2}


def test_create_parent_rejects_missing_student(client, make_auth_headers):
    headers = make_auth_headers()
    resp = make_parent(
        client, headers, student_ids=["00000000-0000-0000-0000-000000000000"]
    )
    assert resp.status_code == 400
    assert "student" in resp.json()["detail"].lower()


# ---------------- List parents ----------------


def test_list_parents_shape(client, make_auth_headers):
    headers = make_auth_headers()
    make_parent(client, headers, email="one@family.net")
    make_parent(client, headers, email="two@family.net")

    resp = client.get("/api/v1/parents", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["total"] == 2
    assert {p["email"] for p in body["data"]} == {"one@family.net", "two@family.net"}


def test_parent_students_404_for_unknown_parent(client, make_auth_headers):
    headers = make_auth_headers()
    missing = client.get(
        "/api/v1/parents/00000000-0000-0000-0000-000000000000/students", headers=headers
    )
    assert missing.status_code == 404

    malformed = client.get("/api/v1/parents/not-a-uuid/students", headers=headers)
    assert malformed.status_code == 404


# ---------------- RBAC ----------------


def test_parents_admin_only(client, make_auth_headers):
    headers = make_auth_headers()
    make_student(client, headers)

    teacher_headers = make_auth_headers(role="teacher")
    parent_headers = make_auth_headers(role="parent")

    assert make_parent(client, teacher_headers).status_code == 403
    assert make_parent(client, parent_headers).status_code == 403
    assert client.get("/api/v1/parents", headers=teacher_headers).status_code == 403
    assert client.get("/api/v1/parents", headers=parent_headers).status_code == 403
    assert (
        client.get(
            f"/api/v1/parents/{make_parent(client, headers).json()['parent']['parent_id']}/students",
            headers=teacher_headers,
        ).status_code
        == 403
    )
    assert client.post("/api/v1/parents", json=deepcopy(VALID_PARENT) | {"student_ids": []}).status_code == 401