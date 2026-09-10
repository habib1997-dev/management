"""Contract tests for teacher/parent login account endpoints (optional password)."""

from copy import deepcopy

import student_management.models  # noqa: F401
from student_management.models import User

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


def make_user(db_session, email, role="admin"):
    user = db_session.query(User).filter(User.email == email).first()
    assert user is not None
    return user


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


# ---------------- Admin account management (list / deactivate / reset) ----------------


def test_list_user_accounts(client, db_session, make_auth_headers):
    headers = make_auth_headers()
    make_user(db_session, "admin@test.edu")  # default admin from fixture
    client.post(
        "/api/v1/teachers", json=deepcopy(VALID_TEACHER) | {"password": "teacherpw123"}, headers=headers
    )

    resp = client.get("/api/v1/administrators/users", headers=headers)
    assert resp.status_code == 200
    emails = {u["email"] for u in resp.json()["data"]}
    assert VALID_TEACHER["email"] in emails
    assert "admin@test.edu" in emails
    admin_row = next(u for u in resp.json()["data"] if u["email"] == VALID_TEACHER["email"])
    assert set(admin_row.keys()) == {"user_id", "email", "role", "active"}
    assert admin_row["role"] == "teacher"
    assert admin_row["active"] is True


def test_admin_resets_password(client, db_session, make_auth_headers):
    headers = make_auth_headers()
    client.post(
        "/api/v1/teachers", json=deepcopy(VALID_TEACHER) | {"password": "firstpw123"}, headers=headers
    )
    user_id = str(make_user(db_session, VALID_TEACHER["email"]).user_id)

    reset = client.put(
        f"/api/v1/administrators/users/{user_id}",
        json={"password": "newpw456"},
        headers=headers,
    )
    assert reset.status_code == 200
    assert reset.json()["success"] is True
    assert login(client, VALID_TEACHER["email"], "firstpw123").status_code == 401
    assert login(client, VALID_TEACHER["email"], "newpw456").status_code == 200


def test_password_reset_invalidates_old_login_token(client, db_session, make_auth_headers):
    headers = make_auth_headers()
    client.post(
        "/api/v1/teachers", json=deepcopy(VALID_TEACHER) | {"password": "firstpw123"}, headers=headers
    )
    user_id = str(make_user(db_session, VALID_TEACHER["email"]).user_id)

    old_login = client.post(
        "/api/v1/auth/login", json={"email": VALID_TEACHER["email"], "password": "firstpw123"}
    )
    assert old_login.status_code == 200
    old_token = old_login.json()["access_token"]
    old_headers = {"Authorization": f"Bearer {old_token}"}

    # 403 = credentials valid but wrong role (admin-only endpoint); 401 = invalid token
    before = client.get(f"/api/v1/teachers/{user_id}", headers=old_headers)
    assert before.status_code == 403

    reset = client.put(
        f"/api/v1/administrators/users/{user_id}",
        json={"password": "newpw456"},
        headers=headers,
    )
    assert reset.status_code == 200

    after = client.get(f"/api/v1/teachers/{user_id}", headers=old_headers)
    assert after.status_code == 401


def test_admin_deactivates_and_reactivates_login(client, db_session, make_auth_headers):
    headers = make_auth_headers()
    client.post(
        "/api/v1/teachers", json=deepcopy(VALID_TEACHER) | {"password": "teacherpw123"}, headers=headers
    )
    user_id = str(make_user(db_session, VALID_TEACHER["email"]).user_id)

    off = client.put(
        f"/api/v1/administrators/users/{user_id}", json={"active": False}, headers=headers
    )
    assert off.status_code == 200
    assert login(client, VALID_TEACHER["email"], "teacherpw123").status_code == 401

    on = client.put(
        f"/api/v1/administrators/users/{user_id}", json={"active": True}, headers=headers
    )
    assert on.status_code == 200
    assert login(client, VALID_TEACHER["email"], "teacherpw123").status_code == 200


