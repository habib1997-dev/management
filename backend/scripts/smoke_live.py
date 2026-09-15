"""Live smoke test for the deployed School System API + SPA.

Usage:
    python scripts/smoke_live.py [BASE_URL]

Defaults to http://localhost:8199. Emails default as listed; PASSWORDS are
required and must be supplied via env vars (no defaults are committed):

    SMOKE_ADMIN_EMAIL      (default admin@schoolsystem.com)
    SMOKE_ADMIN_PASSWORD   (required)
    SMOKE_TEACHER_EMAIL    (default jane.smith@schoolsystem.com)
    SMOKE_TEACHER_PASSWORD (required)
    SMOKE_PARENT_EMAIL     (default maria.doe@family.net)
    SMOKE_PARENT_PASSWORD  (required)

Standard-library only, so it runs anywhere (local uvicorn, Docker container,
or the Render deployment) with zero extra dependencies.

Exit code 0 = every check passed; 1 = at least one check failed; 2 = a required
env var is missing.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import date

DEFAULT_BASE = "http://localhost:8199"
LOGIN_ISSUED = "token issued"

FAILURES: list[str] = []


def _required_env(name: str) -> str:
    value = (os.environ.get(name) or "").strip()
    if not value:
        print(f"Missing required env var {name} — supply it (e.g. `$env:{name}='...'`) and re-run.")
        sys.exit(2)
    return value


def request(method: str, url: str, *, token: str | None = None, body: dict | None = None) -> tuple[int, object]:
    headers: dict[str, str] = {"Accept": "application/json"}
    data = None
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            content = resp.read()
            try:
                return resp.status, json.loads(content)
            except (json.JSONDecodeError, UnicodeDecodeError):
                return resp.status, content
    except urllib.error.HTTPError as exc:
        content = exc.read()
        try:
            return exc.code, json.loads(content)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return exc.code, content


def check(step: str, ok: bool, detail: str = "") -> None:
    mark = "PASS" if ok else "FAIL"
    print(f"  [{mark}] {step}" + (f"  ({detail})" if detail and ok else ""))
    if not ok:
        FAILURES.append(f"{step} :: {detail}")


def login(base: str, email: str, password: str) -> tuple[str, dict]:
    status, data = request("POST", f"{base}/api/v1/auth/login", body={"email": email, "password": password})
    if status != 200 or not isinstance(data, dict) or "access_token" not in data:
        raise RuntimeError(f"login failed for {email}: status={status} data={data!r}")
    return str(data["access_token"]), data


def _login_check(base: str, email: str, password: str, label: str) -> tuple[str | None, dict | None]:
    try:
        token, data = login(base, email, password)
    except RuntimeError as exc:
        check(f"{label} login", False, str(exc))
        return None, None
    check(f"{label} login", True, data.get("role") or LOGIN_ISSUED)
    return token, data


def first_id(item: dict) -> str | None:
    return str(item.get("course_id") or item.get("student_id") or item.get("parent_id") or item.get("teacher_id") or item.get("id"))


def _smoke_health_and_brand(base: str) -> None:
    status, data = request("GET", f"{base}/health")
    check("GET /health -> 200", status == 200, f"status={status}")
    if isinstance(data, dict):
        check("/health payload status=ok", data.get("status") == "ok", str(data))

    status, brand = request("GET", f"{base}/api/v1/settings/brand")
    check("GET brand -> 200 with school name", status == 200 and isinstance(brand, dict) and bool(brand.get("name")),
          f"status={status} keys={list(brand) if isinstance(brand, dict) else brand!r}")


def _smoke_admin(base: str, token: str) -> str | None:
    status, students = request("GET", f"{base}/api/v1/students?page=1&pageSize=50", token=token)
    rows = students.get("data") if isinstance(students, dict) else None
    check("admin GET /students -> paginated list", status == 200 and isinstance(rows, list) and len(rows) >= 1,
          f"status={status} count={len(rows) if isinstance(rows, list) else 'n/a'}")

    status, csv = request("GET", f"{base}/api/v1/export/students.csv", token=token)
    is_csv = isinstance(csv, bytes) and b"student_id" in csv[:300]
    check("admin CSV export -> csv bytes", status == 200 and is_csv, f"status={status} len={len(csv) if isinstance(csv, bytes) else 0}")
    return first_id(rows[0]) if isinstance(rows, list) and rows else None


def _smoke_teacher(base: str) -> tuple[str | None, str | None]:
    teacher = os.environ.get("SMOKE_TEACHER_EMAIL", "jane.smith@schoolsystem.com")
    teacher_pw = _required_env("SMOKE_TEACHER_PASSWORD")
    token, data = _login_check(base, teacher, teacher_pw, "teacher")
    if token is None:
        return None, None

    tid = data.get("teacher_id")
    url = f"{base}/api/v1/courses?teacherId={tid}" if tid else f"{base}/api/v1/courses"
    status, courses = request("GET", url, token=token)
    course_rows = courses.get("data") if isinstance(courses, dict) else None
    check("teacher GET /courses -> own courses", status == 200 and isinstance(course_rows, list) and len(course_rows) >= 1,
          f"status={status} count={len(course_rows) if isinstance(course_rows, list) else 'n/a'}")
    course_id = first_id(course_rows[0]) if isinstance(course_rows, list) and course_rows else None
    if course_id:
        status, _ = request("GET", f"{base}/api/v1/attendance/{course_id}", token=token)
        check("teacher GET attendance for own course", status == 200, f"status={status}")
    else:
        check("teacher GET attendance for own course", False, "no course available")
    return token, course_id


def _smoke_parent(base: str) -> None:
    parent = os.environ.get("SMOKE_PARENT_EMAIL", "maria.doe@family.net")
    parent_pw = _required_env("SMOKE_PARENT_PASSWORD")
    token, data = _login_check(base, parent, parent_pw, "parent")
    if token is None:
        return

    pid = data.get("parent_id")
    if not pid:
        check("parent GET portal", False, "no parent_id in login response")
        return

    status, portal = request("GET", f"{base}/api/v1/parents/{pid}/portal", token=token)
    parent_rows = portal.get("parents") if isinstance(portal, dict) else None
    children = (parent_rows[0].get("children") if isinstance(parent_rows, list) and parent_rows else None)
    check("parent GET portal -> own children", status == 200 and isinstance(children, list) and len(children) >= 1,
          f"status={status}")
    child_id = str(children[0].get("student_id")) if isinstance(children, list) and children and children[0].get("student_id") else None
    if child_id:
        status, pdf = request("GET", f"{base}/api/v1/reports/portal/{child_id}", token=token)
        check("parent PDF download -> %PDF bytes", status == 200 and isinstance(pdf, bytes) and pdf.startswith(b"%PDF-"),
              f"status={status} prefix={pdf[:5] if isinstance(pdf, bytes) else 'n/a'}")
    else:
        check("parent PDF download -> %PDF bytes", False, "no child id from portal")


def _smoke_create_ops(base: str, admin_token: str, teacher_token: str, course_id: str, roster_student_id: str) -> None:
    today = date.today().isoformat()

    status, body = request("POST", f"{base}/api/v1/students", token=admin_token, body={
        "first_name": "Smoke", "last_name": "Test",
        "date_of_birth": "2010-03-15", "grade_level": "10",
    })
    new_student_id = str(body["student"]["student_id"]) if status == 201 and isinstance(body, dict) else None
    check("admin POST /students -> 201", status == 201 and isinstance(new_student_id, str) and new_student_id,
          f"status={status}")

    status, _ = request("POST", f"{base}/api/v1/enrollments", token=admin_token, body={
        "student_id": new_student_id, "enrolled_by": "smoke-test",
    })
    check("admin POST /enrollments -> 201", status == 201, f"status={status}")

    status, _ = request("POST", f"{base}/api/v1/attendance", token=teacher_token, body={
        "course_id": course_id, "date": today,
        "records": [{"student_id": roster_student_id, "status": "present"}],
    })
    check("teacher POST /attendance -> 201", status == 201, f"status={status}")

    status, _ = request("POST", f"{base}/api/v1/grades", token=teacher_token, body={
        "student_id": roster_student_id, "course_id": course_id,
        "grade_value": 88.0, "assignment_type": "quiz",
        "date_assigned": today, "date_due": today,
    })
    check("teacher POST /grades -> 201", status == 201, f"status={status}")

    status, detail = request("GET", f"{base}/api/v1/students/{new_student_id}", token=admin_token)
    check("admin GET /students/{id} -> readback", status == 200 and isinstance(detail, dict) and detail.get("first_name") == "Smoke",
          f"status={status}")

    status, grades = request("GET", f"{base}/api/v1/students/{roster_student_id}/grades", token=teacher_token)
    check("teacher GET /students/{id}/grades -> readback",
          status == 200 and isinstance(grades, dict) and isinstance(grades.get("data"), list) and len(grades["data"]) >= 1,
          f"status={status}")


def _smoke_spa(base: str) -> None:
    status, html = request("GET", f"{base}/")
    has_root = isinstance(html, bytes) and b'id="root"' in html
    check("SPA fallback GET / -> HTML", isinstance(html, bytes) and has_root,
          f"status={status} hasRoot={has_root}")

    status, nomatch = request("GET", f"{base}/api/v1/definitely-not-a-route")
    check("unknown API route -> 404 JSON (not SPA HTML)", status == 404 and isinstance(nomatch, dict),
          f"status={status} type={type(nomatch).__name__}")


def main() -> int:
    base = os.environ.get("SMOKE_BASE_URL") or (sys.argv[1] if len(sys.argv) > 1 else DEFAULT_BASE)
    admin = os.environ.get("SMOKE_ADMIN_EMAIL", "admin@schoolsystem.com")
    admin_pw = _required_env("SMOKE_ADMIN_PASSWORD")

    print(f"Smoke test against: {base}")
    _smoke_health_and_brand(base)

    admin_token, _ = _login_check(base, admin, admin_pw, "admin")
    roster_student_id = _smoke_admin(base, admin_token) if admin_token else None

    teacher_token, course_id = _smoke_teacher(base)
    _smoke_parent(base)
    _smoke_spa(base)

    if admin_token and teacher_token and course_id and roster_student_id:
        _smoke_create_ops(base, admin_token, teacher_token, course_id, roster_student_id)

    print()
    if FAILURES:
        print(f"SMOKE RESULT: FAILED  ({len(FAILURES)} failed checks)")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print("SMOKE RESULT: ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())