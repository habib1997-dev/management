"""Contract tests for editing a parent/teacher profile (name/email/phone/subjects)
and folding deactivate/restore into the same edit call.
"""

from copy import deepcopy

VALID_TEACHER = {
    "name": "Profile Teacher",
    "email": "profile.teacher@schoolsystem.com",
    "subjects_taught": "Math",
}
VALID_PARENT = {
    "name": "Profile Parent",
    "email": "profile.parent@family.net",
    "phone": "555-777-8888",
}


def login(client, email, password):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})


def make_teacher(client, headers, **overrides):
    body = deepcopy(VALID_TEACHER)
    body.update(overrides)
    resp = client.post("/api/v1/teachers", json=body, headers=headers)
    assert resp.status_code == 201
    return resp.json()["teacher"]["teacher_id"]


def make_parent(client, headers, **overrides):
    body = deepcopy(VALID_PARENT)
    body.update(overrides)
    resp = client.post("/api/v1/parents", json=body, headers=headers)
    assert resp.status_code == 201
    return resp.json()["parent"]["parent_id"]


# ---------------- Teacher profile editing ----------------

def test_teacher_edit_profile(client, make_auth_headers):
    headers = make_auth_headers()
    tid = make_teacher(client, headers)

    resp = client.put(
        f"/api/v1/teachers/{tid}",
        json={"name": "Renamed Teacher", "email": "renamed.teacher@schoolsystem.com", "subjects_taught": "Physics"},
        headers=headers,
    )
    assert resp.status_code == 200
    teacher = resp.json()["teacher"]
    assert teacher["name"] == "Renamed Teacher"
    assert teacher["email"] == "renamed.teacher@schoolsystem.com"
    assert teacher["subjects_taught"] == "Physics"
    assert teacher["status"] is True


