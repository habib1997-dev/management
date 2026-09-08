"""Auth + RBAC integration tests: login, JWT issuance, and role guards."""

from student_management.models import User
from student_management.security import hash_password


def create_user(db, email: str, password: str, role: str) -> User:
    user = User(
        email=email,
        password_hash=hash_password(password),
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login(client, email: str, password: str) -> dict:
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})


def test_login_returns_token_for_admin(client, db_session):
    create_user(db_session, "admin@school.edu", "secret123", "admin")
    resp = login(client, "admin@school.edu", "secret123")
    assert resp.status_code == 200
    body = resp.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"
    assert body["role"] == "admin"
    assert body["email"] == "admin@school.edu"


def test_login_rejects_wrong_password(client, db_session):
    create_user(db_session, "admin@school.edu", "secret123", "admin")
    resp = login(client, "admin@school.edu", "wrongpass")
    assert resp.status_code == 401
    assert "password" in resp.json()["detail"].lower() or resp.json()["detail"]


def test_login_rejects_unknown_email(client, db_session):
    resp = login(client, "nobody@school.edu", "whatever")
    assert resp.status_code == 401


def test_login_is_case_insensitive_on_email(client, db_session):
    create_user(db_session, "admin@school.edu", "secret123", "admin")
    resp = login(client, "ADMIN@school.edu", "secret123")
    assert resp.status_code == 200


def test_administrators_requires_token(client):
    resp = client.get("/api/v1/administrators")
    assert resp.status_code == 401


def test_administrators_rejects_teacher(client, db_session):
    create_user(db_session, "teacher@school.edu", "secret123", "teacher")
    token = login(client, "teacher@school.edu", "secret123").json()["access_token"]
    resp = client.get("/api/v1/administrators", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


def test_administrators_allows_admin(client, db_session):
    create_user(db_session, "admin@school.edu", "secret123", "admin")
    token = login(client, "admin@school.edu", "secret123").json()["access_token"]
    resp = client.get("/api/v1/administrators", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["data"][0]["email"] == "admin@school.edu"


def test_invalid_token_rejected(client):
    resp = client.get("/api/v1/administrators", headers={"Authorization": "Bearer not-a-jwt"})
    assert resp.status_code == 401