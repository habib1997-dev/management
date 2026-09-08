"""End-to-end integration test: teacher -> course -> enrolled students."""



def test_teacher_course_student_flow(client, make_auth_headers):
    admin = make_auth_headers(role="admin")

    teacher = client.post(
        "/api/v1/teachers",
        json={
            "name": "Jane Smith",
            "email": "jane.instructor@schoolsystem.com",
            "subjects_taught": "Mathematics",
        },
        headers=admin,
    )
    assert teacher.status_code == 201
    tid = teacher.json()["teacher"]["teacher_id"]

    student_ids = []
    for first, last in (("John", "Doe"), ("Maria", "Garcia")):
        resp = client.post(
            "/api/v1/students",
            json={
                "first_name": first,
                "last_name": last,
                "date_of_birth": "2010-05-15",
                "grade_level": "9",
            },
            headers=admin,
        )
        assert resp.status_code == 201
        student_ids.append(resp.json()["student"]["student_id"])

    course = client.post(
        "/api/v1/courses",
        json={
            "name": "Algebra I",
            "teacher_id": tid,
            "grade_level": "9",
            "semester": "Fall 2026",
        },
        headers=admin,
    )
    assert course.status_code == 201
    cid = course.json()["course"]["course_id"]

    roster = client.put(
        f"/api/v1/courses/{cid}/students",
        json={"student_ids": student_ids},
        headers=admin,
    )
    assert roster.status_code == 200
    assert len(roster.json()["students"]) == 2

    listed = client.get(f"/api/v1/courses/{cid}/students", headers=admin)
    assert listed.status_code == 200
    assert listed.json()["meta"]["total"] == 2
    assert {s["first_name"] for s in listed.json()["data"]} == {"John", "Maria"}

    by_teacher = client.get(f"/api/v1/courses?teacherId={tid}", headers=admin)
    assert by_teacher.status_code == 200
    assert by_teacher.json()["meta"]["total"] == 1
    assert by_teacher.json()["data"][0]["course_id"] == cid