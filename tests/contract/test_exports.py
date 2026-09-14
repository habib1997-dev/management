"""Contract tests for admin CSV exports (students + grades)."""

import csv
import io


def _parse(resp):
    return list(csv.reader(io.StringIO(resp.text)))


def _make_student(client, admin, **overrides):
    payload = {
        "first_name": "Zain",
        "last_name": "Malik",
        "date_of_birth": "2011-05-12",
        "grade_level": "9",
        **overrides,
    }
    resp = client.post("/api/v1/students", json=payload, headers=admin)
    assert resp.status_code in (200, 201)
    return resp.json()["student"]


def test_students_export_is_admin_only_csv(client, make_auth_headers):
    teacher = make_auth_headers(role="teacher", email="export.teacher@test.edu")
    resp = client.get("/api/v1/export/students.csv", headers=teacher)
    assert resp.status_code == 403


def test_students_export_returns_rows(client, make_auth_headers):
    admin = make_auth_headers(role="admin")
    _make_student(client, admin, first_name="Zain", last_name="Malik")

    resp = client.get("/api/v1/export/students.csv", headers=admin)
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")
    assert 'filename="students.csv"' in resp.headers["content-disposition"]

    rows = _parse(resp)
    header, body = rows[0], rows[1:]
    assert header[0] == "student_id"
    assert any(r[1] == "Zain" and r[2] == "Malik" for r in body)


def test_grades_export_includes_course_and_student(client, make_auth_headers):
    admin = make_auth_headers(role="admin")
    student = _make_student(client, admin)

    t_resp = client.post(
        "/api/v1/teachers",
        json={"name": "M. Iqbal", "email": "export.grades.t@test.edu", "subjects_taught": "Maths"},
        headers=admin,
    )
    tid = t_resp.json()["teacher"]["teacher_id"]
    c_resp = client.post(
        "/api/v1/courses",
        json={"name": "Algebra", "grade_level": "9", "semester": "Fall 2026", "teacher_id": tid},
        headers=admin,
    )
    cid = c_resp.json()["course"]["course_id"]
    client.put(f"/api/v1/courses/{cid}/students", json={"student_ids": [student["student_id"]]}, headers=admin)

    client.post(
        "/api/v1/grades",
        json={
            "student_id": student["student_id"],
            "course_id": cid,
            "grade_value": 87.5,
            "assignment_type": "test",
            "date_assigned": "2026-09-01",
            "date_due": "2026-09-08",
        },
        headers=admin,
    )

    resp = client.get("/api/v1/export/grades.csv", headers=admin)
    assert resp.status_code == 200
    rows = _parse(resp)
    assert rows[0][4] == "course_name"
    grade_row = [r for r in rows[1:] if r[4] == "Algebra"]
    assert grade_row
    assert grade_row[0][2] == "Zain"
    assert grade_row[0][5] == "87.50"


def test_csv_neutralizes_formula_injection(client, make_auth_headers):
    admin = make_auth_headers(role="admin")
    _make_student(client, admin, first_name='=HYPERLINK("evil","x")', last_name="Trap")
    _make_student(client, admin, first_name="@sum", last_name="Func")
    _make_student(client, admin, first_name="-2+3", last_name="Math")

    rows = _parse(client.get("/api/v1/export/students.csv", headers=admin))
    header, body = rows[0], rows[1:]
    idx = header.index("first_name")

    # No name cell may begin with a live formula marker after escaping.
    for row in body:
        assert not row[idx].startswith(("=", "+", "-", "@"))

    names = [row[idx] for row in body]
    assert any(n.startswith("'=HYPERLINK") for n in names)
    assert any(n == "'@sum" for n in names)
    assert any(n == "'-2+3" for n in names)