def test_admin_login_deactivate_syncs_teacher_status(client, db_session, make_auth_headers):
    headers = make_auth_headers()
    client.post(
        "/api/v1/teachers", json=deepcopy(VALID_TEACHER) | {"password": "teacherpw123"}, headers=headers
    )
    user_id = str(make_user(db_session, VALID_TEACHER["email"]).user_id)

    off = client.put(
        f"/api/v1/administrators/users/{user_id}", json={"active": False}, headers=headers
    )
    assert off.status_code == 200
    teachers = client.get("/api/v1/teachers", headers=headers).json()["data"]
    row = next(t for t in teachers if t["email"] == VALID_TEACHER["email"])
    assert row["status"] is False
    assert login(client, VALID_TEACHER["email"], "teacherpw123").status_code == 401

    on = client.put(
        f"/api/v1/administrators/users/{user_id}", json={"active": True}, headers=headers
    )
    assert on.status_code == 200
    teachers = client.get("/api/v1/teachers", headers=headers).json()["data"]
    row = next(t for t in teachers if t["email"] == VALID_TEACHER["email"])
    assert row["status"] is True
    assert login(client, VALID_TEACHER["email"], "teacherpw123").status_code == 200


def test_admin_login_deactivate_syncs_parent_status(client, db_session, make_auth_headers):
    headers = make_auth_headers()
    client.post(
        "/api/v1/parents", json=deepcopy(VALID_PARENT) | {"password": "parentpw123"}, headers=headers
    )
    user_id = str(make_user(db_session, VALID_PARENT["email"]).user_id)

    off = client.put(
        f"/api/v1/administrators/users/{user_id}", json={"active": False}, headers=headers
    )
    assert off.status_code == 200
    parents = client.get("/api/v1/parents", headers=headers).json()["data"]
    row = next(p for p in parents if p["email"] == VALID_PARENT["email"])
    assert row["status"] is False

    on = client.put(
        f"/api/v1/administrators/users/{user_id}", json={"active": True}, headers=headers
    )
    assert on.status_code == 200
    parents = client.get("/api/v1/parents", headers=headers).json()["data"]
    row = next(p for p in parents if p["email"] == VALID_PARENT["email"])
    assert row["status"] is True


def test_admin_update_user_errors(client, db_session, make_auth_headers):
    headers = make_auth_headers()
    missing = client.put(
        "/api/v1/administrators/users/00000000-0000-0000-0000-000000000000",
        json={"active": False},
        headers=headers,
    )
    assert missing.status_code == 404

    client.post(
        "/api/v1/teachers", json=deepcopy(VALID_TEACHER) | {"password": "teacherpw123"}, headers=headers
    )
    user_id = str(make_user(db_session, VALID_TEACHER["email"]).user_id)
    short = client.put(
        f"/api/v1/administrators/users/{user_id}",
        json={"password": "x"},
        headers=headers,
    )
    assert short.status_code == 422

    malformed = client.put(
        "/api/v1/administrators/users/not-a-uuid",
        json={"active": True},
        headers=headers,
    )
    assert malformed.status_code == 404


def test_admin_user_management_admin_only(client, db_session, make_auth_headers):
    teacher_headers = make_auth_headers(role="teacher")
    assert client.get("/api/v1/administrators/users", headers=teacher_headers).status_code == 403
    assert client.get("/api/v1/administrators/users").status_code == 401
    assert (
        client.put(
            "/api/v1/administrators/users/00000000-0000-0000-0000-000000000000",
            json={"active": False},
            headers=teacher_headers,
        ).status_code
        == 403
    )


# ---------------- Account creation blocks email collisions ----------------

def test_teacher_account_creation_email_conflicts_with_other_login(
    client, make_auth_headers
):
    headers = make_auth_headers()
    tid = client.post(
        "/api/v1/teachers", json=deepcopy(VALID_TEACHER), headers=headers
    ).json()["teacher"]["teacher_id"]
    # A parent claims the teacher's email as their login BEFORE the teacher gets one.
    client.post(
        "/api/v1/parents",
        json=deepcopy(VALID_PARENT) | {"email": VALID_TEACHER["email"], "password": "parentpw123"},
        headers=headers,
    )
    resp = client.post(
        f"/api/v1/teachers/{tid}/account",
        json={"password": "teacherpw123"},
        headers=headers,
    )
    assert resp.status_code == 400
    assert "login account" in resp.json()["detail"].lower()


def test_parent_account_creation_email_conflicts_with_other_login(
    client, make_auth_headers
):
    headers = make_auth_headers()
    pid = client.post(
        "/api/v1/parents", json=deepcopy(VALID_PARENT), headers=headers
    ).json()["parent"]["parent_id"]
    client.post(
        "/api/v1/teachers",
        json=deepcopy(VALID_TEACHER) | {"email": VALID_PARENT["email"], "password": "teacherpw123"},
        headers=headers,
    )
    resp = client.post(
        f"/api/v1/parents/{pid}/account",
        json={"password": "parentpw123"},
        headers=headers,
    )
    assert resp.status_code == 400
    assert "login account" in resp.json()["detail"].lower()