def test_teacher_edit_partial_and_subjects_clear(client, make_auth_headers):
    headers = make_auth_headers()
    tid = make_teacher(client, headers)

    resp = client.put(f"/api/v1/teachers/{tid}", json={"name": "Only Renamed"}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["teacher"]["name"] == "Only Renamed"
    assert resp.json()["teacher"]["email"] == VALID_TEACHER["email"]

    cleared = client.put(f"/api/v1/teachers/{tid}", json={"subjects_taught": ""}, headers=headers)
    assert cleared.status_code == 200
    assert cleared.json()["teacher"]["subjects_taught"] is None


def test_teacher_edit_status_and_profile_together(client, make_auth_headers):
    headers = make_auth_headers()
    tid = make_teacher(client, headers, password="teachpw123")

    resp = client.put(
        f"/api/v1/teachers/{tid}",
        json={"name": "Blocked", "status": False},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["teacher"]["name"] == "Blocked"
    assert resp.json()["teacher"]["status"] is False
    assert login(client, VALID_TEACHER["email"], "teachpw123").status_code == 401


def test_teacher_edit_duplicate_email(client, make_auth_headers):
    headers = make_auth_headers()
    make_teacher(client, headers, email="dup.teacher@schoolsystem.com")
    tid = make_teacher(client, headers, email="other.teacher@schoolsystem.com")

    resp = client.put(
        f"/api/v1/teachers/{tid}",
        json={"email": "dup.teacher@schoolsystem.com"},
        headers=headers,
    )
    assert resp.status_code == 400
    assert "email" in resp.json()["detail"].lower()


def test_teacher_edit_bad_email(client, make_auth_headers):
    headers = make_auth_headers()
    tid = make_teacher(client, headers)
    resp = client.put(f"/api/v1/teachers/{tid}", json={"email": "not-an-email"}, headers=headers)
    assert resp.status_code == 422


# ---------------- Parent profile editing ----------------

def test_parent_edit_profile(client, make_auth_headers):
    headers = make_auth_headers()
    pid = make_parent(client, headers)

    resp = client.put(
        f"/api/v1/parents/{pid}",
        json={"name": "Renamed Parent", "email": "renamed.parent@family.net", "phone": "555-999-0000"},
        headers=headers,
    )
    assert resp.status_code == 200
    parent = resp.json()["parent"]
    assert parent["name"] == "Renamed Parent"
    assert parent["email"] == "renamed.parent@family.net"
    assert parent["phone"] == "555-999-0000"
    assert parent["status"] is True


def test_parent_edit_status_and_profile_together(client, make_auth_headers):
    headers = make_auth_headers()
    pid = make_parent(client, headers, password="parentpw123")

    resp = client.put(
        f"/api/v1/parents/{pid}",
        json={"name": "Blocked Parent", "status": False},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["parent"]["name"] == "Blocked Parent"
    assert resp.json()["parent"]["status"] is False
    assert login(client, VALID_PARENT["email"], "parentpw123").status_code == 401


def test_parent_edit_duplicate_email(client, make_auth_headers):
    headers = make_auth_headers()
    make_parent(client, headers, email="dup.parent@family.net")
    pid = make_parent(client, headers, email="other.parent@family.net")

    resp = client.put(
        f"/api/v1/parents/{pid}",
        json={"email": "dup.parent@family.net"},
        headers=headers,
    )
    assert resp.status_code == 400
    assert "email" in resp.json()["detail"].lower()


def test_parent_edit_bad_phone_and_email(client, make_auth_headers):
    headers = make_auth_headers()
    pid = make_parent(client, headers)

    bad_phone = client.put(f"/api/v1/parents/{pid}", json={"phone": "abc"}, headers=headers)
    assert bad_phone.status_code == 422

    bad_email = client.put(f"/api/v1/parents/{pid}", json={"email": "nope"}, headers=headers)
    assert bad_email.status_code == 422


# ---------------- Email/login sync + collision checks ----------------

def test_teacher_edit_email_syncs_login_account(client, make_auth_headers):
    headers = make_auth_headers()
    tid = make_teacher(client, headers, password="teachpw123")
    assert login(client, VALID_TEACHER["email"], "teachpw123").status_code == 200

    resp = client.put(
        f"/api/v1/teachers/{tid}",
        json={"email": "renamed.sync@schoolsystem.com"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["teacher"]["email"] == "renamed.sync@schoolsystem.com"
    assert login(client, "renamed.sync@schoolsystem.com", "teachpw123").status_code == 200
    assert login(client, VALID_TEACHER["email"], "teachpw123").status_code == 401


def test_parent_edit_email_syncs_login_account(client, make_auth_headers):
    headers = make_auth_headers()
    pid = make_parent(client, headers, password="parentpw123")
    assert login(client, VALID_PARENT["email"], "parentpw123").status_code == 200

    resp = client.put(
        f"/api/v1/parents/{pid}",
        json={"email": "renamed.sync@family.net"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert login(client, "renamed.sync@family.net", "parentpw123").status_code == 200
    assert login(client, VALID_PARENT["email"], "parentpw123").status_code == 401


def test_teacher_edit_same_email_keeps_login_valid(client, make_auth_headers):
    headers = make_auth_headers()
    tid = make_teacher(client, headers, password="teachpw123")
    # A no-op email edit must not treat the teacher's own login as a collision.
    resp = client.put(
        f"/api/v1/teachers/{tid}", json={"email": VALID_TEACHER["email"]}, headers=headers
    )
    assert resp.status_code == 200
    assert login(client, VALID_TEACHER["email"], "teachpw123").status_code == 200


def test_teacher_edit_email_conflicts_with_login_account(client, make_auth_headers):
    headers = make_auth_headers()
    make_parent(client, headers, email="shared@family.net", password="parentpw123")
    tid = make_teacher(client, headers, email="teacher.own@schoolsystem.com")

    resp = client.put(
        f"/api/v1/teachers/{tid}", json={"email": "shared@family.net"}, headers=headers
    )
    assert resp.status_code == 400
    assert "login account" in resp.json()["detail"].lower()


def test_parent_edit_email_conflicts_with_login_account(client, make_auth_headers):
    headers = make_auth_headers()
    make_teacher(client, headers, email="sharedt@schoolsystem.com", password="teachpw123")
    pid = make_parent(client, headers, email="parent.own@family.net")

    resp = client.put(
        f"/api/v1/parents/{pid}", json={"email": "sharedt@schoolsystem.com"}, headers=headers
    )
    assert resp.status_code == 400
    assert "login account" in resp.json()["detail"].lower()


def test_create_teacher_email_conflicts_with_login_account(client, make_auth_headers):
    headers = make_auth_headers()
    make_parent(client, headers, email="clash@family.net", password="parentpw123")
    resp = client.post(
        "/api/v1/teachers",
        json={"name": "Clash", "email": "clash@family.net", "subjects_taught": "Math"},
        headers=headers,
    )
    assert resp.status_code == 400
    assert "login account" in resp.json()["detail"].lower()


def test_create_parent_email_conflicts_with_login_account(client, make_auth_headers):
    headers = make_auth_headers()
    make_teacher(client, headers, email="clashh@schoolsystem.com", password="teachpw123")
    resp = client.post(
        "/api/v1/parents",
        json={
            "name": "Clash Parent",
            "email": "clashh@schoolsystem.com",
            "phone": "555-555-5555",
        },
        headers=headers,
    )
    assert resp.status_code == 400
    assert "login account" in resp.json()["detail"].lower()


# ---------------- Password change / first-login creation ----------------

def test_teacher_edit_resets_login_password(client, make_auth_headers):
    headers = make_auth_headers()
    tid = make_teacher(client, headers, password="teachpw123")
    assert login(client, VALID_TEACHER["email"], "teachpw123").status_code == 200

    resp = client.put(
        f"/api/v1/teachers/{tid}",
        json={"password": "brandnew-teach-pw"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert login(client, VALID_TEACHER["email"], "brandnew-teach-pw").status_code == 200
    assert login(client, VALID_TEACHER["email"], "teachpw123").status_code == 401


def test_parent_edit_resets_login_password(client, make_auth_headers):
    headers = make_auth_headers()
    pid = make_parent(client, headers, password="parentpw123")
    assert login(client, VALID_PARENT["email"], "parentpw123").status_code == 200

    resp = client.put(
        f"/api/v1/parents/{pid}",
        json={"password": "brandnew-parent-pw"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert login(client, VALID_PARENT["email"], "brandnew-parent-pw").status_code == 200
    assert login(client, VALID_PARENT["email"], "parentpw123").status_code == 401


def test_teacher_edit_password_creates_first_login(client, make_auth_headers):
    headers = make_auth_headers()
    tid = make_teacher(client, headers)
    assert login(client, VALID_TEACHER["email"], "anything123").status_code == 401

    resp = client.put(
        f"/api/v1/teachers/{tid}", json={"password": "first-login-pw"}, headers=headers
    )
    assert resp.status_code == 200
    assert login(client, VALID_TEACHER["email"], "first-login-pw").status_code == 200


def test_parent_edit_password_creates_first_login(client, make_auth_headers):
    headers = make_auth_headers()
    pid = make_parent(client, headers)
    assert login(client, VALID_PARENT["email"], "anything123").status_code == 401

    resp = client.put(
        f"/api/v1/parents/{pid}", json={"password": "first-login-pw"}, headers=headers
    )
    assert resp.status_code == 200
    assert login(client, VALID_PARENT["email"], "first-login-pw").status_code == 200


def test_teacher_edit_password_with_profile_and_status(client, make_auth_headers):
    headers = make_auth_headers()
    tid = make_teacher(client, headers, password="teachpw123")

    resp = client.put(
        f"/api/v1/teachers/{tid}",
        json={"name": "Password Teacher", "status": True, "password": "combined-pw-123"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["teacher"]["name"] == "Password Teacher"
    assert login(client, VALID_TEACHER["email"], "combined-pw-123").status_code == 200
    assert login(client, VALID_TEACHER["email"], "teachpw123").status_code == 401


def test_teacher_edit_short_password_rejected(client, make_auth_headers):
    headers = make_auth_headers()
    tid = make_teacher(client, headers, password="teachpw123")
    resp = client.put(f"/api/v1/teachers/{tid}", json={"password": "short"}, headers=headers)
    assert resp.status_code == 422
    assert login(client, VALID_TEACHER["email"], "teachpw123").status_code == 200


def test_parent_edit_short_password_rejected(client, make_auth_headers):
    headers = make_auth_headers()
    pid = make_parent(client, headers, password="parentpw123")
    resp = client.put(f"/api/v1/parents/{pid}", json={"password": "short"}, headers=headers)
    assert resp.status_code == 422
    assert login(client, VALID_PARENT["email"], "parentpw123").status_code == 200
