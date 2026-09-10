"""End-to-end integration test: full student enrollment + attendance of the MVP flow."""

VALID_STUDENT = {
    "first_name": "Grace",
    "last_name": "Hopper",
    "date_of_birth": "2011-06-19",
    "grade_level": "4",
}


def test_mvp_student_flow(client, make_auth_headers):
    admin = make_auth_headers(role="admin")

    created = client.post("/api/v1/students", json=VALID_STUDENT, headers=admin)
    assert created.status_code == 201
    sid = created.json()["student"]["student_id"]

    # A teacher reads a profile only for a student they actually teach.
    tid = client.post(
        "/api/v1/teachers",
        json={
            "name": "Grace Teacher",
            "email": "grace.teacher@schoolsystem.com",
            "subjects_taught": "Math",
        },
        headers=admin,
    ).json()["teacher"]["teacher_id"]
    cid = client.post(
        "/api/v1/courses",
        json={"name": "Math", "teacher_id": tid, "grade_level": "4", "semester": "Fall 2026"},
        headers=admin,
    ).json()["course"]["course_id"]
    client.put(f"/api/v1/courses/{cid}/students", json={"student_ids": [sid]}, headers=admin)
    teacher = make_auth_headers(
        email="grace.teacher1@schoolsystem.com", role="teacher", teacher_id=tid
    )

    found = client.get(f"/api/v1/students/{sid}", headers=teacher)
    assert found.status_code == 200
    assert found.json()["first_name"] == "Grace"

    searched = client.get("/api/v1/students?search=hopper", headers=admin)
    assert searched.status_code == 200
    assert [s["student_id"] for s in searched.json()["data"]] == [sid]

    updated = client.put(
        f"/api/v1/students/{sid}", json={"email": "grace.hopper@navy.mil"}, headers=admin
    )
    assert updated.status_code == 200
    assert updated.json()["student"]["email"] == "grace.hopper@navy.mil"

    duplicated = client.put(
        "/api/v1/students/00000000-0000-0000-0000-000000000000",
        json={"first_name": "X"},
        headers=admin,
    )
    assert duplicated.status_code == 404

    enrollment = client.post(
        "/api/v1/enrollments",
        json={"student_id": sid, "enrolled_by": "admin@test.edu"},
        headers=admin,
    )
    assert enrollment.status_code == 201
    assert enrollment.json()["enrollment"]["status"] == "active"
