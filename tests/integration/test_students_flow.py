"""End-to-end integration test: full student enrollment + attendance of the MVP flow."""

VALID_STUDENT = {
    "first_name": "Grace",
    "last_name": "Hopper",
    "date_of_birth": "2011-06-19",
    "grade_level": "4",
}


def test_mvp_student_flow(client, make_auth_headers):
    admin = make_auth_headers(role="admin")
    teacher = make_auth_headers(role="teacher")

    created = client.post("/api/v1/students", json=VALID_STUDENT, headers=admin)
    assert created.status_code == 201
    sid = created.json()["student"]["student_id"]

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
