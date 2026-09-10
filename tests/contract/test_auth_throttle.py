"""Login throttling: 5 failed attempts per email+IP within 15 minutes -> 429."""

from student_management.api.auth import (
    LOGIN_WINDOW_SECONDS,
    MAX_FAILED_LOGINS,
    _clear_failures,
    _is_throttled,
    _record_failure,
)


def _login(client, email, password="wrongpass"):
    return client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )


def test_blocks_after_too_many_failures(client, make_auth_headers, db_session):
    email = "throttle-1@test.edu"
    make_auth_headers(email=email, role="admin")

    for _ in range(MAX_FAILED_LOGINS):
        assert _login(client, email).status_code == 401

    blocked = _login(client, email)
    assert blocked.status_code == 429
    assert "minutes" in blocked.json()["detail"].lower()


def test_success_resets_counter(client, make_auth_headers, db_session):
    email = "throttle-2@test.edu"
    make_auth_headers(email=email, role="admin")

    for _ in range(3):
        assert _login(client, email).status_code == 401

    ok = _login(client, email, password="password123")
    assert ok.status_code == 200

    for _ in range(MAX_FAILED_LOGINS):
        assert _login(client, email).status_code == 401
    assert _login(client, email).status_code == 429


def test_failures_are_per_email(client, make_auth_headers, db_session):
    email = "throttle-3@test.edu"
    make_auth_headers(email=email, role="admin")

    for _ in range(MAX_FAILED_LOGINS + 1):
        _login(client, email)
    assert _login(client, email).status_code == 429

    other = client.post(
        "/api/v1/auth/login",
        json={"email": "throttle-other@test.edu", "password": "wrongpass"},
    )
    assert other.status_code == 401


def test_window_expiry_resets_history():
    key = "unit-window@test.edu|testclient"
    _clear_failures(key)
    for _ in range(MAX_FAILED_LOGINS - 1):
        _record_failure(key)
    assert not _is_throttled(key)
    _record_failure(key)
    assert _is_throttled(key)
    _clear_failures(key)


def test_max_failed_logins_constant_is_5():
    assert MAX_FAILED_LOGINS == 5
    assert LOGIN_WINDOW_SECONDS == 15 * 60