"""Contract tests for teacher/parent login account endpoints (optional password)."""

from copy import deepcopy

VALID_TEACHER = {
    "name": "Nadia Rahman",
    "email": "nadia.accounts@schoolsystem.com",
    "subjects_taught": "Mathematics",
}

VALID_PARENT = {
    "name": "Rashid Khan",
    "email": "rashid.accounts@family.net",
    "phone": "555-111-2222",
}


def login(client, email, password):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})


def test_create_teacher_with_password_creates_login(client, db_session, make_auth_headers):
    headers = make_auth_headers()
    resp = client.post(
        "/api/v1/teachers", json=deepcopy(VALID_TEACHER) | {"password": "teacherpw123"}, headers=headers
    )
    assert resp.status_code == 201

    ok = login(client, VALID_TEACHER["email"], "teacherpw123")
    assert ok.status_code == 200
    assert ok.json()["role"] == "teacher"

    bad = login(client, VALID_TEACHER["email"], "wrong-password")
    assert bad.status_code == 401


def test_create_teacher_without_password_has_no_login(client, db_session, make_auth_headers):
    headers = make_auth_headers()
    resp = client.post("/api/v1/teachers", json=deepcopy(VALID_TEACHER), headers=headers)
    assert resp.status_code == 201

    none = login(client, VALID_TEACHER["email"], "teacherpw123")
    assert none.status_code == 401


def test_short_password_rejected(client, make_auth_headers):
    headers = make_auth_headers()
    resp = client.post(
        "/api/v1/teachers", json=deepcopy(VALID_TEACHER) | {"password": "short"}, headers=headers
    )
    assert resp.status_code == 422


def test_give_login_to_existing_teacher(client, make_auth_headers):
    headers = make_auth_headers()
    tid = client.post("/api/v1/teachers", json=deepcopy(VALID_TEACHER), headers=headers).json()[
        "teacher"
    ]["teacher_id"]

    created = client.post(
        f"/api/v1/teachers/{tid}/account", json={"password": "teacherpw123"}, headers=headers
    )
    assert created.status_code == 201
    assert created.json()["success"] is True
    assert created.json()["account"]["role"] == "teacher"
    assert created.json()["message"] == "Teacher login created"

    ok = login(client, VALID_TEACHER["email"], "teacherpw123")
    assert ok.status_code == 200

    dup = client.post(
        f"/api/v1/teachers/{tid}/account", json={"password": "anotherpw123"}, headers=headers
    )
    assert dup.status_code == 400
    assert "already" in dup.json()["detail"].lower()


def test_give_login_to_existing_parent(client, make_auth_headers):
    headers = make_auth_headers()
    pid = client.post("/api/v1/parents", json=deepcopy(VALID_PARENT), headers=headers).json()[
        "parent"
    ]["parent_id"]

    created = client.post(
        f"/api/v1/parents/{pid}/account", json={"password": "parentpw123"}, headers=headers
    )
    assert created.status_code == 201
    assert created.json()["account"]["role"] == "parent"

    ok = login(client, VALID_PARENT["email"], "parentpw123")
    assert ok.status_code == 200
    assert ok.json()["role"] == "parent"


def test_account_endpoints_errors(client, make_auth_headers):
    headers = make_auth_headers()
    missing = client.post(
        "/api/v1/teachers/00000000-0000-0000-0000-000000000000/account",
        json={"password": "teacherpw123"},
        headers=headers,
    )
    assert missing.status_code == 404

    short = client.post(
        "/api/v1/parents/00000000-0000-0000-0000-000000000000/account",
        json={"password": "x"},
        headers=headers,
    )
    assert short.status_code == 422


def test_account_endpoints_admin_only(client, make_auth_headers):
    tid = client.post(
        "/api/v1/teachers", json=deepcopy(VALID_TEACHER), headers=make_auth_headers()
    ).json()["teacher"]["teacher_id"]

    teacher_headers = make_auth_headers(role="teacher")
    assert (
        client.post(
            f"/api/v1/teachers/{tid}/account",
            json={"password": "teacherpw123"},
            headers=teacher_headers,
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/api/v1/teachers/00000000-0000-0000-0000-000000000000/account",
            json={"password": "teacherpw123"},
        ).status_code
        == 401
    )